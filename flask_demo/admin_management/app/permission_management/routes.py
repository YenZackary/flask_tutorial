from flask import Flask, g, render_template, request
from sqlalchemy import create_engine, desc, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from . import permission_management_bp
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

@permission_management_bp.before_request
def before_request():
    g.db = Session()
    services = g.db.query(Services).all()
    g.services_by_category = {}
    for service in services:
        category = service.category
        if category not in g.services_by_category:
            g.services_by_category[category] = []
        g.services_by_category[category].append(service)

@permission_management_bp.teardown_request
def teardown_request(exception=None):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@permission_management_bp.route('/permission_overview')
def permission_overview():
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')

    if not has_permission(current_user_id, 5):
        return render_template('permission_error.html')
    
    # get information in DB
    query = text("""
        SELECT 
            u.user_id, 
            u.username, 
            STUFF((
                SELECT ',' + CAST(p.service_id AS VARCHAR)
                FROM Permissions p
                WHERE p.user_id = u.user_id
                ORDER BY p.service_id
                FOR XML PATH('')
            ), 1, 1, '') AS service_ids
        FROM Users_Data u
        LEFT OUTER JOIN Permissions p
        ON u.user_id = p.user_id
        GROUP BY u.user_id, u.username
    """)

    results = g.db.execute(query).fetchall()
    transformed_results = [
        {
            'user_id': item[0],
            'username': item[1],
            'services_id': item[2]
        }
        for item in results
    ]

    # Return success message and redirect to login
    return render_template('permission_overview.html', username=current_username, user_permission = transformed_results)


@permission_management_bp.route('/change_permission/<int:id>')
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

@permission_management_bp.route('/update_permission/<int:id>', methods=['POST'])
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