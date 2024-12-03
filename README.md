# Flask Website Tutorial Series

Welcome to the **Flask Website Tutorial Series**! This repository contains the code for building a modular and scalable Flask web application.

## 📖 Check Out the Full Tutorial

For a detailed step-by-step guide on setting up and extending this project, please visit the following Medium article:

- [Flask Website Tutorial series](https://medium.com/zackary-yen)

The series of articles covers everything from setting up the project to creating a secure login system, deploying services, and managing permissions.

## 🗄️ Database Setup Options
This repository includes two options for setting up your database:

1. Step-by-Step Setup: Each part of the tutorial includes SQL snippets for creating only the necessary tables and records for that section (check the db folder -> part2.sql ~ part5.sql). This option is ideal if you are following along with the tutorial series and using the UI on the deployed website to create records.

2. Full Database Setup with all_db.sql: If you'd like to set up the entire database with all tables and records at once, or if you've missed any steps in the tutorial, you can use the (check the db folder -> all_db.sql) file. This script includes all SQL commands needed to create databases, tables, and insert data, ensuring your database is complete without following every step in the tutorial.

## 🖥️ Flask Code
You can check the folder "flask_demo," where all our three necessary folders and related code in this tutorial are located. Follow the tutorial series and implement these codes to learn and practice Flask development. Have fun exploring and building your Flask web application!

### Three Folders in flask_demo
- **website**: part 2
- **service**: part 3
- **admin_management**: part 5  
(Permission in part 4 is directly added to the file)

## 🚨 Important Setup Reminder  

### Step 1: Update the Database Configuration
Locate the following code snippet and update it with your credentials:

<pre>
create_engine("mssql+pyodbc://your_db_user_name:your_db_password@your_IP/demo?driver=ODBC+Driver+17+for+SQL+Server", pool_pre_ping=True)
</pre>

- Replace `your_db_user_name` with your database username.
- Replace `your_db_password` with your database password.
- Replace `your_IP` with the IP address of your database server.

### Step 2: Update HTML Files
- Search for all instances of `192.168.8.12` in your HTML files and replace them with your own IP address to ensure everything works correctly.
