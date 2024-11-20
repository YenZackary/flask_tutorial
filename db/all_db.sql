-- Part 2: Setup demo database and Users table
CREATE DATABASE demo;
USE demo;

CREATE TABLE dbo.Users_Data (
    user_id   INT IDENTITY NOT NULL,
    username  VARCHAR(255) NOT NULL,
    password  VARCHAR(255) NOT NULL,
    role_id   INT NULL,
    activate  VARCHAR(10) NULL,
    PRIMARY KEY (user_id)
);

INSERT INTO dbo.Users_Data (username, password, role_id, activate) VALUES
('user1', '123', 2, 1),
('user2', '123', 2, 0),
('user3', '123', 1, 0),
('user4', '123', 1, 1),
('user5', '123', 2, 1);

CREATE TABLE dbo.Login_Status (
    id          INT IDENTITY NOT NULL,
    user_id     INT NOT NULL,
    status      VARCHAR(50) NOT NULL,
    IP          VARCHAR(50) NOT NULL,
    access_time DATETIME NOT NULL,
    PRIMARY KEY (id)
);

-- Part 3: Setup service_info database and tables for name input and services
CREATE DATABASE service_info;
USE service_info;

CREATE TABLE dbo.name_input (
    input_id  INT IDENTITY NOT NULL,
    nameinput VARCHAR(255) NOT NULL,
    PRIMARY KEY (input_id)
);

USE demo;

CREATE TABLE dbo.Services (
    service_id   INT IDENTITY NOT NULL,
    service_name NVARCHAR(255) NOT NULL,
    IP           NVARCHAR(255) NOT NULL,
    category     NVARCHAR(50) NOT NULL,
    PRIMARY KEY (service_id)
);

INSERT INTO dbo.Services (service_name, IP, category) 
VALUES 
('hello', 'http://192.168.8.12:5001/hello', 'QC'),
('review', 'http://192.168.8.12:5001/review', 'HM'),
('Service_management', 'http://192.168.8.12:5002/service_management/service_overview', 'Admin'),
('User_management', 'http://192.168.8.12:5002/user_management/user_overview', 'Admin'),
('Permission_management', 'http://192.168.8.12:5002/permission_management/permission_overview', 'Admin'),
('Daily_monitor', 'http://192.168.8.12:5002/monitor', 'Admin');

-- Part 4: Permissions table
USE demo;

CREATE TABLE dbo.Permissions (
    user_id    INT NOT NULL,
    service_id INT NOT NULL,
    role_id    INT NULL,
    PRIMARY KEY (user_id, service_id)
);

INSERT INTO dbo.Permissions (user_id, service_id, role_id) 
VALUES 
(1, 1, 2),
(1, 2, 2),
(1, 3, 2),
(1, 4, 2),
(1, 5, 2),
(1, 6, 2),
(2, 2, 2),
(2, 3, 2),
(2, 4, 2),
(2, 6, 2),
(3, 4, 1),
(3, 5, 1),
(4, 2, 2),
(5, 1, 2),
(5, 2, 2);


-- Part 5: Service Access Log table
USE demo;

CREATE TABLE dbo.ServiceAccessLog (
    id                 INT IDENTITY NOT NULL,
    service_id         INT NOT NULL,
    user_id            INT NOT NULL,
    access_date        DATE DEFAULT GETDATE() NULL,
    today_access_times INT DEFAULT 1 NULL,
    PRIMARY KEY (id)
);