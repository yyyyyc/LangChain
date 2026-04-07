USE [company_demo];
GO

/*========================================================
  Clean up old tables if they already exist
========================================================*/
IF OBJECT_ID('dbo.Hierarchy', 'U') IS NOT NULL
    DROP TABLE dbo.Hierarchy;
GO

IF OBJECT_ID('dbo.Workers', 'U') IS NOT NULL
    DROP TABLE dbo.Workers;
GO

IF OBJECT_ID('dbo.Cities', 'U') IS NOT NULL
    DROP TABLE dbo.Cities;
GO

IF OBJECT_ID('dbo.Departments', 'U') IS NOT NULL
    DROP TABLE dbo.Departments;
GO

/*========================================================
  Create Departments
========================================================*/
CREATE TABLE dbo.Departments
(
    department_id INT NOT NULL PRIMARY KEY,
    [name] NVARCHAR(100) NOT NULL
);
GO

/*========================================================
  Create Cities
========================================================*/
CREATE TABLE dbo.Cities
(
    city_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    city_name NVARCHAR(100) NOT NULL
);
GO

/*========================================================
  Create Workers
========================================================*/
CREATE TABLE dbo.Workers
(
    worker_id INT NOT NULL PRIMARY KEY,
    sur_name NVARCHAR(100) NOT NULL,
    first_name NVARCHAR(100) NOT NULL,
    age INT NOT NULL,
    [rank] NVARCHAR(100) NOT NULL,
    department_id INT NOT NULL,
    city_id INT NOT NULL,
    gender CHAR(1) NOT NULL,
    DOB DATE NOT NULL,

    CONSTRAINT FK_Workers_Departments
        FOREIGN KEY (department_id) REFERENCES dbo.Departments(department_id),

    CONSTRAINT FK_Workers_Cities
        FOREIGN KEY (city_id) REFERENCES dbo.Cities(city_id),

    CONSTRAINT CK_Workers_Gender
        CHECK (gender IN ('M', 'F')),

    CONSTRAINT CK_Workers_Age
        CHECK (age BETWEEN 18 AND 70)
);
GO

/*========================================================
  Create Hierarchy
========================================================*/
CREATE TABLE dbo.Hierarchy
(
    relation_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    worker_id INT NOT NULL,
    manager_id INT NOT NULL,

    CONSTRAINT FK_Hierarchy_Worker
        FOREIGN KEY (worker_id) REFERENCES dbo.Workers(worker_id),

    CONSTRAINT FK_Hierarchy_Manager
        FOREIGN KEY (manager_id) REFERENCES dbo.Workers(worker_id),

    CONSTRAINT UQ_Hierarchy_Worker UNIQUE (worker_id),

    CONSTRAINT CK_Hierarchy_NoSelfReference
        CHECK (worker_id <> manager_id)
);
GO

/*========================================================
  Insert Departments (4 departments)
========================================================*/
INSERT INTO dbo.Departments (department_id, [name])
VALUES
(1, N'Human Resources'),
(2, N'Finance'),
(3, N'IT'),
(4, N'Operations');
GO

/*========================================================
  Insert Cities
========================================================*/
INSERT INTO dbo.Cities (city_name)
VALUES
(N'Tel Aviv'),
(N'Jerusalem'),
(N'Haifa'),
(N'Petah Tikva'),
(N'Rishon LeZion'),
(N'Netanya'),
(N'Holon'),
(N'Beersheba');
GO

/*========================================================
  Insert Workers (30 workers)
========================================================*/
INSERT INTO dbo.Workers
(
    worker_id, sur_name, first_name, age, [rank],
    department_id, city_id, gender, DOB
)
VALUES
(1 , N'Cohen'    , N'Dan'    , 52, N'CEO'                , 4, 1, 'M', '1974-02-10'),
(2 , N'Levi'     , N'Maya'   , 46, N'HR Director'        , 1, 2, 'F', '1980-06-15'),
(3 , N'Mizrahi'  , N'Eyal'   , 44, N'Finance Director'   , 2, 3, 'M', '1982-03-22'),
(4 , N'Biton'    , N'Noa'    , 41, N'IT Director'        , 3, 4, 'F', '1985-08-11'),
(5 , N'Azoulay'  , N'Ronen'  , 48, N'Operations Director', 4, 5, 'M', '1978-11-05'),

(6 , N'Sharon'   , N'Liat'   , 38, N'HR Manager'         , 1, 1, 'F', '1988-01-19'),
(7 , N'Peretz'   , N'Omer'   , 35, N'Recruiter'          , 1, 6, 'M', '1991-04-03'),
(8 , N'Ben David', N'Tamar'  , 31, N'HR Specialist'      , 1, 7, 'F', '1995-09-14'),
(9 , N'Haddad'   , N'Yossi'  , 29, N'HR Coordinator'     , 1, 4, 'M', '1997-12-01'),
(10, N'Katz'     , N'Yael'   , 34, N'Training Lead'      , 1, 8, 'F', '1992-07-25'),
(11, N'Ohayon'   , N'Gil'    , 28, N'HR Analyst'         , 1, 5, 'M', '1998-05-17'),
(12, N'Dayan'    , N'Adi'    , 32, N'Recruitment Lead'   , 1, 2, 'F', '1994-10-30'),

(13, N'Abutbul'  , N'Nir'    , 39, N'Finance Manager'    , 2, 3, 'M', '1987-02-08'),
(14, N'Harari'   , N'Sharon' , 33, N'Accountant'         , 2, 1, 'F', '1993-01-13'),
(15, N'Rosen'    , N'Amit'   , 30, N'Financial Analyst'  , 2, 6, 'M', '1996-06-09'),
(16, N'Malka'    , N'Dana'   , 36, N'Payroll Lead'       , 2, 7, 'F', '1990-03-26'),
(17, N'Sabag'    , N'Ido'    , 27, N'Junior Accountant'  , 2, 4, 'M', '1999-08-18'),
(18, N'Elbaz'    , N'Rivka'  , 31, N'Budget Analyst'     , 2, 5, 'F', '1995-11-21'),
(19, N'Barda'    , N'Tal'    , 29, N'Accounts Payable'   , 2, 8, 'M', '1997-04-12'),

(20, N'Assulin'  , N'Orit'   , 37, N'IT Manager'         , 3, 4, 'F', '1989-09-07'),
(21, N'Zohar'    , N'Chen'   , 34, N'Software Engineer'  , 3, 1, 'M', '1992-02-27'),
(22, N'Avraham'  , N'Mor'    , 30, N'DBA'                , 3, 2, 'F', '1996-12-19'),
(23, N'Gabay'    , N'Itay'   , 28, N'System Administrator', 3, 3, 'M', '1998-10-04'),
(24, N'Nahum'    , N'Sivan'  , 33, N'QA Lead'            , 3, 6, 'F', '1993-05-29'),
(25, N'Amar'     , N'Alon'   , 27, N'Help Desk Specialist', 3, 7, 'M', '1999-07-16'),
(26, N'Israeli'  , N'Neta'   , 29, N'BI Developer'       , 3, 5, 'F', '1997-03-03'),

(27, N'Maimon'   , N'Keren'  , 40, N'Operations Manager' , 4, 8, 'F', '1986-04-20'),
(28, N'Vaknin'   , N'Elad'   , 35, N'Logistics Lead'     , 4, 1, 'M', '1991-01-31'),
(29, N'Turgeman' , N'Hila'   , 31, N'Planning Analyst'   , 4, 2, 'F', '1995-06-28'),
(30, N'Ben Haim' , N'Asaf'   , 26, N'Operations Coordinator', 4, 3, 'M', '2000-09-09');
GO

/*========================================================
  Insert Hierarchy
  worker_id -> manager_id
========================================================*/
INSERT INTO dbo.Hierarchy (worker_id, manager_id)
VALUES
-- Department heads report to CEO
(2, 1),
(3, 1),
(4, 1),
(5, 1),

-- HR team
(6, 2),
(7, 6),
(8, 6),
(9, 6),
(10, 6),
(11, 6),
(12, 6),

-- Finance team
(13, 3),
(14, 13),
(15, 13),
(16, 13),
(17, 13),
(18, 13),
(19, 13),

-- IT team
(20, 4),
(21, 20),
(22, 20),
(23, 20),
(24, 20),
(25, 20),
(26, 20),

-- Operations team
(27, 5),
(28, 27),
(29, 27),
(30, 27);
GO

/*========================================================
  Sample checks
========================================================*/
SELECT * FROM dbo.Departments;
SELECT * FROM dbo.Cities;
SELECT * FROM dbo.Workers;
SELECT * FROM dbo.Hierarchy;
GO