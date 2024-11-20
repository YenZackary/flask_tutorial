from flask import g, render_template, url_for, send_file
from sqlalchemy import create_engine, desc, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
import io
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from . import monitor_bp
from .scripts.check import check_login, has_permission

# Create an engine to connect to the database
engine = create_engine("mssql+pyodbc://your_db_user_name:your_db_password@your_IP/demo?driver=ODBC+Driver+17+for+SQL+Server", pool_pre_ping=True)


# Reflect the database schema
Base = automap_base()
Base.prepare(engine, reflect=True)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)

# Get the Servicesclasses from the reflected tables
Services = Base.classes.Services


@monitor_bp.before_request
def before_request():
    g.db = Session()
    services = g.db.query(Services).all()
    g.services_by_category = {}
    for service in services:
        category = service.category
        if category not in g.services_by_category:
            g.services_by_category[category] = []
        g.services_by_category[category].append(service)

    # Pre-fetch and cache service and user access data to avoid repeated queries
    g.service_access_per_day = fetch_service_access_data(g.db)
    g.user_access_today = fetch_user_access_data(g.db)


@monitor_bp.teardown_request
def teardown_request(exception=None):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@monitor_bp.route('/')
def home():
    current_user_id, current_username = check_login()
    
    if not current_user_id:
        return render_template('login_no.html')

    if not has_permission(current_user_id, 6):
        return render_template('permission_error.html')

    # Use cached data from g
    service_access_per_day = g.service_access_per_day
    user_access_today = g.user_access_today

    # 3. Today Total Access Times
    query3 = text('''
    SELECT SUM(today_access_times) AS total_access_times
    FROM ServiceAccessLog
    WHERE access_date = CAST(GETDATE() AS DATE);
    ''')
    total_access_today = g.db.execute(query3).fetchone()[0]

    # 4. Today Total user access
    query4 = text('''
    SELECT COUNT(DISTINCT user_id) AS distinct_user
    FROM ServiceAccessLog
    WHERE access_date = CAST(GETDATE() AS DATE);
    ''')
    total_user_today = g.db.execute(query4).fetchone()[0]

    # 5. The service is being used today
    query5 = text('''
    SELECT COUNT(DISTINCT service_id) AS distinct_service
    FROM ServiceAccessLog
    WHERE access_date = CAST(GETDATE() AS DATE);
    ''')
    total_service_user_today = g.db.execute(query5).fetchone()[0]

    # Avoid loading directly from /monitor; instead, access files from another directory
    if not [row.service_name for row in service_access_per_day]:
        return render_template('monitor_warning.html')

    # Generate plots
    service_plot = create_service_access_plot(service_access_per_day)
    user_plot = create_user_access_plot(user_access_today)

    # Save plots to in-memory files
    service_plot_io = io.BytesIO()
    user_plot_io = io.BytesIO()
    
    service_plot.savefig(service_plot_io, format='png')
    user_plot.savefig(user_plot_io, format='png')

    # Seek to the beginning of the in-memory file
    service_plot_io.seek(0)
    user_plot_io.seek(0)

    # Render the results in an HTML template
    return render_template('monitor_results.html', 
                           service_access_per_day=service_access_per_day,
                           user_access_today=user_access_today,
                           total_access_today=total_access_today,
                           total_user_today=total_user_today,
                           total_service_user_today=total_service_user_today,
                           service_plot_url=url_for('monitor.service_plot'),
                           user_plot_url=url_for('monitor.user_plot'),
                           username=current_username)


@monitor_bp.route('/service_plot')
def service_plot():
    service_plot_io = io.BytesIO()
    # Use cached data from g
    service_access_per_day = g.service_access_per_day
    service_plot = create_service_access_plot(service_access_per_day)
    service_plot.savefig(service_plot_io, format='png')
    service_plot_io.seek(0)
    return send_file(service_plot_io, mimetype='image/png')


@monitor_bp.route('/user_plot')
def user_plot():
    user_plot_io = io.BytesIO()
    # Use cached data from g
    user_access_today = g.user_access_today
    user_plot = create_user_access_plot(user_access_today)
    user_plot.savefig(user_plot_io, format='png')
    user_plot_io.seek(0)
    return send_file(user_plot_io, mimetype='image/png')


def fetch_service_access_data(session):
    query = text('''
    SELECT 
        sa.service_id,
        s.service_name,
        SUM(sa.today_access_times) AS total_access_times
    FROM 
        ServiceAccessLog sa
    LEFT JOIN 
        Services s ON sa.service_id = s.service_id
    WHERE 
        sa.access_date = CAST(GETDATE() AS DATE)
    GROUP BY 
        sa.service_id, 
        s.service_name
    HAVING 
        SUM(sa.today_access_times) > 0
    ORDER BY 
        total_access_times DESC;
    ''')
    return session.execute(query).fetchall()


def fetch_user_access_data(session):
    query = text('''
    SELECT 
        sl.user_id,
        ud.username,
        SUM(sl.today_access_times) AS total_access_times
    FROM 
        ServiceAccessLog sl
    LEFT JOIN 
        Users_Data ud ON sl.user_id = ud.user_id
    WHERE 
        sl.access_date = CAST(GETDATE() AS DATE)
    GROUP BY 
        sl.user_id,
        ud.username
    HAVING 
        SUM(sl.today_access_times) > 0
    ORDER BY 
        total_access_times DESC;
    ''')
    return session.execute(query).fetchall()


def create_service_access_plot(data):
    service_ids = [str(row.service_id) for row in data]  # Convert service_ids to strings
    total_access_times = [row.total_access_times for row in data]

    # Combine service_ids and total_access_times into a list of tuples and sort by total_access_times in descending order
    sorted_data = sorted(zip(service_ids, total_access_times), key=lambda x: x[1], reverse=True)
    sorted_service_ids, sorted_total_access_times = zip(*sorted_data)
    
    plt.switch_backend('Agg')  # Set backend to Agg for the plot
    fig, ax = plt.subplots()
    plt.close(fig)

    # Plot sorted data with custom bar colors
    bars = ax.bar(range(len(sorted_service_ids)), sorted_total_access_times, color='#33e7b6')
    
    # Set x-axis labels
    ax.set_xticks(range(len(sorted_service_ids)))
    ax.set_xticklabels(sorted_service_ids)
    
    ax.set_xlabel('Service ID')
    ax.set_ylabel('Total Access Times')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    return fig


def create_user_access_plot(data):
    usernames = [row.username for row in data]
    total_access_times = [row.total_access_times for row in data]

    # Combine usernames and total_access_times into a list of tuples and sort by total_access_times
    sorted_data = sorted(zip(usernames, total_access_times), key=lambda x: x[1], reverse=True)
    sorted_usernames, sorted_total_access_times = zip(*sorted_data)
    
    plt.switch_backend('Agg')  # Set backend to Agg for the plot
    fig, ax = plt.subplots()
    plt.close(fig)

    # Plot data with custom bar colors
    bars = ax.bar(sorted_usernames, sorted_total_access_times, color='#33e7b6')
    ax.set_xlabel('Username')
    ax.set_ylabel('Total Access Times')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    return fig
