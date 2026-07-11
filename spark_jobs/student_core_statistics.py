from pyspark.sql.functions import (
    avg,
    sum,
    countDistinct,
    round,
    col,
    when
)
from pyspark.sql import SparkSession
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

df = (
    df
    .withColumn(
        "Time_Spent_Hours",
        col("Time_Spent_Hours").cast("double")
    )
    .withColumn(
        "Quiz_Score_Avg",
        col("Quiz_Score_Avg").cast("double")
    )
    .withColumn(
        "Project_Grade",
        col("Project_Grade").cast("double")
    )
    .withColumn(
        "Progress_Percentage",
        col("Progress_Percentage").cast("double")
    )
    .withColumn(
        "Video_Completion_Rate",
        col("Video_Completion_Rate").cast("double")
    )
    .withColumn(
        "Average_Session_Duration_Min",
        col("Average_Session_Duration_Min").cast("double")
    )
    .withColumn(
        "Login_Frequency",
        col("Login_Frequency").cast("double")
    )
)
student_core_statistics = (
    df.groupBy("Student_ID")

      .agg(

        countDistinct("Course_ID")
            .alias("course_count"),

        round(
            sum("Time_Spent_Hours"),
            2
        ).alias("total_study_time"),

        sum(
            when(
                col("Completed")==1,
                1
            ).otherwise(0)
        ).alias("completed_course_count"),

        round(
            avg("Progress_Percentage"),
            2
        ).alias("avg_progress"),

        round(
            avg("Quiz_Score_Avg"),
            2
        ).alias("avg_quiz_score"),

        round(
            avg("Project_Grade"),
            2
        ).alias("avg_project_grade"),

        round(
            avg("Video_Completion_Rate"),
            2
        ).alias("avg_video_completion"),

        round(
            avg("Login_Frequency"),
            2
        ).alias("avg_login_frequency"),

        round(
            avg("Average_Session_Duration_Min"),
            2
        ).alias("avg_session_duration"),

        countDistinct("Enrollment_Date")
            .alias("study_days")

      )

      .withColumnRenamed(
          "Student_ID",
          "student_id"
      )

)
student_core_statistics.show(20, False)
student_core_statistics.write.jdbc(
    url=MYSQL_URL,
    table="student_core_statistics",
    mode="overwrite",
    properties=MYSQL_PROPERTIES
)
print("student_core_statistics 已成功写入 MySQL！")