USE online_learning;

DROP TABLE IF EXISTS dim_student_info;

CREATE TABLE dim_student_info
STORED AS ORC
AS
SELECT DISTINCT
student_id,
gender,
age,
education_level,
employment_status,
city,
device_type,
internet_connection_quality
FROM dwd_online_learning;

DROP TABLE IF EXISTS dim_course_info;

CREATE TABLE dim_course_info
STORED AS ORC
AS
SELECT DISTINCT
course_id,
course_name,
category,
course_level,
course_duration_days,
instructor_rating
FROM dwd_online_learning;