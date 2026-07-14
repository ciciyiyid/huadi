from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    countDistinct,
    dense_rank,
)
from pyspark.sql.window import Window


# ============================================================
# 1. 基础配置
# ============================================================
SPARK_MASTER = "spark://192.168.75.129:7077"

# Windows 主机在 VMware NAT 网络中的地址
WINDOWS_HOST = "192.168.75.1"

# HDFS 中清洗后的在线学习数据
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

MYSQL_TABLE = "course_enrollment_ranking"

MYSQL_PROPERTIES = {
    "user": "online_app",
    "password": "Online@123456",
    "driver": "com.mysql.cj.jdbc.Driver",
}

# Windows Spark Driver 使用的 JDBC 驱动
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
    .appName("CourseEnrollmentRankingToMySQL")
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

    print("读取 HDFS 成功")
    print("数据总行数：", df.count())
    print("数据总列数：", len(df.columns))

    # ========================================================
    # 4. 过滤无效课程和学生记录
    # ========================================================
    valid_df = (
        df
        .filter(
            col("Course_ID").isNotNull()
            & (col("Course_ID") != "")
            & col("Course_Name").isNotNull()
            & (col("Course_Name") != "")
            & col("Student_ID").isNotNull()
            & (col("Student_ID") != "")
        )
    )

    print("有效数据行数：", valid_df.count())

    # ========================================================
    # 5. 按课程统计选课人数
    #
    # 使用 countDistinct(Student_ID)，避免同一学生在同一课程
    # 出现重复记录时被重复计数。
    # ========================================================
    course_enrollment_count = (
        valid_df
        .groupBy(
            "Course_ID",
            "Course_Name",
        )
        .agg(
            countDistinct("Student_ID")
            .alias("learner_count")
        )
    )

    # ========================================================
    # 6. 根据选课人数生成排名
    #
    # dense_rank：
    # 人数相同的课程排名相同，下一名不跳号。
    # 例如：1、2、2、3
    # ========================================================
    ranking_window = Window.orderBy(
        col("learner_count").desc(),
        col("Course_ID").asc(),
    )

    course_enrollment_ranking = (
        course_enrollment_count
        .withColumn(
            "enrollment_rank",
            dense_rank().over(
                Window.orderBy(
                    col("learner_count").desc()
                )
            ),
        )
        .select(
            "enrollment_rank",
            col("Course_ID").alias("course_id"),
            col("Course_Name").alias("course_name"),
            "learner_count",
        )
        .orderBy(
            col("enrollment_rank").asc(),
            col("course_id").asc(),
        )
    )

    # ========================================================
    # 7. 显示结果
    # ========================================================
    print("\n课程选课人数排行榜：")

    course_enrollment_ranking.show(
        100,
        truncate=False,
    )

    result_count = course_enrollment_ranking.count()

    print("课程数量：", result_count)

    if result_count == 0:
        raise RuntimeError("没有生成任何课程排名数据。")

    # ========================================================
    # 8. 写入 MySQL
    # ========================================================
    print(
        f"\n开始写入 MySQL 表："
        f"online_learning_db.{MYSQL_TABLE}"
    )

    (
        course_enrollment_ranking
        .coalesce(1)
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

    print("=" * 70)
    print("课程选课人数排行榜计算完成")
    print("写入记录数：", result_count)
    print("=" * 70)

finally:
    spark.stop()
    print("SparkSession 已关闭")