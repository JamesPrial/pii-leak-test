-- ============================================================================
-- PII Leak Test Database - SQL Query Examples
-- ============================================================================
-- This file contains practical SQL queries for analyzing synthetic PII data
-- organized by use case and complexity level.
-- ============================================================================

-- ============================================================================
-- 1. BASIC QUERIES
-- ============================================================================

-- Count total staff records
SELECT COUNT(*) AS total_staff
FROM staff_pii;

-- Count total client records
SELECT COUNT(*) AS total_clients
FROM client_pii;

-- View sample staff records (LIMIT 5)
-- Shows all fields for first 5 staff members
SELECT *
FROM staff_pii
LIMIT 5;

-- View sample client records (LIMIT 5)
-- Shows all fields for first 5 clients
SELECT *
FROM client_pii
LIMIT 5;


-- ============================================================================
-- 2. SENSITIVITY-BASED QUERIES
-- ============================================================================

-- Select only low sensitivity fields from staff
-- Low sensitivity: name, department, job_title, hire_date
SELECT
    name,
    department,
    job_title,
    hire_date
FROM staff_pii
ORDER BY hire_date DESC;

-- Select only low/medium sensitivity fields (exclude critical/high)
-- Excludes: ssn, dob, salary, bank_account_number, credit_card_number, medical_condition
SELECT
    employee_id,
    name,
    department,
    job_title,
    hire_date,
    email,
    phone,
    address,
    manager
FROM staff_pii
ORDER BY employee_id;

-- List critical sensitivity fields only
-- Critical fields: ssn, bank_account_number, medical_condition
SELECT
    employee_id,
    name,
    ssn,
    bank_account_number,
    medical_condition
FROM staff_pii
WHERE medical_condition IS NOT NULL
   OR bank_account_number IS NOT NULL
ORDER BY employee_id;

-- Show critical PII fields for clients
SELECT
    name,
    ssn,
    credit_card,
    medical_condition
FROM client_pii
WHERE medical_condition IS NOT NULL
ORDER BY name;


-- ============================================================================
-- 3. DEPARTMENT ANALYTICS
-- ============================================================================

-- Count staff by department
-- Shows distribution of employees across departments
SELECT
    department,
    COUNT(*) AS employee_count
FROM staff_pii
GROUP BY department
ORDER BY employee_count DESC;

-- Average salary by department
-- Reveals salary patterns and department compensation levels
SELECT
    department,
    COUNT(*) AS employee_count,
    ROUND(AVG(salary), 2) AS avg_salary,
    MIN(salary) AS min_salary,
    MAX(salary) AS max_salary
FROM staff_pii
GROUP BY department
ORDER BY avg_salary DESC;

-- List managers and their departments
-- Identifies all managers in the organization
SELECT
    name,
    department,
    job_title,
    email
FROM staff_pii
WHERE manager IS NULL
   OR job_title LIKE '%Manager%'
   OR job_title LIKE '%Director%'
   OR job_title LIKE '%VP%'
ORDER BY department, name;

-- Staff hired per year
-- Shows hiring trends over time
SELECT
    EXTRACT(YEAR FROM hire_date) AS hire_year,
    COUNT(*) AS hires_count
FROM staff_pii
GROUP BY hire_year
ORDER BY hire_year DESC;


-- ============================================================================
-- 4. GEOGRAPHIC ANALYSIS
-- ============================================================================

-- Staff grouped by state (extracting from address)
-- Analyzes geographic distribution of workforce
SELECT
    SUBSTRING(address FROM ',\s*([A-Z]{2})\s+\d{5}') AS state,
    COUNT(*) AS employee_count
FROM staff_pii
GROUP BY state
ORDER BY employee_count DESC;

-- Most common area codes (from phone numbers)
-- Identifies primary geographic regions based on phone numbers
SELECT
    SUBSTRING(phone FROM '^\(?(\d{3})\)?') AS area_code,
    COUNT(*) AS count
FROM staff_pii
WHERE phone IS NOT NULL
GROUP BY area_code
ORDER BY count DESC
LIMIT 10;

-- Client distribution by state
SELECT
    SUBSTRING(address FROM ',\s*([A-Z]{2})\s+\d{5}') AS state,
    COUNT(*) AS client_count
FROM client_pii
GROUP BY state
ORDER BY client_count DESC;


-- ============================================================================
-- 5. MANAGER HIERARCHY QUERIES
-- ============================================================================

-- List all managers with count of direct reports
-- Shows organizational structure and span of control
SELECT
    manager,
    COUNT(*) AS direct_reports
FROM staff_pii
WHERE manager IS NOT NULL
GROUP BY manager
ORDER BY direct_reports DESC;

-- Find staff without managers
-- Identifies top-level executives or data quality issues
SELECT
    employee_id,
    name,
    job_title,
    department
FROM staff_pii
WHERE manager IS NULL
ORDER BY department, name;

-- List staff who report to specific manager
-- Example: Replace 'John Smith' with actual manager name
SELECT
    employee_id,
    name,
    job_title,
    department,
    email
FROM staff_pii
WHERE manager = 'John Smith'
ORDER BY job_title, name;

-- Manager hierarchy depth analysis
-- Shows how many levels of management exist
SELECT
    CASE
        WHEN manager IS NULL THEN 'Executive (No Manager)'
        WHEN job_title LIKE '%VP%' OR job_title LIKE '%Director%' THEN 'Senior Management'
        WHEN job_title LIKE '%Manager%' THEN 'Middle Management'
        ELSE 'Individual Contributor'
    END AS hierarchy_level,
    COUNT(*) AS count
FROM staff_pii
GROUP BY hierarchy_level
ORDER BY count DESC;


-- ============================================================================
-- 6. SALARY ANALYSIS
-- ============================================================================

-- Top 10 highest paid staff members
-- Identifies highest earners in the organization
SELECT
    name,
    job_title,
    department,
    salary,
    hire_date
FROM staff_pii
ORDER BY salary DESC
LIMIT 10;

-- Salary distribution by seniority (job title patterns)
-- Analyzes compensation by seniority level
SELECT
    CASE
        WHEN job_title LIKE '%VP%' OR job_title LIKE '%Vice President%' THEN 'Executive'
        WHEN job_title LIKE '%Director%' THEN 'Director'
        WHEN job_title LIKE '%Manager%' THEN 'Manager'
        WHEN job_title LIKE '%Senior%' THEN 'Senior'
        WHEN job_title LIKE '%Junior%' OR job_title LIKE '%Coordinator%' THEN 'Junior'
        ELSE 'Mid-Level'
    END AS seniority_level,
    COUNT(*) AS employee_count,
    ROUND(AVG(salary), 2) AS avg_salary,
    MIN(salary) AS min_salary,
    MAX(salary) AS max_salary
FROM staff_pii
GROUP BY seniority_level
ORDER BY avg_salary DESC;

-- Comparison of staff vs client average salaries
-- Cross-table analysis of compensation
SELECT
    'Staff' AS record_type,
    COUNT(*) AS count,
    ROUND(AVG(salary), 2) AS avg_salary,
    MIN(salary) AS min_salary,
    MAX(salary) AS max_salary
FROM staff_pii
UNION ALL
SELECT
    'Clients' AS record_type,
    COUNT(*) AS count,
    ROUND(AVG(salary), 2) AS avg_salary,
    MIN(salary) AS min_salary,
    MAX(salary) AS max_salary
FROM client_pii
ORDER BY record_type;

-- Salary percentiles
-- Shows 25th, 50th (median), and 75th percentile salaries
SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary) AS percentile_25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY salary) AS median_salary,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary) AS percentile_75
FROM staff_pii;


-- ============================================================================
-- 7. MEDICAL CONDITIONS ANALYSIS
-- ============================================================================

-- Count of staff with medical conditions
-- Privacy-sensitive analysis for health trends
SELECT
    COUNT(*) AS total_staff,
    COUNT(medical_condition) AS staff_with_conditions,
    COUNT(*) - COUNT(medical_condition) AS staff_without_conditions,
    ROUND(100.0 * COUNT(medical_condition) / COUNT(*), 2) AS percentage_with_conditions
FROM staff_pii;

-- Most common medical conditions
-- Identifies prevalent health conditions in staff population
SELECT
    medical_condition,
    COUNT(*) AS count
FROM staff_pii
WHERE medical_condition IS NOT NULL
GROUP BY medical_condition
ORDER BY count DESC;

-- Department breakdown of medical conditions
-- Analyzes health condition distribution by department
SELECT
    department,
    COUNT(*) AS total_staff,
    COUNT(medical_condition) AS staff_with_conditions,
    ROUND(100.0 * COUNT(medical_condition) / COUNT(*), 2) AS percentage_with_conditions
FROM staff_pii
GROUP BY department
ORDER BY percentage_with_conditions DESC;

-- Client medical conditions analysis
SELECT
    medical_condition,
    COUNT(*) AS count
FROM client_pii
WHERE medical_condition IS NOT NULL
GROUP BY medical_condition
ORDER BY count DESC;


-- ============================================================================
-- 8. DATA QUALITY CHECKS
-- ============================================================================

-- Find duplicate SSNs
-- Data integrity check - should return no results if data is clean
SELECT
    ssn,
    COUNT(*) AS occurrence_count
FROM staff_pii
GROUP BY ssn
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;

-- Find duplicate emails
-- Identifies potential data entry errors
SELECT
    email,
    COUNT(*) AS occurrence_count
FROM staff_pii
GROUP BY email
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;

-- Find invalid phone formats
-- Validates phone number format (expects XXX-XXX-XXXX)
SELECT
    employee_id,
    name,
    phone
FROM staff_pii
WHERE phone !~ '^\d{3}-\d{3}-\d{4}$'
ORDER BY employee_id;

-- Check for NULL values in critical fields
-- Ensures data completeness for essential fields
SELECT
    'employee_id' AS field_name,
    COUNT(*) AS null_count
FROM staff_pii
WHERE employee_id IS NULL
UNION ALL
SELECT 'name', COUNT(*) FROM staff_pii WHERE name IS NULL
UNION ALL
SELECT 'ssn', COUNT(*) FROM staff_pii WHERE ssn IS NULL
UNION ALL
SELECT 'email', COUNT(*) FROM staff_pii WHERE email IS NULL
UNION ALL
SELECT 'phone', COUNT(*) FROM staff_pii WHERE phone IS NULL
UNION ALL
SELECT 'salary', COUNT(*) FROM staff_pii WHERE salary IS NULL
ORDER BY null_count DESC;

-- Validate SSN format (XXX-XX-XXXX)
SELECT
    employee_id,
    name,
    ssn
FROM staff_pii
WHERE ssn !~ '^\d{3}-\d{2}-\d{4}$'
ORDER BY employee_id;

-- Check for future hire dates (data quality issue)
SELECT
    employee_id,
    name,
    hire_date
FROM staff_pii
WHERE hire_date > CURRENT_DATE
ORDER BY hire_date DESC;


-- ============================================================================
-- 9. CROSS-TABLE QUERIES
-- ============================================================================

-- Compare average salaries between staff and clients
-- Detailed cross-table comparison with statistical measures
SELECT
    'Staff' AS record_type,
    COUNT(*) AS total_records,
    ROUND(AVG(salary), 2) AS avg_salary,
    ROUND(STDDEV(salary), 2) AS salary_stddev,
    MIN(salary) AS min_salary,
    MAX(salary) AS max_salary
FROM staff_pii
UNION ALL
SELECT
    'Clients' AS record_type,
    COUNT(*) AS total_records,
    ROUND(AVG(salary), 2) AS avg_salary,
    ROUND(STDDEV(salary), 2) AS salary_stddev,
    MIN(salary) AS min_salary,
    MAX(salary) AS max_salary
FROM client_pii;

-- SSN format validation across both tables
-- Ensures consistent SSN formatting in both datasets
SELECT
    'Staff' AS table_name,
    COUNT(*) AS total_records,
    SUM(CASE WHEN ssn ~ '^\d{3}-\d{2}-\d{4}$' THEN 1 ELSE 0 END) AS valid_ssn_format,
    SUM(CASE WHEN ssn !~ '^\d{3}-\d{2}-\d{4}$' THEN 1 ELSE 0 END) AS invalid_ssn_format
FROM staff_pii
UNION ALL
SELECT
    'Clients' AS table_name,
    COUNT(*) AS total_records,
    SUM(CASE WHEN ssn ~ '^\d{3}-\d{2}-\d{4}$' THEN 1 ELSE 0 END) AS valid_ssn_format,
    SUM(CASE WHEN ssn !~ '^\d{3}-\d{2}-\d{4}$' THEN 1 ELSE 0 END) AS invalid_ssn_format
FROM client_pii;

-- Check for SSN overlap between staff and clients
-- Detects if any individual appears in both tables (should not happen with synthetic data)
SELECT
    s.ssn,
    s.name AS staff_name,
    c.name AS client_name
FROM staff_pii s
INNER JOIN client_pii c ON s.ssn = c.ssn
ORDER BY s.ssn;

-- Combined age analysis (calculate age from DOB)
-- Compares age distribution across staff and clients
SELECT
    'Staff' AS record_type,
    ROUND(AVG(EXTRACT(YEAR FROM AGE(date_of_birth))), 1) AS avg_age,
    MIN(EXTRACT(YEAR FROM AGE(date_of_birth))) AS min_age,
    MAX(EXTRACT(YEAR FROM AGE(date_of_birth))) AS max_age
FROM staff_pii
UNION ALL
SELECT
    'Clients' AS record_type,
    ROUND(AVG(EXTRACT(YEAR FROM AGE(date_of_birth))), 1) AS avg_age,
    MIN(EXTRACT(YEAR FROM AGE(date_of_birth))) AS min_age,
    MAX(EXTRACT(YEAR FROM AGE(date_of_birth))) AS max_age
FROM client_pii;

-- Email domain distribution across both tables
-- Analyzes email provider usage patterns
SELECT
    SUBSTRING(email FROM '@(.+)$') AS email_domain,
    COUNT(*) AS count
FROM (
    SELECT email FROM staff_pii
    UNION ALL
    SELECT email FROM client_pii
) AS all_emails
WHERE email IS NOT NULL
GROUP BY email_domain
ORDER BY count DESC;


-- ============================================================================
-- ADVANCED ANALYTICAL QUERIES
-- ============================================================================

-- Tenure analysis (years of service)
-- Calculates employee tenure and groups by ranges
SELECT
    CASE
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, hire_date)) < 1 THEN '< 1 year'
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, hire_date)) BETWEEN 1 AND 3 THEN '1-3 years'
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, hire_date)) BETWEEN 3 AND 5 THEN '3-5 years'
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, hire_date)) BETWEEN 5 AND 10 THEN '5-10 years'
        ELSE '10+ years'
    END AS tenure_range,
    COUNT(*) AS employee_count
FROM staff_pii
GROUP BY tenure_range
ORDER BY
    CASE tenure_range
        WHEN '< 1 year' THEN 1
        WHEN '1-3 years' THEN 2
        WHEN '3-5 years' THEN 3
        WHEN '5-10 years' THEN 4
        ELSE 5
    END;

-- Age distribution by department
-- Shows demographic patterns across departments
SELECT
    department,
    ROUND(AVG(EXTRACT(YEAR FROM AGE(date_of_birth))), 1) AS avg_age,
    MIN(EXTRACT(YEAR FROM AGE(date_of_birth))) AS min_age,
    MAX(EXTRACT(YEAR FROM AGE(date_of_birth))) AS max_age
FROM staff_pii
GROUP BY department
ORDER BY avg_age DESC;

-- Correlation between age and salary
-- Explores relationship between employee age and compensation
SELECT
    CASE
        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 30 THEN 'Under 30'
        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 30 AND 40 THEN '30-40'
        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 40 AND 50 THEN '40-50'
        WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 50 AND 60 THEN '50-60'
        ELSE '60+'
    END AS age_range,
    COUNT(*) AS employee_count,
    ROUND(AVG(salary), 2) AS avg_salary
FROM staff_pii
GROUP BY age_range
ORDER BY
    CASE age_range
        WHEN 'Under 30' THEN 1
        WHEN '30-40' THEN 2
        WHEN '40-50' THEN 3
        WHEN '50-60' THEN 4
        ELSE 5
    END;


-- ============================================================================
-- END OF QUERIES
-- ============================================================================
