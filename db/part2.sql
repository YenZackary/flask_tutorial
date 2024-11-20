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

CREATE TABLE dbo.Login_Status (
    id          INT IDENTITY NOT NULL,
    user_id     INT NOT NULL,
    status      VARCHAR(50) NOT NULL,
    IP          VARCHAR(50) NOT NULL,
    access_time DATETIME NOT NULL,
    PRIMARY KEY (id)
);

INSERT INTO dbo.Users_Data (username, password, role_id, activate) 
VALUES ('user1', '123', 2, '1');
