from flask import Blueprint, jsonify, g

from auth_utils import token_required
from db import query_all, query_one


profile_bp = Blueprint("profile_bp", __name__, url_prefix="/api/profiles")


def _check_student_permission(student_id: str):
    role = g.current_user.get("role")
    if role in {"admin", "teacher"}:
        return None
    if role == "student" and g.current_user.get("student_id") == student_id:
        return None
    return jsonify({"message": "无权限查看该学生画像"}), 403


@profile_bp.get("/students/<student_id>/daily-trend")
@token_required
def student_daily_trend(student_id: str):
    return jsonify({"message": "数据库无学生每日粒度数据，该接口暂不可用"}), 503


@profile_bp.get("/students/<student_id>")
@token_required
def student_detail(student_id: str):
    denial = _check_student_permission(student_id)
    if denial:
        return denial

    basic = query_one(
        """
        SELECT student_id, student_name, gender, age, education_level,
               employment_status, city, device_type, internet_connection_quality
        FROM student_info WHERE student_id = %s
        """,
        (student_id,),
    )
    feature = query_one(
        """
        SELECT student_id, completion_rate, total_study_time_hours,
               avg_session_duration_min, avg_login_frequency,
               avg_video_completion_rate, avg_progress_percentage,
               avg_quiz_score, avg_project_grade,
               avg_discussion_participation, avg_peer_interaction_score,
               total_assignments_missed
        FROM student_feature WHERE student_id = %s
        """,
        (student_id,),
    )
    profile = query_one(
        """
        SELECT Student_ID, 人群标签, total_duration, avg_completion_rate,
               avg_quiz_score, avg_progress, avg_project_grade,
               login_freq, avg_days_since_login
        FROM student_profile_detail WHERE Student_ID = %s
        """,
        (student_id,),
    )
    warning = query_one(
        """
        SELECT Student_ID, Course_ID, Course_Name, warning_level, risk_sum,
               Quiz_Score_Avg, Assignment_Submission_Rate, Progress_Percentage,
               Video_Completion_Rate
        FROM student_warning_detail WHERE Student_ID = %s
        LIMIT 1
        """,
        (student_id,),
    )

    if not basic:
        return jsonify({"message": "student_id 不存在"}), 404

    courses = query_all(
        """
        SELECT s.course_id AS Course_ID, ci.course_name AS Course_Name,
               s.total_study_time_hours, s.avg_session_duration_min,
               s.course_progress_rate AS completion_rate,
               s.course_progress_rate AS avg_progress_percentage,
               s.video_completion_rate AS avg_video_completion_rate,
               s.quiz_score_avg AS avg_quiz_score,
               s.project_grade AS avg_project_grade,
               s.assignment_submit_rate AS Assignment_Submission_Rate,
               s.course_progress_rate AS Progress_Percentage,
               s.video_completion_rate AS Video_Completion_Rate,
               s.quiz_score_avg AS Quiz_Score_Avg,
               COALESCE(w.warning_level, '安全') AS warning_level,
               COALESCE(CAST(w.risk_sum AS UNSIGNED), 0) AS risk_sum,
               s.login_frequency AS learning_days
        FROM student_stat s
        LEFT JOIN course_info ci ON s.course_id = ci.course_id
        LEFT JOIN student_warning_detail w ON s.student_id = w.Student_ID AND s.course_id = w.Course_ID
        WHERE s.student_id = %s
        """,
        (student_id,),
    )

    return jsonify(
        {
            "basic": basic,
            "feature": feature,
            "profile": profile,
            "warning": warning,
            "courses": courses,
        }
    )


@profile_bp.get("/students/summary")
@profile_bp.get("/students/summary")
@token_required
def student_summary():
    rows = query_all(
        """
        SELECT 人群标签, student_count, ratio_percent,
               avg_completion_rate, avg_quiz_score, avg_age
        FROM student_profile_summary
        ORDER BY student_count DESC
        """
    )
    return jsonify(rows)


@profile_bp.get("/teachers/summary")
@token_required
def teacher_summary():
    rows = query_all(
        """
        SELECT 教学效能评级, course_count, ratio_percent,
               avg_effect_score, avg_instructor_rating, avg_student_count
        FROM teacher_profile_summary
        ORDER BY avg_effect_score DESC
        """
    )
    return jsonify(rows)


@profile_bp.get("/teachers/<course_id>")
@token_required
def teacher_detail(course_id: str):
    role = g.current_user.get("role")
    if role == "teacher" and g.current_user.get("course_id") not in {None, "", course_id}:
        return jsonify({"message": "教师仅可查看自己课程画像"}), 403

    row = query_one(
        """
        SELECT Course_ID, Course_Name, 教学效能评级, teaching_effect_score,
               avg_instructor_rating, avg_student_satisfaction,
               avg_video_completion, avg_student_progress,
               course_finish_rate, avg_quiz_score,
               avg_discussion_participation, avg_assignment_submit_rate,
               total_student_count, course_level, course_category
        FROM teacher_profile_detail
        WHERE Course_ID = %s
        """,
        (course_id,),
    )
    if not row:
        return jsonify({"message": "course_id 不存在"}), 404
    return jsonify(row)
