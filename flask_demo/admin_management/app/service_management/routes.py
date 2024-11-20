from flask import Flask, g, render_template, request
from sqlalchemy import create_engine, desc, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from . import service_management_bp
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

@service_management_bp.before_request
def before_request():
    g.db = Session()
    services = g.db.query(Services).all()
    g.services_by_category = {}
    for service in services:
        category = service.category
        if category not in g.services_by_category:
            g.services_by_category[category] = []
        g.services_by_category[category].append(service)

@service_management_bp.teardown_request
def teardown_request(exception=None):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@service_management_bp.route('/service_overview')
def service_overview():
    current_user_id, current_username = check_login()

    if not current_user_id:
        return render_template('login_no.html')

    if not has_permission(current_user_id, 3):
        return render_template('permission_error.html')

    all_service = g.db.query(Services.service_id, Services.service_name, Services.IP, Services.category).all()
    service_data = []
    for service in all_service:
        service_data.append({
            'service_id': service.service_id,
            'service_name': service.service_name,
            'IP': service.IP,
            'category': service.category
        })

    return render_template('service_overview.html', username=current_username, all_service=service_data)

@service_management_bp.route('/add_service', methods=['GET', 'POST'])
def add_service():
    current_user_id, current_username = check_login()
    if not current_user_id:
        return render_template('login_no.html')
    
    if not has_permission(current_user_id, 3):
        return render_template('permission_error.html')
    # All current service
    all_user = g.db.query(User.user_id, User.username).all()
    
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        IP = request.form.get('IP')
        category = request.form.get('category')
        new_service = Services(service_name=service_name, IP=IP, category=category)
        g.db.add(new_service)
        g.db.commit()
        latest_service_id = g.db.query(Services.service_id).order_by(desc(Services.service_id)).first()
        latest_service_name = g.db.query(Services.service_name).order_by(desc(Services.service_id)).first()
        return render_template('service_add_permission.html', all_user = all_user, latest_service_id = latest_service_id[0], latest_service_name = latest_service_name[0], username=current_username)

    return render_template('service_add.html', username=current_username)

@service_management_bp.route('/update_permission_user/<int:id>', methods=['POST'])
def update_permission_user(id):
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')

    if not has_permission(current_user_id, 3):
        return render_template('permission_error.html')
    
    if request.method == 'POST':
        selected_users = request.form.getlist('users')
        selected_users = [int(user) for user in selected_users]

        # Add new permissions
        for perm in selected_users:
            new_permission = Permissions(user_id=perm, service_id=id, role_id=2)
            g.db.add(new_permission)

        # Commit the transaction
        g.db.commit()
        
    # Return success message and redirect to login
    return render_template('update_success.html')

@service_management_bp.route('/update_delete_service', methods=['GET', 'POST'])
def update_delete_service():
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')

    if not has_permission(current_user_id, 3):
        return render_template('permission_error.html')
    
    if request.method == 'POST':
        selected_services = request.form.getlist('service_result')
        selected_services = [int(service) for service in selected_services]

    # Check if selected_services is not empty
    if selected_services:
        # Create a string with the selected services as a comma-separated list
        values = ','.join(str(service) for service in selected_services)
        
        # Delete related permission first
        query = text(f'DELETE FROM Permissions WHERE service_id IN ({values})')
        g.db.execute(query)
        g.db.commit()

        # Delete service
        query = text(f'DELETE FROM Services WHERE service_id IN ({values})')
        g.db.execute(query)
        g.db.commit()

        # reseed
        current_latest_service_id = g.db.query(Services.service_id).order_by(Services.service_id.desc()).first()
        if current_latest_service_id:
            current_latest_service_id = current_latest_service_id[0]
        else:
            current_latest_service_id = 0

        reseed_query = text(f"DBCC CHECKIDENT ('Services', RESEED, {current_latest_service_id})")
        print(reseed_query)
        g.db.execute(reseed_query)
        g.db.commit()

        print('DB update')
    else:
        print('No services selected for deletion')

    # Return success message and redirect to login
    return render_template('update_success.html')

@service_management_bp.route('/edit_service', methods=['GET', 'POST'])
def edit_service():
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')
    
    if not has_permission(current_user_id, 3):
        return render_template('permission_error.html')
    
    if request.method == 'POST':
        selected_services = request.form.getlist('service_result')
        selected_services = [int(service) for service in selected_services]
        select_service_info = g.db.query(Services.service_id, Services.service_name, Services.IP, Services.category).filter_by(service_id=selected_services[0]).first()
         # Convert the SQLAlchemy result to a dictionary
        select_service_info_dict = {
            'service_id': select_service_info.service_id,
            'service_name': select_service_info.service_name,
            'IP': select_service_info.IP,
            'category': select_service_info.category
        }
        return render_template('service_edit.html', select_service_info_dict = select_service_info_dict, username = current_username)

@service_management_bp.route('/update_edit_service', methods=['POST'])
def update_edit_service():
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')
    
    if not has_permission(current_user_id, 3):
        return render_template('permission_error.html')
    
    if request.method == 'POST':
        service_id = request.form['service_id']
        service_name = request.form['service_name']
        IP = request.form['IP']
        category = request.form['category']
        
        # Log the received data for debugging
        print(f"Received data: service_id={service_id}, service_name={service_name}, IP={IP}, category={category}")

        # Update the service in the database
        service = g.db.query(Services).filter_by(service_id=service_id).first()
        if service:
            service.service_name = service_name
            service.IP = IP
            service.category = category
            g.db.commit()

    return render_template('update_success.html')