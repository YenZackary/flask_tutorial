from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from flask import g, request

# Create an engine to connect to the database
engine = create_engine("mssql+pyodbc://your_db_user_name:your_db_password@your_IP/demo?driver=ODBC+Driver+17+for+SQL+Server", pool_pre_ping=True)


# Reflect the database schema
Base = automap_base()
Base.prepare(engine, reflect=True)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

# Get the User, UserRole, Services, and Permissions classes from the reflected tables
User = Base.classes.Users_Data
Login_Status = Base.classes.Login_Status
Permissions = Base.classes.Permissions


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

def has_permission(user_id, service_id):
    # Query the Permissions table for all rows corresponding to the user_id
    permissions = g.db.query(Permissions).filter_by(user_id=user_id).all()

    # Check if the service_id is among the user's permissions
    for permission in permissions:
        if permission.service_id == service_id:
            return True
    return False