from flask import Blueprint, jsonify

from auth_utils import token_required
from db import query_all


resource_bp = Blueprint("resource_bp", __name__, url_prefix="/api/resources")


@resource_bp.get("/core-stats")
@token_required
def core_stats():
    rows = query_all(
        """
        SELECT resource_id, resource_name, resource_category, resource_level,
               learner_count, access_volume, avg_usage_rate,
               avg_video_completion_rate, total_rewatch_count,
               avg_study_time_hours, usage_rank
        FROM resource_core_statistics
        ORDER BY usage_rank
        """
    )
    return jsonify(rows)
