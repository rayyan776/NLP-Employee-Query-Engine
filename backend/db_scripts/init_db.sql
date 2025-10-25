
-- Create Departments table
CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    manager_id INT
);

-- Create Employees table
CREATE TABLE employees (
    emp_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    dept_id INT REFERENCES departments(dept_id),
    position VARCHAR(50),
    annual_salary NUMERIC(10,2),
    join_date DATE,
    office_location VARCHAR(50)
);

-- Create Documents table
CREATE TABLE documents (
    doc_id SERIAL PRIMARY KEY,
    emp_id INT REFERENCES employees(emp_id),
    doc_type VARCHAR(50),
    content TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Departments
INSERT INTO departments (dept_name, manager_id) VALUES
('Engineering', 1),
('Human Resources', 2),
('Marketing', 3),
('Finance', 4),
('Sales', 5);

-- Seed 30 Employees
INSERT INTO employees (full_name, dept_id, position, annual_salary, join_date, office_location) VALUES
('Arjun Sharma', 1, 'Software Engineer', 120000, '2021-06-01', 'Mumbai'),
('Priya Verma', 1, 'Senior Developer', 150000, '2020-01-15', 'Bangalore'),
('Rohan Mehta', 2, 'HR Manager', 110000, '2019-09-10', 'Delhi'),
('Ananya Kapoor', 3, 'Marketing Executive', 90000, '2022-03-05', 'Mumbai'),
('Vikram Singh', 4, 'Finance Analyst', 95000, '2021-11-20', 'Chennai'),
('Neha Reddy', 5, 'Sales Lead', 100000, '2020-07-12', 'Hyderabad'),
('Karan Gupta', 1, 'DevOps Engineer', 130000, '2018-08-25', 'Bangalore'),
('Sanya Iyer', 2, 'HR Executive', 80000, '2021-04-18', 'Mumbai'),
('Aditya Joshi', 3, 'Marketing Manager', 125000, '2019-12-01', 'Delhi'),
('Meera Nair', 4, 'Finance Manager', 140000, '2020-05-23', 'Chennai'),
('Ritika Sen', 1, 'Frontend Developer', 110000, '2022-01-10', 'Bangalore'),
('Amitabh Roy', 1, 'Backend Developer', 115000, '2021-03-15', 'Mumbai'),
('Siddharth Malhotra', 1, 'QA Engineer', 90000, '2020-06-20', 'Bangalore'),
('Tanvi Desai', 2, 'HR Coordinator', 85000, '2021-08-05', 'Delhi'),
('Harsh Vardhan', 2, 'Recruiter', 75000, '2020-10-10', 'Mumbai'),
('Pooja Bhatia', 3, 'Content Strategist', 95000, '2021-11-11', 'Bangalore'),
('Manish Kumar', 3, 'SEO Specialist', 90000, '2019-09-09', 'Delhi'),
('Shreya Iyer', 3, 'Marketing Analyst', 100000, '2020-12-12', 'Chennai'),
('Rahul Choudhary', 4, 'Accountant', 85000, '2021-02-14', 'Mumbai'),
('Divya Patil', 4, 'Financial Analyst', 90000, '2019-07-07', 'Bangalore'),
('Saurabh Saxena', 5, 'Sales Executive', 80000, '2020-04-04', 'Delhi'),
('Nisha Rao', 5, 'Business Development', 95000, '2021-05-05', 'Hyderabad'),
('Kunal Mehta', 5, 'Sales Associate', 75000, '2022-02-02', 'Mumbai'),
('Anjali Gupta', 1, 'Software Architect', 160000, '2018-09-09', 'Bangalore'),
('Vivek Joshi', 2, 'HR Analyst', 85000, '2020-06-06', 'Delhi'),
('Rhea Nair', 3, 'Marketing Coordinator', 90000, '2021-08-08', 'Mumbai'),
('Kabir Singh', 4, 'Finance Lead', 135000, '2019-11-11', 'Chennai'),
('Isha Sharma', 5, 'Sales Manager', 120000, '2020-03-03', 'Bangalore'),
('Tanmay Kapoor', 1, 'Fullstack Developer', 125000, '2021-01-01', 'Mumbai'),
('Aarav Reddy', 2, 'HR Specialist', 80000, '2020-09-09', 'Hyderabad');

-- Seed Documents for 30 employees
INSERT INTO documents (emp_id, doc_type, content) VALUES
(1, 'Resume', 'Arjun Sharma - Software Engineer, Python, Django, React.'),
(2, 'Resume', 'Priya Verma - Senior Developer, Java, Spring Boot, AWS.'),
(3, 'Resume', 'Rohan Mehta - HR Manager, recruitment, employee relations.'),
(4, 'Resume', 'Ananya Kapoor - Marketing Executive, social media, SEO.'),
(5, 'Resume', 'Vikram Singh - Finance Analyst, budgeting, forecasting.'),
(6, 'Resume', 'Neha Reddy - Sales Lead, B2B sales, client management.'),
(7, 'Resume', 'Karan Gupta - DevOps Engineer, CI/CD, Docker, Kubernetes.'),
(8, 'Resume', 'Sanya Iyer - HR Executive, onboarding, payroll.'),
(9, 'Resume', 'Aditya Joshi - Marketing Manager, campaigns, analytics.'),
(10, 'Resume', 'Meera Nair - Finance Manager, auditing, financial planning.'),
(11, 'Resume', 'Ritika Sen - Frontend Developer, React, JavaScript, CSS.'),
(12, 'Resume', 'Amitabh Roy - Backend Developer, Node.js, SQL, APIs.'),
(13, 'Resume', 'Siddharth Malhotra - QA Engineer, testing, Selenium, JIRA.'),
(14, 'Resume', 'Tanvi Desai - HR Coordinator, employee engagement, payroll.'),
(15, 'Resume', 'Harsh Vardhan - Recruiter, hiring, interviews.'),
(16, 'Resume', 'Pooja Bhatia - Content Strategist, blogs, SEO.'),
(17, 'Resume', 'Manish Kumar - SEO Specialist, keywords, analytics.'),
(18, 'Resume', 'Shreya Iyer - Marketing Analyst, campaigns, metrics.'),
(19, 'Resume', 'Rahul Choudhary - Accountant, bookkeeping, tax filings.'),
(20, 'Resume', 'Divya Patil - Financial Analyst, reports, forecasting.'),
(21, 'Resume', 'Saurabh Saxena - Sales Executive, client acquisition.'),
(22, 'Resume', 'Nisha Rao - Business Development, lead generation.'),
(23, 'Resume', 'Kunal Mehta - Sales Associate, customer follow-ups.'),
(24, 'Resume', 'Anjali Gupta - Software Architect, Python, React, Cloud.'),
(25, 'Resume', 'Vivek Joshi - HR Analyst, metrics, recruitment.'),
(26, 'Resume', 'Rhea Nair - Marketing Coordinator, social media, campaigns.'),
(27, 'Resume', 'Kabir Singh - Finance Lead, budgeting, investments.'),
(28, 'Resume', 'Isha Sharma - Sales Manager, targets, team management.'),
(29, 'Resume', 'Tanmay Kapoor - Fullstack Developer, Node.js, React.'),
(30, 'Resume', 'Aarav Reddy - HR Specialist, employee relations, compliance.');
