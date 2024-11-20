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
    (1, 2, 2),
    (4, 2, 2);