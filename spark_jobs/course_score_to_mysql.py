from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    count,
    round as spark_round,
)


# ============================================================
# 1. 基础配置
# ============================================================
SPARK_MASTER = "spark://192.168.75.129:7077"

# Windows 主机在虚拟机网络中的地址
WINDOWS_HOST = "192.168.75.1"

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

MYSQL_TABLE = "course_score_statistics"

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
    .appName("CourseScoreToMySQL")
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
        "/home/huadi/opt/spark-4.1.2/jars/mysql-connector-j-8.3.0.jar",
    )
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("Spark 启动成功")
print("Spark Master：", spark.sparkContext.master)


# ============================================================
# 3. 从 HDFS 读取数据
# ============================================================
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


# ============================================================
# 4. 字段类型处理
# ============================================================
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
)


# ============================================================
# 5. 按课程统计平均分
# ============================================================
result = (
    df
    .filter(
        col("Course_ID").isNotNull()
        & col("Course_Name").isNotNull()
        & col("Quiz_Score_Avg").isNotNull()
    )
    .groupBy(
        "Course_ID",
        "Course_Name",
    )
    .agg(
        count("*").alias("student_count"),

        spark_round(
            avg("Quiz_Score_Avg"),
            2,
        ).alias("avg_quiz_score"),

        spark_round(
            avg("Project_Grade"),
            2,
        ).alias("avg_project_grade"),
    )
    .orderBy(
        col("avg_quiz_score").desc()
    )
)

print("统计结果：")
result.show(100, truncate=False)


# ============================================================
# 6. 写入 Windows 本地 MySQL
# ============================================================
(
    result
    .coalesce(2)
    .write
    .format("jdbc")
    .option("url", MYSQL_URL)
    .option("dbtable", MYSQL_TABLE)
    .option("user", MYSQL_PROPERTIES["user"])
    .option("password", MYSQL_PROPERTIES["password"])
    .option("driver", MYSQL_PROPERTIES["driver"])
    .option("batchsize", "1000")
    .mode("overwrite")
    .save()
)

print(
    f"统计结果已写入 MySQL 表："
    f"online_learning_db.{MYSQL_TABLE}"
)


# ============================================================
# 7. 关闭 Spark
# ============================================================
spark.stop()

print("SparkSession 已关闭")