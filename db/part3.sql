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
    ('review', 'http://192.168.8.12:5001/review', 'HM');