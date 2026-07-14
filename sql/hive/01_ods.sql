CREATE DATABASE IF NOT EXISTS online_learning;

USE online_learning;

DROP TABLE IF EXISTS ods_online_learning;

CREATE EXTERNAL TABLE ods_online_learning(
    student_id STRING,
    gender STRING,
    age STRING,
    education_level STRING,
    employment_status STRING,
    city STRING,
    device_type STRING,
    internet_connection_quality STRING,
    course_id STRING,
    course_name STRING,
    category STRING,
    course_level STRING,
    course_duration_days STRING,
    instructor_rating STRING,
    login_frequency STRING,
    average_session_duration_min STRING,
    video_completion_rate STRING,
    discussion_participation STRING,
    time_spent_hours STRING,
    days_since_last_login STRING,
    notifications_checked STRING,
    peer_interaction_score STRING,
    assignments_submitted STRING,
    assignments_missed STRING,
    quiz_attempts STRING,
    quiz_score_avg STRING,
    project_grade STRING,
    progress_percentage STRING,
    rewatch_count STRING,
    enrollment_date STRING,
    payment_mode STRING,
    fee_paid STRING,
    discount_used STRING,
    payment_amount STRING,
    app_usage_percentage STRING,
    reminder_emails_clicked STRING,
    support_tickets_raised STRING,
    satisfaction_rating STRING,
    completed STRING,
    assignment_submission_rate STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/project/online_learning/ods'
TBLPROPERTIES ("skip.header.line.count"="1");