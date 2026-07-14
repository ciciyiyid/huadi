USE online_learning;

-- 学生统计
DROP TABLE IF EXISTS dws_student_stat;

CREATE TABLE dws_student_stat
STORED AS ORC
AS
SELECT
student_id,
course_id,
time_spent_hours AS total_study_time_hours,
average_session_duration_min AS avg_session_duration_min,
progress_percentage AS course_progress_rate,
completed AS course_completed,
assignment_submission_rate,
quiz_score_avg,
project_grade,
login_frequency,
video_completion_rate,
discussion_participation,
peer_interaction_score,
days_since_last_login,
app_usage_percentage,
satisfaction_rating,
CURRENT_DATE AS update_date,
CURRENT_TIMESTAMP AS create_time,
CURRENT_TIMESTAMP AS update_time
FROM dwd_online_learning;

-- 课程统计
DROP TABLE IF EXISTS dws_course_stat;

CREATE TABLE dws_course_stat
STORED AS ORC
AS
SELECT
course_id,
MAX(course_name) course_name,
MAX(category) category,
MAX(course_level) course_level,
MAX(course_duration_days) course_duration_days,
COUNT(*) learner_count,
SUM(completed) completion_count,
ROUND(AVG(completed)*100,2) completion_rate,
AVG(time_spent_hours) avg_study_time_hours,
AVG(progress_percentage) avg_progress_percentage,
AVG(video_completion_rate) avg_video_completion_rate,
AVG(assignment_submission_rate) avg_assignment_submit_rate,
AVG(quiz_score_avg) avg_quiz_score,
AVG(project_grade) avg_project_grade,
AVG(instructor_rating) avg_instructor_rating,
AVG(satisfaction_rating) avg_satisfaction_rating,
AVG(app_usage_percentage) avg_app_usage_percentage,
CURRENT_DATE update_date,
CURRENT_TIMESTAMP create_time,
CURRENT_TIMESTAMP update_time
FROM dwd_online_learning
GROUP BY course_id;

-- 学生画像特征
DROP TABLE IF EXISTS dws_student_feature;

CREATE TABLE dws_student_feature
STORED AS ORC
AS
SELECT
student_id,
COUNT(*) course_count,
SUM(completed) completed_course_count,
ROUND(AVG(completed)*100,2) completion_rate,
SUM(time_spent_hours) total_study_time_hours,
AVG(average_session_duration_min) avg_session_duration_min,
AVG(login_frequency) avg_login_frequency,
AVG(video_completion_rate) avg_video_completion_rate,
AVG(progress_percentage) avg_progress_percentage,
AVG(assignment_submission_rate) avg_assignment_submit_rate,
AVG(quiz_score_avg) avg_quiz_score,
AVG(project_grade) avg_project_grade,
AVG(discussion_participation) avg_discussion_participation,
AVG(peer_interaction_score) avg_peer_interaction_score,
AVG(app_usage_percentage) avg_app_usage_percentage,
AVG(satisfaction_rating) avg_satisfaction_rating,
AVG(days_since_last_login) avg_days_since_last_login,
SUM(assignments_missed) total_assignments_missed,
CURRENT_DATE update_date,
CURRENT_TIMESTAMP update_time
FROM dwd_online_learning
GROUP BY student_id;