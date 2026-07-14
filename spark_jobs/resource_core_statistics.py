from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    countDistinct,
    dense_rank,
    round as spark_round,
    sum as spark_sum,
)
from pyspark.sql.window import Window


# ============================================================
# 1. 基础配置
# ============================================================
SPARK_MASTER = "spark://192.168.75.129:7077"

# Windows 主机在 VMware 网络中的地址
WINDOWS_HOST = "192.168.75.1"

# HDFS 清洗数据
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

MYSQL_TABLE = "resource_core_statistics"

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
    .appName("ResourceCoreStatisticsToMySQL")
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
            "Login_Frequency",
            col("Login_Frequency").cast("double"),
        )
        .withColumn(
            "App_Usage_Percentage",
            col("App_Usage_Percentage").cast("double"),
        )
        .withColumn(
            "Video_Completion_Rate",
            col("Video_Completion_Rate").cast("double"),
        )
        .withColumn(
            "Rewatch_Count",
            col("Rewatch_Count").cast("long"),
        )
        .withColumn(
            "Notifications_Checked",
            col("Notifications_Checked").cast("double"),
        )
        .withColumn(
            "Reminder_Emails_Clicked",
            col("Reminder_Emails_Clicked").cast("double"),
        )
        .withColumn(
            "Time_Spent_Hours",
            col("Time_Spent_Hours").cast("double"),
        )
    )

    # ========================================================
    # 5. 资源维度核心指标计算
    #    当前将课程视为教学资源单元
    # ========================================================
    resource_core_statistics = (
        df
        .filter(
            col("Course_ID").isNotNull()
            & col("Course_Name").isNotNull()
        )
        .groupBy(
            "Course_ID",
            "Course_Name",
            "Category",
            "Course_Level",
        )
        .agg(
            countDistinct("Student_ID")
            .alias("learner_count"),

            spark_sum("Login_Frequency")
            .alias("access_volume"),

            spark_round(
                avg("App_Usage_Percentage"),
                2,
            ).alias("avg_usage_rate"),

            spark_round(
                avg("Video_Completion_Rate"),
                2,
            ).alias("avg_video_completion_rate"),

            spark_sum("Rewatch_Count")
            .alias("total_rewatch_count"),

            spark_round(
                avg("Notifications_Checked"),
                2,
            ).alias("avg_notifications_checked"),

            spark_round(
                avg("Reminder_Emails_Clicked"),
                2,
            ).alias("avg_reminder_clicks"),

            spark_round(
                avg("Time_Spent_Hours"),
                2,
            ).alias("avg_study_time_hours"),
        )
    )

    # ========================================================
    # 6. 按访问量生成排名
    # ========================================================
    rank_window = Window.orderBy(
        col("access_volume").desc()
    )

    resource_core_statistics = (
        resource_core_statistics
        .withColumn(
            "usage_rank",
            dense_rank().over(rank_window),
        )
        .select(
            col("Course_ID").alias("resource_id"),
            col("Course_Name").alias("resource_name"),
            col("Category").alias("resource_category"),
            col("Course_Level").alias("resource_level"),
            "learner_count",
            "access_volume",
            "avg_usage_rate",
            "avg_video_completion_rate",
            "total_rewatch_count",
            "avg_notifications_checked",
            "avg_reminder_clicks",
            "avg_study_time_hours",
            "usage_rank",
        )
        .orderBy("usage_rank")
    )

    print("资源维度核心指标统计结果：")

    resource_core_statistics.show(
        100,
        truncate=False,
    )

    # ========================================================
    # 7. 写入 MySQL
    # ========================================================
    (
        resource_core_statistics
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