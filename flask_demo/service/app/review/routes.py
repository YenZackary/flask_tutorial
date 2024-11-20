from flask import Flask, render_template, request, g
from . import review_bp
from .scripts.check import check_login, has_permission
from .scripts.review import get_data_from_db
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
engine = create_engine("mssql+pyodbc://your_db_user_name:your_db_password@your_IP/demo?driver=ODBC+Driver+17+for+SQL+Server", pool_pre_ping=True)

Base = automap_base()
Base.prepare(engine, reflect=True)
Session = sessionmaker(bind=engine)

# Get the User, UserRole, Services, and Permissions classes from the reflected tables
User = Base.classes.Users_Data
Login_Status = Base.classes.Login_Status
Services = Base.classes.Services

@review_bp.before_request
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

@review_bp.teardown_request
def teardown_request(exception=None):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@review_bp.route('/')
def home():
    current_user_id, current_username = check_login()

    if not current_user_id:
        return render_template('login_no.html')
    
    if not has_permission(current_user_id, 2):
        return render_template('permission_error.html')
    
    data_from_db = get_data_from_db()

    return render_template('review.html', username = current_username, result = data_from_db)

