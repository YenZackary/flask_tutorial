from flask import jsonify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker


# Create the engine for the database
engine2 = create_engine("mssql+pyodbc://your_db_user_name:your_db_password@your_IP/service_info?driver=ODBC+Driver+17+for+SQL+Server", pool_pre_ping=True)

Base2 = automap_base()
Base2.prepare(engine2, reflect=True)
Session2 = sessionmaker(bind=engine2)
session2 = Session2()
name_input = Base2.classes.name_input

def get_data_from_db():
    # Query to get the required columns from the table
    query = session2.query(
        name_input.input_id,
        name_input.nameinput,

    ).all()

    results = [
        {
            "ID" : row.input_id,
            "user_name_input": row.nameinput,
        }
        for row in query
    ]

    return results