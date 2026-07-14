USE online_learning;

DROP TABLE IF EXISTS dwd_online_learning;

CREATE TABLE dwd_online_learning
STORED AS ORC
AS
SELECT
student_id,
gender,
CAST(age AS INT) age,
education_level,
employment_status,
city,
device_type,
internet_connection_quality,
course_id,
course_name,
category,
course_level,
CAST(course_duration_days AS INT) course_duration_days,
CAST(instructor_rating AS DOUBLE) instructor_rating,
CAST(login_frequency AS INT) login_frequency,
CAST(average_session_duration_min AS DOUBLE) average_session_duration_min,
CAST(video_completion_rate AS DOUBLE) video_completion_rate,
CAST(discussion_participation AS INT) discussion_participation,
CAST(time_spent_hours AS DOUBLE) time_spent_hours,
CAST(days_since_last_login AS INT) days_since_last_login,
CAST(notifications_checked AS INT) notifications_checked,
CAST(peer_interaction_score AS DOUBLE) peer_interaction_score,
CAST(assignments_submitted AS INT) assignments_submitted,
CAST(assignments_missed AS INT) assignments_missed,
CAST(quiz_attempts AS INT) quiz_attempts,
CAST(quiz_score_avg AS DOUBLE) quiz_score_avg,
CAST(project_grade AS DOUBLE) project_grade,
CAST(progress_percentage AS DOUBLE) progress_percentage,
CAST(rewatch_count AS INT) rewatch_count,
CAST(enrollment_date AS DATE) enrollment_date,
payment_mode,
CAST(fee_paid AS INT) fee_paid,
CAST(discount_used AS INT) discount_used,
CAST(payment_amount AS DOUBLE) payment_amount,
CAST(app_usage_percentage AS DOUBLE) app_usage_percentage,
CAST(reminder_emails_clicked AS INT) reminder_emails_clicked,
CAST(support_tickets_raised AS INT) support_tickets_raised,
CAST(satisfaction_rating AS DOUBLE) satisfaction_rating,
CAST(completed AS INT) completed,
CAST(assignment_submission_rate AS DOUBLE) assignment_submission_rate
FROM ods_online_learning;