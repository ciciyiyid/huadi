import sys
from pathlib import Path

# 确保 backend 目录在 sys.path 最前面，避免导入旧缓存模块
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from api.auth_routes import auth_bp
from api.intervention_routes import intervention_bp
from api.overview_routes import overview_bp
from api.profile_routes import profile_bp
from api.resource_routes import resource_bp
from api.warning_routes import warning_bp
from config import config
from db import execute


load_dotenv()


def init_auth_tables():
    sql_path = Path(__file__).parent / "sql" / "init_auth.sql"
    sql_text = sql_path.read_text(encoding="utf-8")
    for statement in [s.strip() for s in sql_text.split(";") if s.strip()]:
        execute(statement)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    init_auth_tables()

    app.register_blueprint(auth_bp)
    app.register_blueprint(intervention_bp)
    app.register_blueprint(overview_bp)
    app.register_blueprint(resource_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(warning_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"message": "接口不存在"}), 404

    @app.errorhandler(Exception)
    def unknown_error(err):
        return jsonify({"message": "服务器异常", "detail": str(err)}), 500

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(
        host=config.flask_host,
        port=config.flask_port,
        debug=config.flask_debug,
        use_reloader=False,  # 关闭自动重载，避免 Windows 上 reloader 导致进程退出
    )
