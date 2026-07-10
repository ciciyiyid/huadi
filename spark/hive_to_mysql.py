from __future__ import annotations

import sys
from dataclasses import dataclass

from pyspark.sql import DataFrame, SparkSession


# ============================================================
# 1. MySQL JDBC 配置
# ============================================================
MYSQL_URL = (
    "jdbc:mysql://localhost:3306/online_learning_db"
    "?useSSL=false"
    "&allowPublicKeyRetrieval=true"
    "&serverTimezone=UTC"
    "&useUnicode=true"
    "&characterEncoding=UTF-8"
    "&rewriteBatchedStatements=true"
)

MYSQL_USER = "online_app"
MYSQL_PASSWORD = "Online@123456"
MYSQL_DRIVER = "com.mysql.cj.jdbc.Driver"


# ============================================================
# 2. HDFS 表路径与 MySQL 表名映射
# ============================================================
@dataclass(frozen=True)
class SyncTask:
    """一张 HDFS ORC 表到一张 MySQL 表的同步任务。"""

    hdfs_path: str
    mysql_table: str


SYNC_TASKS = [
    SyncTask(
        hdfs_path=(
            "hdfs://UESTC04/user/hive/warehouse/"
            "online_learning.db/dim_student_info"
        ),
        mysql_table="student_info",
    ),
    SyncTask(
        hdfs_path=(
            "hdfs://UESTC04/user/hive/warehouse/"
            "online_learning.db/dim_course_info"
        ),
        mysql_table="course_info",
    ),
    SyncTask(
        hdfs_path=(
            "hdfs://UESTC04/user/hive/warehouse/"
            "online_learning.db/dws_student_stat"
        ),
        mysql_table="student_stat",
    ),
    SyncTask(
        hdfs_path=(
            "hdfs://UESTC04/user/hive/warehouse/"
            "online_learning.db/dws_course_stat"
        ),
        mysql_table="course_stat",
    ),
    SyncTask(
        hdfs_path=(
            "hdfs://UESTC04/user/hive/warehouse/"
            "online_learning.db/dws_student_feature"
        ),
        mysql_table="student_feature",
    ),
]


# ============================================================
# 3. 各 MySQL 表要求写入的字段
# ============================================================
TABLE_COLUMNS = {
    "student_info": [
        "student_id",
        "student_name",
        "gender",
        "age",
        "education_level",
        "employment_status",
        "city",
        "device_type",
        "internet_connection_quality",
        "create_time",
        "update_time",
    ],

    "course_info": [
        "course_id",
        "course_name",
        "category",
        "course_level",
        "course_duration_days",
        "instructor_rating",
        "create_time",
        "update_time",
    ],

    "student_stat": [
        # MySQL 的 id 是自增主键，不从 Spark 写入
        "student_id",
        "course_id",
        "total_study_time_hours",
        "avg_session_duration_min",
        "course_progress_rate",
        "course_completed",
        "assignment_submit_rate",
        "quiz_score_avg",
        "project_grade",
        "login_frequency",
        "video_completion_rate",
        "discussion_participation",
        "peer_interaction_score",
        "days_since_last_login",
        "app_usage_percentage",
        "satisfaction_rating",
        "update_date",
        "create_time",
        "update_time",
    ],

    "course_stat": [
        "course_id",
        "course_name",
        "category",
        "course_level",
        "course_duration_days",
        "learner_count",
        "completion_count",
        "completion_rate",
        "avg_study_time_hours",
        "avg_progress_percentage",
        "avg_video_completion_rate",
        "avg_assignment_submit_rate",
        "avg_quiz_score",
        "avg_project_grade",
        "avg_instructor_rating",
        "avg_satisfaction_rating",
        "avg_app_usage_percentage",
        "update_date",
        "create_time",
        "update_time",
    ],

    "student_feature": [
        "student_id",
        "course_count",
        "completed_course_count",
        "completion_rate",
        "total_study_time_hours",
        "avg_session_duration_min",
        "avg_login_frequency",
        "avg_video_completion_rate",
        "avg_progress_percentage",
        "avg_assignment_submit_rate",
        "avg_quiz_score",
        "avg_project_grade",
        "avg_discussion_participation",
        "avg_peer_interaction_score",
        "avg_app_usage_percentage",
        "avg_satisfaction_rating",
        "avg_days_since_last_login",
        "total_assignments_missed",
        "update_date",
        "update_time",
    ],
}


# ============================================================
# 4. 创建 SparkSession
# ============================================================
def create_spark_session() -> SparkSession:
    """
    创建 SparkSession。

    不启用 enableHiveSupport()，避免 Spark 内置 Hive 2.3.10
    客户端与 Hive 4.2.0 Metastore 接口不兼容。

    这里直接读取 Hive 表在 HDFS 中保存的 ORC 文件。
    """
    spark = (
        SparkSession.builder
        .appName("HdfsOrcToMySQLSync")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.orc.impl", "native")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    return spark


# ============================================================
# 5. 检查并整理字段
# ============================================================
def prepare_dataframe(
    dataframe: DataFrame,
    mysql_table: str,
) -> DataFrame:
    """
    检查 HDFS 表字段，并按照 MySQL 表字段顺序进行选择。

    如果字段缺失，则停止运行，防止错位写入。
    """
    if mysql_table not in TABLE_COLUMNS:
        raise KeyError(f"未配置 MySQL 表字段：{mysql_table}")

    required_columns = TABLE_COLUMNS[mysql_table]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"\nMySQL 表 {mysql_table} 对应的 HDFS 数据缺少字段："
            f"{missing_columns}\n"
            f"HDFS 实际字段：{dataframe.columns}"
        )

    return dataframe.select(*required_columns)


# ============================================================
# 6. 清空 MySQL 原表
# ============================================================
def truncate_mysql_table(
    spark: SparkSession,
    mysql_table: str,
) -> None:
    """
    使用 JDBC 执行 TRUNCATE TABLE。

    只清空数据，不删除 MySQL 表，因此能够保留：
    - 主键
    - 唯一索引
    - 普通索引
    - 自增主键
    - 字段类型
    - 表注释
    """
    jvm = spark.sparkContext._gateway.jvm

    jvm.java.lang.Class.forName(MYSQL_DRIVER)

    connection = jvm.java.sql.DriverManager.getConnection(
        MYSQL_URL,
        MYSQL_USER,
        MYSQL_PASSWORD,
    )

    statement = None

    try:
        statement = connection.createStatement()

        sql = f"TRUNCATE TABLE `{mysql_table}`"
        statement.executeUpdate(sql)

        print(f"MySQL 表已清空：{mysql_table}")

    finally:
        if statement is not None:
            statement.close()

        connection.close()


# ============================================================
# 7. 读取 MySQL 表行数
# ============================================================
def get_mysql_row_count(
    spark: SparkSession,
    mysql_table: str,
) -> int:
    """同步完成后查询 MySQL 表行数。"""
    query = f"(SELECT COUNT(*) AS row_count FROM `{mysql_table}`) AS count_table"

    result = (
        spark.read
        .format("jdbc")
        .option("url", MYSQL_URL)
        .option("dbtable", query)
        .option("user", MYSQL_USER)
        .option("password", MYSQL_PASSWORD)
        .option("driver", MYSQL_DRIVER)
        .load()
        .first()
    )

    return int(result["row_count"])


# ============================================================
# 8. 同步单张表
# ============================================================
def sync_table(
    spark: SparkSession,
    task: SyncTask,
) -> None:
    """读取一张 HDFS ORC 表并写入对应的 MySQL 表。"""
    print("\n" + "=" * 75)
    print(f"开始同步 HDFS：{task.hdfs_path}")
    print(f"目标 MySQL 表：{task.mysql_table}")

    # 直接读取 Hive 表对应的 ORC 文件
    dataframe = spark.read.orc(task.hdfs_path)

    print(f"HDFS 原始字段：{dataframe.columns}")

    dataframe = prepare_dataframe(
        dataframe=dataframe,
        mysql_table=task.mysql_table,
    )

    # 缓存，避免 count 和 write 重复扫描文件
    dataframe = dataframe.cache()

    try:
        hdfs_row_count = dataframe.count()

        print(f"HDFS 数据行数：{hdfs_row_count}")
        print(f"写入字段：{dataframe.columns}")

        if hdfs_row_count <= 0:
            raise RuntimeError(
                f"HDFS 路径中没有有效数据：{task.hdfs_path}"
            )

        # 清空旧数据，保留 MySQL 表结构
        truncate_mysql_table(
            spark=spark,
            mysql_table=task.mysql_table,
        )

        # 10 万条数据使用少量分区写入，避免创建过多 MySQL 连接
        (
            dataframe
            .coalesce(4)
            .write
            .format("jdbc")
            .option("url", MYSQL_URL)
            .option("dbtable", task.mysql_table)
            .option("user", MYSQL_USER)
            .option("password", MYSQL_PASSWORD)
            .option("driver", MYSQL_DRIVER)
            .option("batchsize", "1000")
            .option("isolationLevel", "READ_COMMITTED")
            .mode("append")
            .save()
        )

        mysql_row_count = get_mysql_row_count(
            spark=spark,
            mysql_table=task.mysql_table,
        )

        print(f"MySQL 实际行数：{mysql_row_count}")

        if mysql_row_count != hdfs_row_count:
            raise RuntimeError(
                f"同步行数不一致："
                f"HDFS={hdfs_row_count}，"
                f"MySQL={mysql_row_count}"
            )

        print(
            f"同步成功：{task.mysql_table}，"
            f"共写入 {mysql_row_count} 行"
        )

    finally:
        dataframe.unpersist()


# ============================================================
# 9. 主程序
# ============================================================
def main() -> None:
    spark = create_spark_session()

    try:
        print("=" * 75)
        print("Spark 已启动")
        print(f"Spark 版本：{spark.version}")
        print("读取方式：直接读取 HDFS ORC")
        print("写入方式：MySQL TRUNCATE + JDBC append")
        print("=" * 75)

        for task in SYNC_TASKS:
            sync_table(
                spark=spark,
                task=task,
            )

        print("\n" + "=" * 75)
        print("五张成品表已全部同步到 MySQL")
        print("=" * 75)

    except Exception as exc:
        print("\n" + "=" * 75, file=sys.stderr)
        print(f"同步失败：{exc}", file=sys.stderr)
        print("=" * 75, file=sys.stderr)
        raise

    finally:
        spark.stop()
        print("SparkSession 已关闭")


if __name__ == "__main__":
    main()
