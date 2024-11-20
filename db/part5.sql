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