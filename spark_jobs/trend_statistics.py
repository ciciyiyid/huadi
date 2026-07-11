from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    concat_ws,
    count,
    countDistinct,
    lpad,
    round as spark_round,
    sum as spark_sum,
    to_date,
    weekofyear,
    year,
)


# ============================================================
# 1. 基础配置
# ============================================================
SPARK_MASTER = "spark://192.168.75.129:7077"

# Windows 主机在 VMware NAT 网络中的地址
WINDOWS_HOST = "192.168.75.1"

# HDFS 中的清洗后数据
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
    "&rewriteBatchedStatements=true"
)

DAILY_TABLE = "daily_learning_statistics"
WEEKLY_TABLE = "weekly_learning_statistics"

MYSQL_PROPERTIES = {
    "user": "online_app",
    "password": "Online@123456",
    "driver": "com.mysql.cj.jdbc.Driver",
}

# Windows Driver 使用的 JDBC 驱动
WINDOWS_JDBC_JAR = (
    r"E:\huadifinalproject\lib\mysql-connector-j-8.3.0.jar"
)

# 虚拟机 Spark Executor 使用的 JDBC 驱动
LINUX_JDBC_JAR = (
    "/home/huadi/opt/spark-4.1.2/jars/"
    "mysql-connector-j-8.3.0.jar"
)


# ============================================================
# 2. 创建 SparkSession
# ============================================================
spark = (
    SparkSession.builder
    .appName("LearningTrendStatisticsToMySQL")
    .master(SPARK_MASTER)
    .config("spark.driver.host", WINDOWS_HOST)
    .config("spark.driver.bindAddress", WINDOWS_HOST)
    .config("spark.jars", WINDOWS_JDBC_JAR)
    .config("spark.driver.extraClassPath", WINDOWS_JDBC_JAR)
    .config("spark.executor.extraClassPath", LINUX_JDBC_JAR)
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("=" * 70)
print("Spark 启动成功")
print("Spark Master：", spark.sparkContext.master)
print("=" * 70)


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

    source_row_count = df.count()

    print("读取 HDFS 成功")
    print("原始数据行数：", source_row_count)
    print("原始数据列数：", len(df.columns))

    # ========================================================
    # 4. 字段类型转换与基础过滤
    # ========================================================
    df = (
        df
        .withColumn(
            "Enrollment_Date",
            to_date(col("Enrollment_Date"), "yyyy-MM-dd"),
        )
        .withColumn(
            "Time_Spent_Hours",
            col("Time_Spent_Hours").cast("double"),
        )
        .withColumn(
            "Progress_Percentage",
            col("Progress_Percentage").cast("double"),
        )
        .withColumn(
            "Quiz_Score_Avg",
            col("Quiz_Score_Avg").cast("double"),
        )
        .withColumn(
            "Average_Session_Duration_Min",
            col("Average_Session_Duration_Min").cast("double"),
        )
        .filter(
            col("Enrollment_Date").isNotNull()
            & col("Student_ID").isNotNull()
            & col("Course_ID").isNotNull()
            & col("Time_Spent_Hours").isNotNull()
        )
    )

    valid_row_count = df.count()

    print("有效趋势统计数据行数：", valid_row_count)
    print("日期为空或关键字段异常的记录已过滤：",
          source_row_count - valid_row_count)

    # 缓存，避免日统计和周统计重复读取 HDFS
    df = df.cache()

    # ========================================================
    # 5. 按天计算趋势指标
    # ========================================================
    daily_statistics = (
        df
        .groupBy("Enrollment_Date")
        .agg(
            # 学习人次：当天所有学生-课程记录数
            count("*").alias("learning_times"),

            # 去重后的学生人数
            countDistinct("Student_ID").alias("learner_count"),

            # 当天涉及课程数量
            countDistinct("Course_ID").alias("course_count"),

            # 总学习时长
            spark_round(
                spark_sum("Time_Spent_Hours"),
                2,
            ).alias("total_study_time_hours"),

            # 人均/记录平均学习时长
            spark_round(
                avg("Time_Spent_Hours"),
                2,
            ).alias("avg_study_time_hours"),

            spark_round(
                avg("Average_Session_Duration_Min"),
                2,
            ).alias("avg_session_duration_min"),

            spark_round(
                avg("Progress_Percentage"),
                2,
            ).alias("avg_progress_percentage"),

            spark_round(
                avg("Quiz_Score_Avg"),
                2,
            ).alias("avg_quiz_score"),
        )
        .select(
            col("Enrollment_Date").alias("stat_date"),
            "learning_times",
            "learner_count",
            "course_count",
            "total_study_time_hours",
            "avg_study_time_hours",
            "avg_session_duration_min",
            "avg_progress_percentage",
            "avg_quiz_score",
        )
        .orderBy("stat_date")
    )

    print("\n按天学习趋势：")

    daily_statistics.show(
        30,
        truncate=False,
    )

    # ========================================================
    # 6. 按周计算趋势指标
    # ========================================================
    weekly_source = (
        df
        .withColumn(
            "stat_year",
            year(col("Enrollment_Date")),
        )
        .withColumn(
            "stat_week",
            weekofyear(col("Enrollment_Date")),
        )
    )

    weekly_statistics = (
        weekly_source
        .groupBy(
            "stat_year",
            "stat_week",
        )
        .agg(
            count("*").alias("learning_times"),

            countDistinct("Student_ID").alias("learner_count"),

            countDistinct("Course_ID").alias("course_count"),

            spark_round(
                spark_sum("Time_Spent_Hours"),
                2,
            ).alias("total_study_time_hours"),

            spark_round(
                avg("Time_Spent_Hours"),
                2,
            ).alias("avg_study_time_hours"),

            spark_round(
                avg("Average_Session_Duration_Min"),
                2,
            ).alias("avg_session_duration_min"),

            spark_round(
                avg("Progress_Percentage"),
                2,
            ).alias("avg_progress_percentage"),

            spark_round(
                avg("Quiz_Score_Avg"),
                2,
            ).alias("avg_quiz_score"),
        )
        .withColumn(
            "week_label",
            concat_ws(
                "-W",
                col("stat_year").cast("string"),
                lpad(
                    col("stat_week").cast("string"),
                    2,
                    "0",
                ),
            ),
        )
        .select(
            "stat_year",
            "stat_week",
            "week_label",
            "learning_times",
            "learner_count",
            "course_count",
            "total_study_time_hours",
            "avg_study_time_hours",
            "avg_session_duration_min",
            "avg_progress_percentage",
            "avg_quiz_score",
        )
        .orderBy(
            "stat_year",
            "stat_week",
        )
    )

    print("\n按周学习趋势：")

    weekly_statistics.show(
        30,
        truncate=False,
    )

    # ========================================================
    # 7. 写入 MySQL：按天统计表
    # ========================================================
    print("\n开始写入 MySQL 日趋势表……")

    (
        daily_statistics
        .coalesce(2)
        .write
        .jdbc(
            url=MYSQL_URL,
            table=DAILY_TABLE,
            mode="overwrite",
            properties=MYSQL_PROPERTIES,
        )
    )

    print(
        f"写入成功：online_learning_db.{DAILY_TABLE}"
    )

    # ========================================================
    # 8. 写入 MySQL：按周统计表
    # ========================================================
    print("\n开始写入 MySQL 周趋势表……")

    (
        weekly_statistics
        .coalesce(2)
        .write
        .jdbc(
            url=MYSQL_URL,
            table=WEEKLY_TABLE,
            mode="overwrite",
            properties=MYSQL_PROPERTIES,
        )
    )

    print(
        f"写入成功：online_learning_db.{WEEKLY_TABLE}"
    )

    # ========================================================
    # 9. 结果校验
    # ========================================================
    daily_count = daily_statistics.count()
    weekly_count = weekly_statistics.count()

    print("\n" + "=" * 70)
    print("趋势指标计算完成")
    print("日趋势记录数：", daily_count)
    print("周趋势记录数：", weekly_count)
    print("MySQL 日表：", DAILY_TABLE)
    print("MySQL 周表：", WEEKLY_TABLE)
    print("=" * 70)

finally:
    try:
        df.unpersist()
    except NameError:
        pass

    spark.stop()
    print("SparkSession 已关闭")