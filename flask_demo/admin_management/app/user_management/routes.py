from flask import Flask, g, render_template, request, redirect, url_for
from sqlalchemy import create_engine, desc, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from . import user_management_bp
from .scripts.check import check_login, has_permission

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Create an engine to connect to the database
engine = create_engine("mssql+pyodbc://your_db_user_name:your_db_password@your_IP/demo?driver=ODBC+Driver+17+for+SQL+Server", pool_pre_ping=True)


# Reflect the database schema
Base = automap_base()
Base.prepare(engine, reflect=True)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)

# Get the User, UserRole, Services, and Permissions classes from the reflected tables
User = Base.classes.Users_Data
Permissions = Base.classes.Permissions
Login_Status = Base.classes.Login_Status
Services = Base.classes.Services

@user_management_bp.before_request
def before_request():
    g.db = Session()
    services = g.db.query(Services).all()
    g.services_by_category = {}
    for service in services:
        category = service.category
        if category not in g.services_by_category:
            g.services_by_category[category] = []
        g.services_by_category[category].append(service)

@user_management_bp.teardown_request
def teardown_request(exception=None):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@user_management_bp.route('/user_overview')
def user_overview():
    current_user_id, current_username = check_login()

    if not current_user_id:
        return render_template('login_no.html')

    if not has_permission(current_user_id, 4):
        return render_template('permission_error.html')

    # All current service
    all_user = g.db.query(User.user_id, User.username, User.activate).all()

    # Return success message and redirect to login
    return render_template('user_overview.html', username=current_username, all_user = all_user)

@user_management_bp.route('/activate_user', methods=['GET', 'POST'])
def activate_user():
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')
    
    if not has_permission(current_user_id, 4):
        return render_template('permission_error.html')
    
    if request.method == 'POST':
        selected_user_id = request.form.getlist('user_result')[0]

        # Check if user_id is None
        if selected_user_id is not None:
            query = text('UPDATE Users_Data SET activate = 1 WHERE user_id = :user_id')
            g.db.execute(query, {'user_id': selected_user_id})
            g.db.commit()
            print("DB update")
        else:
            print("No user_id provided.")

        return render_template('update_success.html')

@user_management_bp.route('/deactivate_user', methods=['GET', 'POST'])
def deactivate_user():
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')
    
    if not has_permission(current_user_id, 4):
        return render_template('permission_error.html')
    
    if request.method == 'POST':
        selected_user_id = request.form.getlist('user_result')[0]
        print(selected_user_id)

        # Check if user_id is None
        if selected_user_id is not None:
            # Update Users_Data to deactivate the user
            query_users = text('UPDATE Users_Data SET activate = 0 WHERE user_id = :user_id')
            g.db.execute(query_users, {'user_id': selected_user_id})
            
            # Update Login_Status to log out the user
            query_login_status = text('UPDATE Login_Status SET status = \'logged_out\' WHERE user_id = :user_id')
            g.db.execute(query_login_status, {'user_id': selected_user_id})

            g.db.commit()
            print("DB update")
        else:
            print("No user_id provided.")

        return render_template('update_success.html')

@user_management_bp.route('/add_new_user', methods=['GET', 'POST'])
def add_new_user():
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')
    
    if not has_permission(current_user_id, 4):
        return render_template('permission_error.html')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            new_user = User(username=username, password=password, role_id=2, activate=1)
            g.db.add(new_user)
            g.db.commit()

            # find user_id and redirect to change_permission
            latest_user = g.db.query(User.user_id).order_by(desc(User.user_id)).first()
            return redirect(url_for('user_management.change_permission', id = latest_user[0]))

        else:
            error_message = "New passwords do not match."
            
        return f'<script>alert("{error_message}"); window.location.replace("{url_for("add_new_user")}");</script>'
        
    # Return success message and redirect to login
    return render_template('user_add.html', username=current_username)

@user_management_bp.route('/change_permission/<int:id>')
def change_permission(id):
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')
    
    if not has_permission(current_user_id, 4):
        return render_template('permission_error.html')

    # All current service
    all_service = g.db.query(Services.service_id, Services.service_name, Services.category).all()

    # The current username of the user whose permission we want to change
    current_edit_username = g.db.query(User.username).filter_by(user_id=id).first()

    # The current service_id of the user whose permission we want to change
    permissions_show = g.db.query(Permissions.service_id).filter_by(user_id=id).all()
    user_permission = [perm[0] for perm in permissions_show]

    # Return success message and redirect to login
    return render_template('permission_change.html', username=current_username, all_service = all_service, user_permission = user_permission, current_edit_username = current_edit_username[0], current_edit_user_id = id)

@user_management_bp.route('/update_permission/<int:id>', methods=['POST'])
def update_permission(id):
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')
    
    if not has_permission(current_user_id, 4):
        return render_template('permission_error.html')

    # Currently modifying user's all permissions 
    permissions_show = g.db.query(Permissions.service_id).filter_by(user_id=id).all()
    user_permission = [perm[0] for perm in permissions_show]

    if request.method == 'POST':
        selected_permissions = request.form.getlist('permissions')
        selected_permissions = [int(permission) for permission in selected_permissions]

        # Determine which permissions to add and which to remove
        permissions_to_add = set(selected_permissions) - set(user_permission)
        permissions_to_remove = set(user_permission) - set(selected_permissions)

        # Get role_id
        modify_user_role_id = g.db.query(User.role_id).filter_by(user_id=id).first()

        # Add new permissions
        for perm in permissions_to_add:
            new_permission = Permissions(user_id=id, service_id=perm, role_id=modify_user_role_id[0])
            g.db.add(new_permission)

        # Remove old permissions
        for perm in permissions_to_remove:
            permission_to_remove = g.db.query(Permissions).filter_by(user_id=id, service_id=perm, role_id=modify_user_role_id[0]).first()
            if permission_to_remove:
                g.db.delete(permission_to_remove)

        # Commit the transaction
        g.db.commit()
        print('DB update')
        
    # Return success message and redirect to login
    return render_template('update_success.html')