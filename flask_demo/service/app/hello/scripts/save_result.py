from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create the engine for the database
engine1 = create_engine("mssql+pyodbc://your_db_user_name:your_db_password@your_IP/service_info?driver=ODBC+Driver+17+for+SQL+Server", pool_pre_ping=True)

Base1 = automap_base()
Base1.prepare(engine1, reflect=True)
Session1 = sessionmaker(bind=engine1)
session1 = Session1()
name_input = Base1.classes.name_input


def update_db(name_data):
    """Insert data into the name_input table."""
    try:
        # Create a new instance of name_input and set the value
        new_entry = name_input(nameinput=name_data)
        
        # Add the new entry to the session
        session1.add(new_entry)
        
        # Commit the transaction to save it in the database
        session1.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        session1.rollback()  # Rollback in case of an error
    finally:
        session1.close()  # Close the session





