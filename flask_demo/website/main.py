from flask import Flask, render_template, request, redirect, url_for, g, session
from sqlalchemy import create_engine, Date, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from datetime import datetime


# Create an engine to connect to the database
engine = create_engine("mssql+pyodbc://your_db_user_name:your_db_password@your_IP/demo?driver=ODBC+Driver+17+for+SQL+Server", pool_pre_ping=True)


# Reflect the database schema
Base = automap_base()
Base.prepare(engine, reflect=True)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)

# Get the User, UserRole, Services, and Permissions classes from the reflected tables
User = Base.classes.Users_Data
Login_Status = Base.classes.Login_Status
Services = Base.classes.Services
Permissions = Base.classes.Permissions
ServiceAccessLog = Base.classes.ServiceAccessLog

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.before_request
def before_request():
    g.db = Session()
    # Fetch all services and group them by category
    services = g.db.query(Services).all()
    g.services_by_category = {}
    for service in services:
        category = service.category
        if category not in g.services_by_category:
            g.services_by_category[category] = []
        g.services_by_category[category].append(service)

@app.teardown_request
def teardown_request(exception=None):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = g.db.query(User).filter_by(username=username, password=password).first()
        
        if user:
            if user.activate == "0":
                return render_template('login_deactivate_user.html')
            else:
                ip_check_message, ip_check_result = check_other_user(user.user_id, request.remote_addr)
                if ip_check_result:
                    existing_status = g.db.query(Login_Status).filter(Login_Status.user_id != user.user_id, Login_Status.IP == request.remote_addr, Login_Status.status == 'logged_in').first()
                    other_user = g.db.query(User).filter_by(user_id=existing_status.user_id).first()
                    return render_template('multiple_user_error.html', other_username=other_user.username)
                update_login_status(user.user_id, request.remote_addr, 'logged_in')
            return redirect(url_for('home'))
        else:
            return render_template('login_error.html')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    existing_status = g.db.query(Login_Status).filter(Login_Status.IP == request.remote_addr, Login_Status.status == 'logged_in').first()
    current_userid = g.db.query(User.user_id).filter_by(user_id=existing_status.user_id).first()
    update_login_status(current_userid[0], request.remote_addr, 'logged_out')
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def home():
    current_user_id, current_username = check_login()
    if not current_user_id:
        return redirect(url_for('login'))
    return render_template('home.html', username=current_username)

@app.route('/api/<int:link_id>')
def handle_api(link_id):
    current_user_id, current_username = check_login()

    if not current_user_id:
        return render_template('login_no.html')

    if not has_permission(current_user_id, link_id):
        return render_template('permission_error.html')

    go_to_link = g.db.query(Services.IP).filter_by(service_id=link_id).first()[0]
    
    if go_to_link:
        log_service_access(link_id, current_user_id)
        return redirect(go_to_link)
    else:
        return "Invalid link ID"


def has_permission(user_id, service_id):
    # Query the Permissions table for all rows corresponding to the user_id
    permissions = g.db.query(Permissions).filter_by(user_id=user_id).all()

    # Check if the service_id is among the user's permissions
    for permission in permissions:
        if permission.service_id == service_id:
            return True
    return False

def check_login():
    """
    Check if the user is logged in based on the IP address.
    Returns:
        tuple: (user_id, username) if logged in, otherwise (None, None)
    """
    existing_status = g.db.query(Login_Status).join(User, Login_Status.user_id == User.user_id).filter(
        Login_Status.IP == request.remote_addr,
        Login_Status.status == 'logged_in',
        User.activate == 1  # Condition on the User model
    ).first()

    if existing_status:
        user = g.db.query(User).filter_by(user_id=existing_status.user_id).first()
        return existing_status.user_id, user.username if user else None

    return None, None

    
def update_login_status(user_id, ip_address, status):
    # update DB and log file
    existing_status = g.db.query(Login_Status).filter_by(user_id=user_id, IP=ip_address).first()
    if existing_status:
        existing_status.status = status
        existing_status.IP = ip_address
        existing_status.access_time = datetime.now()
    else:
        new_status = Login_Status(user_id=user_id, status=status, IP=ip_address, access_time=datetime.now())
        g.db.add(new_status)

    g.db.commit()

def check_other_user(current_user_id, current_ip):
    # Query the Login_Status table to check if the current IP is associated with any other user_id that is logged in
    existing_status = g.db.query(Login_Status).filter(Login_Status.user_id != current_user_id, Login_Status.IP == current_ip, Login_Status.status == 'logged_in').first()
    
    if existing_status:
        other_user = g.db.query(User).filter_by(user_id=existing_status.user_id).first()
        if other_user:
            message = f"This computer is already logged in by {other_user.username}."
        else:
            message = "This computer is already logged in by another user."
        return message, True
    else:
        return "", False
    
def log_service_access(link_id, user_id):
    """
    Save each user's access to each service in the database.
    """
    # Get the current date (without the time component)
    current_day = datetime.now().date()

    # Check if a log entry for this link_id, ip_address, and day already exists
    existing_log = g.db.query(ServiceAccessLog).filter(
        ServiceAccessLog.service_id == link_id,
        ServiceAccessLog.user_id == user_id,
        func.cast(ServiceAccessLog.access_date, Date) == current_day
    ).first()

    if existing_log:
        # Increment the request count
        existing_log.today_access_times += 1
        g.db.commit()
    else:
        # Insert a new log entry
        new_log = ServiceAccessLog(service_id=link_id, user_id=user_id)
        g.db.add(new_log)
        g.db.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0')