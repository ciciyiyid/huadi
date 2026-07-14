from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    count,
    round as spark_round,
    sum as spark_sum,
    when,
)


# ============================================================
# 1. 基础配置
# ============================================================
SPARK_MASTER = "spark://192.168.75.129:7077"

# Windows 主机在 VMware 网络中的地址
WINDOWS_HOST = "192.168.75.1"

# HDFS 清洗数据路径
HDFS_INPUT = (
    "hdfs://192.168.75.129/"
    "project/online_learning/ods/cleaned_online_learning.csv"
)

# Windows 本地 MySQL
MYSQL_URL = (
    "jdbc:mysql://192.168.75.1:3306/online_learning_db"
    "?useSSL=false"
    "&allowPublicKeyRetrieval=true"
    "&serverTimezone=UTC"
    "&useUnicode=true"
    "&characterEncoding=UTF-8"
)

MYSQL_TABLE = "course_core_statistics"

MYSQL_PROPERTIES = {
    "user": "online_app",
    "password": "Online@123456",
    "driver": "com.mysql.cj.jdbc.Driver",
}


# ============================================================
# 2. 创建 SparkSession
# ============================================================
spark = (
    SparkSession.builder
    .appName("CourseCoreStatisticsToMySQL")
    .master(SPARK_MASTER)
    .config("spark.driver.host", WINDOWS_HOST)
    .config("spark.driver.bindAddress", WINDOWS_HOST)
    .config(
        "spark.jars",
        r"E:\huadifinalproject\lib\mysql-connector-j-8.3.0.jar",
    )
    .config(
        "spark.driver.extraClassPath",
        r"E:\huadifinalproject\lib\mysql-connector-j-8.3.0.jar",
    )
    .config(
        "spark.executor.extraClassPath",
        "/home/huadi/opt/spark-4.1.2/jars/"
        "mysql-connector-j-8.3.0.jar",
    )
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("Spark 启动成功")
print("Spark Master：", spark.sparkContext.master)


try:
    # ========================================================
    # 3. 从 HDFS 读取数据
    # ========================================================
    df = (
        spark.read
        .option("header", True)
        .option("encoding", "UTF-8")
        .option("inferSchema", True)
        .csv(HDFS_INPUT)
    )

    print("读取 HDFS 成功")
    print("数据总行数：", df.count())
    print("数据总列数：", len(df.columns))

    # ========================================================
    # 4. 字段类型转换
    # ========================================================
    df = (
        df
        .withColumn(
            "Quiz_Score_Avg",
            col("Quiz_Score_Avg").cast("double"),
        )
        .withColumn(
            "Project_Grade",
            col("Project_Grade").cast("double"),
        )
        .withColumn(
            "Progress_Percentage",
            col("Progress_Percentage").cast("double"),
        )
        .withColumn(
            "Video_Completion_Rate",
            col("Video_Completion_Rate").cast("double"),
        )
        .withColumn(
            "Time_Spent_Hours",
            col("Time_Spent_Hours").cast("double"),
        )
        .withColumn(
            "Average_Session_Duration_Min",
            col("Average_Session_Duration_Min").cast("double"),
        )
        .withColumn(
            "Login_Frequency",
            col("Login_Frequency").cast("double"),
        )
        .withColumn(
            "Completed",
            col("Completed").cast("int"),
        )
    )

    # ========================================================
    # 5. 课程维度核心指标计算
    # ========================================================
    course_core_statistics = (
        df
        .filter(
            col("Course_ID").isNotNull()
            & col("Course_Name").isNotNull()
        )
        .groupBy(
            "Course_ID",
            "Course_Name",
        )
        .agg(
            count("*").alias("learner_count"),

            spark_sum(
                when(
                    col("Completed") == 1,
                    1,
                ).otherwise(0)
            ).alias("completion_count"),

            spark_round(
                avg("Quiz_Score_Avg"),
                2,
            ).alias("avg_quiz_score"),

            spark_round(
                avg("Project_Grade"),
                2,
            ).alias("avg_project_grade"),

            spark_round(
                avg("Progress_Percentage"),
                2,
            ).alias("avg_progress"),

            spark_round(
                avg("Time_Spent_Hours"),
                2,
            ).alias("avg_study_time"),

            spark_round(
                avg("Video_Completion_Rate"),
                2,
            ).alias("avg_video_completion"),

            spark_round(
                avg("Average_Session_Duration_Min"),
                2,
            ).alias("avg_session_duration"),

            spark_round(
                avg("Login_Frequency"),
                2,
            ).alias("avg_login_frequency"),
        )
        .withColumn(
            "completion_rate",
            spark_round(
                col("completion_count")
                / col("learner_count")
                * 100,
                2,
            ),
        )
        .select(
            col("Course_ID").alias("course_id"),
            col("Course_Name").alias("course_name"),
            "learner_count",
            "completion_count",
            "completion_rate",
            "avg_quiz_score",
            "avg_project_grade",
            "avg_progress",
            "avg_study_time",
            "avg_video_completion",
            "avg_session_duration",
            "avg_login_frequency",
        )
        .orderBy(
            col("completion_rate").desc()
        )
    )

    print("课程维度核心指标统计结果：")

    course_core_statistics.show(
        100,
        truncate=False,
    )

    # ========================================================
    # 6. 写入 MySQL
    # ========================================================
    (
        course_core_statistics
        .coalesce(2)
        .write
        .jdbc(
            url=MYSQL_URL,
            table=MYSQL_TABLE,
            mode="overwrite",
            properties=MYSQL_PROPERTIES,
        )
    )

    print(
        f"写入成功：online_learning_db.{MYSQL_TABLE}"
    )

finally:
    spark.stop()
    print("SparkSession 已关闭")