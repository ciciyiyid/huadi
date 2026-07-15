# -*- coding: utf-8 -*-
"""
在线教学学生画像+教师画像+学情预警
"""

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.functions import col, when, lit, count, avg, round, sum
from pyspark.ml.feature import VectorAssembler, MinMaxScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
import os
import shutil
import pandas as pd

# ====================== 配置 ======================
MYSQL_URL = "jdbc:mysql://localhost:3306/online_learning_db?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true"
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
MYSQL_DRIVER = "com.mysql.cj.jdbc.Driver"

# 统一输出目录
OUTPUT_DIR = "D:/aaa/A_HD/project/data/localstorage/analysis/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 预警阈值配置
LOGIN_FREQ_RED = 4
ASSIGN_SUBMIT_RED = 50
PROGRESS_RED = 30
VIDEO_COMPLETION_RED = 40
QUIZ_SCORE_RED = 55
DAYS_SINCE_RED = 10
MISS_ASSIGN_RED = 4

# ====================== 初始化Spark ======================
spark = SparkSession.builder \
    .appName('Online_Edu_Profile_Warning_Local') \
    .master('local[1]') \
    .config("spark.jars", "D:\spark_jars\mysql-connector-j-9.7.0/mysql-connector-j-9.7.0.jar") \
    .config("spark.hadoop.io.nativeio.enabled", "false") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# ====================== 工具函数 =========================
def read_mysql(table_name):
    return spark.read.format("jdbc") \
        .option("url", MYSQL_URL) \
        .option("dbtable", table_name) \
        .option("user", MYSQL_USER) \
        .option("password", MYSQL_PASSWORD) \
        .option("driver", MYSQL_DRIVER) \
        .load()

def save_single_csv(df, csv_path):
    temp_dir = csv_path + "_temp"
    df.coalesce(1).write.option("header", "true").option("encoding", "utf-8").mode("overwrite").csv(temp_dir)
    for filename in os.listdir(temp_dir):
        if filename.startswith("part-") and filename.endswith(".csv"):
            part_file = os.path.join(temp_dir, filename)
            if os.path.exists(csv_path):
                os.remove(csv_path)
            shutil.move(part_file, csv_path)
            break
    shutil.rmtree(temp_dir)

def generate_insert_sql(df, table_name, sql_path):
    pdf = df.toPandas()
    columns = pdf.columns.tolist()
    batch_size = 1000

    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write(f"-- =============================================\n")
        f.write(f"-- 表名：{table_name}\n")
        f.write(f"-- 数据量：{len(pdf)} 条\n")
        f.write(f"-- =============================================\n\n")
        
        f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
        create_cols = []
        for col_name in columns:
            if pdf[col_name].dtype in ['int64', 'float64']:
                create_cols.append(f"`{col_name}` DOUBLE")
            else:
                create_cols.append(f"`{col_name}` TEXT")
        f.write(f"CREATE TABLE `{table_name}` (\n    " + ",\n    ".join(create_cols) + "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n\n")

        for i in range(0, len(pdf), batch_size):
            batch = pdf.iloc[i:i+batch_size]
            values_list = []
            for _, row in batch.iterrows():
                row_values = []
                for col_name in columns:
                    val = row[col_name]
                    if pd.isna(val):
                        row_values.append("NULL")
                    elif isinstance(val, (int, float)):
                        row_values.append(str(val))
                    else:
                        val_str = str(val).replace("'", "''")
                        row_values.append(f"'{val_str}'")
                values_list.append(f"({', '.join(row_values)})")
            f.write(f"INSERT INTO `{table_name}` ({', '.join([f'`{c}`' for c in columns])}) VALUES\n")
            f.write(",\n".join(values_list) + ";\n\n")

def merge_all_sql(sql_file_list, output_sql_path):
    with open(output_sql_path, 'w', encoding='utf-8') as out_f:
        out_f.write("-- =============================================\n")
        out_f.write("-- 在线教学画像与预警分析结果总SQL文件\n")
        out_f.write("-- 包含全部8张结果表：建表+全量数据\n")
        out_f.write("-- 导入方式：mysql -u root -p 数据库名 < 本文件\n")
        out_f.write("-- =============================================\n\n")
        out_f.write("SET NAMES utf8mb4;\n")
        out_f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
        
        for sql_file in sql_file_list:
            with open(sql_file, 'r', encoding='utf-8') as in_f:
                out_f.write(in_f.read())
                out_f.write("\n")
        
        out_f.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")
    print(f"✅ 已生成总SQL文件：{output_sql_path}")

# ====================== 模块0：读取源数据与宽表构造 ======================
df_student_stat = read_mysql("student_stat")
df_student_info = read_mysql("student_info")
df_student_feature = read_mysql("student_feature")
df_course_info = read_mysql("course_info")

df_student_miss = df_student_feature.select(
    F.col("student_id"),
    F.col("total_assignments_missed"),
    F.col("course_count"),
    (F.col("total_assignments_missed") / F.col("course_count")).alias("avg_miss_per_course")
)

df_all = df_student_stat.alias("ss") \
    .join(df_course_info.alias("ci"), F.col("ss.course_id") == F.col("ci.course_id"), "left") \
    .join(df_student_info.alias("si"), F.col("ss.student_id") == F.col("si.student_id"), "left") \
    .join(df_student_miss.alias("sm"), F.col("ss.student_id") == F.col("sm.student_id"), "left") \
    .select(
        F.col("ss.student_id").alias("Student_ID"),
        F.col("ss.course_id").alias("Course_ID"),
        F.col("ci.course_name").alias("Course_Name"),
        F.col("ss.total_study_time_hours").alias("Time_Spent_Hours"),
        F.col("ss.avg_session_duration_min").alias("Average_Session_Duration_Min"),
        F.lit(0).alias("Rewatch_Count"),
        F.col("ss.video_completion_rate").alias("Video_Completion_Rate"),
        F.col("ss.quiz_score_avg").alias("Quiz_Score_Avg"),
        F.col("ss.course_progress_rate").alias("Progress_Percentage"),
        F.col("ss.project_grade").alias("Project_Grade"),
        F.col("ss.discussion_participation").alias("Discussion_Participation"),
        F.col("ss.peer_interaction_score").alias("Peer_Interaction_Score"),
        F.lit(0).alias("Assignments_Submitted"),
        F.coalesce(F.col("sm.avg_miss_per_course"), F.lit(0)).alias("Assignments_Missed"),
        F.col("ss.assignment_submit_rate").alias("Assignment_Submission_Rate"),
        F.col("ss.login_frequency").alias("Login_Frequency"),
        F.col("ss.days_since_last_login").alias("Days_Since_Last_Login"),
        F.col("ss.course_completed").alias("Completed"),
        F.col("si.gender").alias("Gender"),
        F.col("si.age").alias("Age"),
        F.col("si.education_level").alias("Education_Level"),
        F.col("si.employment_status").alias("Employment_Status"),
        F.col("si.device_type").alias("Device_Type"),
        F.col("si.internet_connection_quality").alias("Internet_Connection_Quality"),
        F.col("ci.instructor_rating").alias("Instructor_Rating"),
        F.col("ss.satisfaction_rating").alias("Satisfaction_Rating"),
        F.lit(0).alias("Support_Tickets_Raised"),
        F.col("ci.course_level").alias("Course_Level"),
        F.col("ci.category").alias("Category")
    )
df_all = df_all.fillna(0)

# ====================== 模块1：学生画像K-Means聚类 ======================
df_student_attr = df_all.select(
    "Student_ID", "Gender", "Age", "Education_Level",
    "Employment_Status", "Device_Type", "Internet_Connection_Quality"
).dropDuplicates(["Student_ID"])

df_student_raw = df_all.groupBy("Student_ID").agg(
    F.sum("Time_Spent_Hours").alias("total_duration"),
    F.countDistinct("Course_ID").alias("course_count"),
    F.avg("Average_Session_Duration_Min").alias("avg_session"),
    F.sum("Rewatch_Count").alias("total_rewatch"),
    F.avg("Video_Completion_Rate").alias("avg_completion_rate"),
    F.avg("Quiz_Score_Avg").alias("avg_quiz_score"),
    F.avg("Progress_Percentage").alias("avg_progress"),
    F.avg("Project_Grade").alias("avg_project_grade"),
    F.avg("Discussion_Participation").alias("avg_discuss"),
    F.avg("Peer_Interaction_Score").alias("peer_interaction"),
    F.sum("Assignments_Submitted").alias("total_submit"),
    F.sum("Assignments_Missed").alias("total_miss"),
    F.avg("Login_Frequency").alias("login_freq"),
    F.avg("Days_Since_Last_Login").alias("avg_days_since_login")
)

df_student_filter = df_student_raw.filter("total_duration > 0.1 AND total_duration < 200") \
       .filter("course_count >= 1") \
       .filter("avg_completion_rate BETWEEN 0 AND 100") \
       .filter("avg_quiz_score BETWEEN 0 AND 100") \
       .filter("avg_progress BETWEEN 0 AND 100")
print(f"有效学生样本数：{df_student_filter.count()}")

# 特征工程
feature_cols = ["avg_completion_rate", "avg_quiz_score", "avg_progress", "total_duration", "total_miss", "login_freq"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw")
df_vector = assembler.transform(df_student_filter)
scaler = MinMaxScaler(inputCol="features_raw", outputCol="features")
scaler_model = scaler.fit(df_vector)
df_scaled = scaler_model.transform(df_vector)

# K-Means聚类
final_k = 3
kmeans_final = KMeans(featuresCol='features', k=final_k, seed=2024)
model_final = kmeans_final.fit(df_scaled)
df_cluster = model_final.transform(df_scaled).withColumnRenamed("prediction", "cluster_id")

# 验证
print("\n" + "="*50)
print("【模型验证】K-Means聚类模型效果验证")
print("="*50)

sse = model_final.summary.trainingCost
print(f"1. 簇内平方和 SSE：{sse:.2f}")

evaluator = ClusteringEvaluator(featuresCol='features', predictionCol='cluster_id', metricName='silhouette', distanceMeasure='squaredEuclidean')
silhouette_score = evaluator.evaluate(df_cluster)
print(f"\n2. 轮廓系数 Silhouette Score：{silhouette_score:.4f}")
if silhouette_score > 0.5:
    print("   结论：聚类效果优秀，簇间区分度强")
elif silhouette_score > 0.2:
    print("   结论：聚类效果可接受，存在一定簇间重叠")
else:
    print("   结论：聚类效果较差")

print("\n3. 多K值SSE对比（肘部法则参考）：")
k_candidates = [2, 3, 4, 5, 6, 7]
sse_list = []
for k in k_candidates:
    model_temp = KMeans(featuresCol='features', k=k, seed=2024).fit(df_scaled)
    sse_temp = model_temp.summary.trainingCost
    sse_list.append(sse_temp)
    print(f"   k={k:2d}  SSE = {sse_temp:.2f}")

print("\n   相邻K值SSE下降幅度：")
for i in range(1, len(k_candidates)):
    drop = sse_list[i-1] - sse_list[i]
    drop_rate = drop / sse_list[i-1] * 100
    print(f"   k={k_candidates[i-1]}→k={k_candidates[i]}：下降 {drop:.2f}（{drop_rate:.2f}%）")

cluster_biz_stats = df_cluster.groupBy("cluster_id").agg(
    F.avg("avg_quiz_score").alias("mean_quiz"),
    F.avg("avg_completion_rate").alias("mean_completion"),
    F.avg("avg_progress").alias("mean_progress"),
    F.avg("total_duration").alias("mean_duration"),
    F.avg("total_miss").alias("mean_miss")
).collect()

quiz_means = [float(row["mean_quiz"]) for row in cluster_biz_stats]
completion_means = [float(row["mean_completion"]) for row in cluster_biz_stats]
progress_means = [float(row["mean_progress"]) for row in cluster_biz_stats]
duration_means = [float(row["mean_duration"]) for row in cluster_biz_stats]
miss_means = [float(row["mean_miss"]) for row in cluster_biz_stats]

completion_gap = max(completion_means) - min(completion_means)
quiz_gap = max(quiz_means) - min(quiz_means)
progress_gap = max(progress_means) - min(progress_means)
duration_gap = max(duration_means) - min(duration_means)
miss_gap = max(miss_means) - min(miss_means)

print(f"\n4. 簇间业务区分度综合校验：")
print("──────────────────────────────────")
print(f"完课率极差：{completion_gap:.2f} %  {'✅ 强区分' if completion_gap > 20 else '⚠️ 中区分' if completion_gap > 10 else '❌ 弱区分'}")
print(f"平均分极差：{quiz_gap:.2f} 分  {'✅ 强区分' if quiz_gap > 10 else '⚠️ 中区分' if quiz_gap > 5 else '❌ 弱区分'}")
print(f"学习进度极差：{progress_gap:.2f} %  {'✅ 强区分' if progress_gap > 15 else '⚠️ 中区分' if progress_gap > 8 else '❌ 弱区分'}")
print(f"学习时长极差：{duration_gap:.2f} 小时  {'✅ 强区分' if duration_gap > 1 else '⚠️ 中区分' if duration_gap > 0.5 else '❌ 弱区分'}")
print(f"漏交作业极差：{miss_gap:.2f} 次  {'✅ 强区分' if miss_gap > 2 else '⚠️ 中区分' if miss_gap > 1 else '❌ 弱区分'}")
print("──────────────────────────────────")

# 统计强区分指标数量
strong_count = 0
if completion_gap > 20: strong_count += 1
if quiz_gap > 10: strong_count += 1
if progress_gap > 15: strong_count += 1
if duration_gap > 1: strong_count += 1
if miss_gap > 2: strong_count += 1

if strong_count >= 3:
    print("综合结论：✅ 核心行为指标区分显著")
elif strong_count >= 2:
    print("综合结论：⚠️ 部分核心指标区分度可接受")
else:
    print("综合结论：❌ 整体区分度不足")

# 簇标签映射
cluster_stats = df_cluster.groupBy("cluster_id").agg(
    F.count("Student_ID").alias("student_count"),
    F.round(F.avg("total_duration"), 2).alias("avg_total_duration"),
    F.round(F.avg("avg_completion_rate"), 2).alias("avg_completion_rate"),
    F.round(F.avg("avg_quiz_score"), 2).alias("avg_quiz_score"),
    F.round(F.avg("avg_progress"), 2).alias("avg_progress"),
    F.round(F.avg("avg_discuss"), 2).alias("avg_discuss"),
    F.round(F.avg("total_miss"), 2).alias("avg_miss")
)
cluster_stats_pd = cluster_stats.toPandas()
convert_cols = ["avg_quiz_score", "avg_total_duration", "avg_completion_rate", "avg_discuss", "avg_miss", "avg_progress"]
for c in convert_cols:
    cluster_stats_pd[c] = cluster_stats_pd[c].astype(float)

cluster_stats_pd["composite_score"] = (
    cluster_stats_pd["avg_quiz_score"] * 0.35 +
    cluster_stats_pd["avg_completion_rate"] * 0.25 +
    cluster_stats_pd["avg_progress"] * 0.15 +
    cluster_stats_pd["avg_total_duration"] * 0.15
) - cluster_stats_pd["avg_miss"] * 0.1

cluster_stats_pd = cluster_stats_pd.sort_values("composite_score", ascending=False).reset_index(drop=True)
label_map = {0: "自律学霸", 1: "普通中等", 2: "有待提升"}
cluster_label_dict = {}
for idx, row in cluster_stats_pd.iterrows():
    cluster_label_dict[int(row["cluster_id"])] = label_map.get(idx, f"分组{idx+1}")
print("学生簇标签映射：", cluster_label_dict)

label_map_expr = F.create_map(*[F.lit(item) for pair in cluster_label_dict.items() for item in pair])
df_student_cluster = df_cluster.withColumn("人群标签", label_map_expr[F.col("cluster_id")])
df_student_final = df_student_cluster.join(df_student_attr, on="Student_ID", how="left")

# 输出
student_detail_cols = [
    "Student_ID", "人群标签", "total_duration", "course_count", "avg_session",
    "avg_completion_rate", "avg_quiz_score", "avg_progress", "avg_project_grade",
    "avg_discuss", "peer_interaction", "total_submit", "total_miss",
    "login_freq", "avg_days_since_login", "Gender", "Age", "Education_Level",
    "Employment_Status", "Device_Type", "Internet_Connection_Quality"
]
df_student_detail_out = df_student_final.select(student_detail_cols)
s1_csv = os.path.join(OUTPUT_DIR, "student_profile_detail.csv")
s1_sql = os.path.join(OUTPUT_DIR, "student_profile_detail.sql")
save_single_csv(df_student_detail_out, s1_csv)
generate_insert_sql(df_student_detail_out, "student_profile_detail", s1_sql)

total_student = df_student_final.count()
df_student_summary = df_student_final.groupBy("人群标签").agg(
    F.count("Student_ID").alias("student_count"),
    F.round(F.count("Student_ID") / total_student * 100, 2).alias("ratio_percent"),
    F.round(F.avg("total_duration"), 2).alias("avg_total_duration"),
    F.round(F.avg("avg_completion_rate"), 2).alias("avg_completion_rate"),
    F.round(F.avg("avg_quiz_score"), 2).alias("avg_quiz_score"),
    F.round(F.avg("Age"), 1).alias("avg_age"),
    F.round(F.sum(F.when(F.col("Gender")=="Male",1)) / F.count("*")*100,2).alias("male_ratio"),
    F.round(F.sum(F.when(F.col("Education_Level")=="Bachelor",1)) / F.count("*")*100,2).alias("bachelor_ratio")
).orderBy(F.col("ratio_percent").desc())

s2_csv = os.path.join(OUTPUT_DIR, "student_profile_summary.csv")
s2_sql = os.path.join(OUTPUT_DIR, "student_profile_summary.sql")
save_single_csv(df_student_summary, s2_csv)
generate_insert_sql(df_student_summary, "student_profile_summary", s2_sql)

print("\n【学生画像统计预览】")
df_student_summary.show()

# ====================== 模块2：教师教学效能画像 ======================
df_teacher_base = df_all.groupBy('Course_ID', 'Course_Name').agg(
    F.round(F.mean('Instructor_Rating'), 2).alias('avg_instructor_rating'),
    F.round(F.stddev('Instructor_Rating'), 2).alias('rating_std'),
    F.round(F.mean('Satisfaction_Rating'), 2).alias('avg_student_satisfaction'),
    F.round(F.mean('Video_Completion_Rate'), 2).alias('avg_video_completion'),
    F.round(F.mean('Progress_Percentage'), 2).alias('avg_student_progress'),
    F.round(F.mean('Completed'), 4).alias('course_finish_rate'),
    F.round(F.mean('Quiz_Score_Avg'), 2).alias('avg_quiz_score'),
    F.round(F.mean('Discussion_Participation'), 2).alias('avg_discussion_participation'),
    F.round(F.mean('Assignment_Submission_Rate'), 4).alias('avg_assignment_submit_rate'),
    F.round(F.mean('Support_Tickets_Raised'), 2).alias('avg_support_tickets'),
    F.countDistinct('Student_ID').alias('total_student_count')
)

df_course_attr = df_all.select('Course_ID', 'Course_Level', 'Category').dropDuplicates(["Course_ID"]) \
    .select('Course_ID', F.col('Course_Level').alias('course_level'), F.col('Category').alias('course_category'))
df_teacher_full = df_teacher_base.join(df_course_attr, on="Course_ID", how="left").fillna({"course_level": "未知"})

df_teacher_score = df_teacher_full.withColumn(
    "teaching_effect_score_raw",
    F.col("avg_instructor_rating") * 10 * 0.2 +
    F.col("avg_student_satisfaction") * 10 * 0.2 +
    F.col("avg_video_completion") * 0.05 +
    F.col("course_finish_rate") * 100 * 0.15 +
    F.col("avg_discussion_participation") * 5 * 0.1 +
    F.col("avg_assignment_submit_rate") * 100 * 0.1 +
    F.log(F.col("total_student_count")) * 2 * 0.2
)

score_min_max = df_teacher_score.agg(F.min("teaching_effect_score_raw"), F.max("teaching_effect_score_raw")).collect()[0]
score_min, score_max = score_min_max[0], score_min_max[1]
if score_max == score_min: score_max = score_min + 1e-6
df_teacher_score = df_teacher_score.withColumn(
    "teaching_effect_score",
    F.round((F.col("teaching_effect_score_raw") - score_min) / (score_max - score_min) * 100, 2)
)

rank_window = Window.orderBy(F.col("teaching_effect_score").desc())
df_teacher_ranked = df_teacher_score.withColumn("score_percent_rank", F.percent_rank().over(rank_window))
df_teacher_final = df_teacher_ranked.withColumn('教学效能评级',
    F.when(F.col("score_percent_rank") <= 0.3, '标杆引领型')
     .when(F.col("score_percent_rank") <= 0.7, '稳健深耕型')
     .otherwise('潜力成长型')
)

# 输出CSV+SQL
teacher_detail_cols = [
    'Course_ID', 'Course_Name', '教学效能评级', 'teaching_effect_score',
    'avg_instructor_rating', 'avg_student_satisfaction', 'avg_video_completion',
    'avg_student_progress', 'course_finish_rate', 'avg_quiz_score',
    'avg_discussion_participation', 'avg_assignment_submit_rate', 'avg_support_tickets',
    'total_student_count', 'course_level', 'course_category'
]
df_teacher_detail_out = df_teacher_final.select(teacher_detail_cols)
t1_csv = os.path.join(OUTPUT_DIR, "teacher_profile_detail.csv")
t1_sql = os.path.join(OUTPUT_DIR, "teacher_profile_detail.sql")
save_single_csv(df_teacher_detail_out, t1_csv)
generate_insert_sql(df_teacher_detail_out, "teacher_profile_detail", t1_sql)

total_course = df_teacher_final.count()
df_teacher_summary = df_teacher_final.groupBy("教学效能评级").agg(
    F.count("*").alias("course_count"),
    F.round(F.count("*") / total_course * 100, 2).alias("ratio_percent"),
    F.round(F.avg('teaching_effect_score'), 2).alias('avg_effect_score'),
    F.round(F.avg('avg_instructor_rating'), 2).alias('avg_instructor_rating'),
    F.round(F.avg('avg_video_completion'), 2).alias('avg_video_completion'),
    F.round(F.avg('total_student_count'), 2).alias('avg_student_count')
).orderBy(F.col("ratio_percent").desc())

t2_csv = os.path.join(OUTPUT_DIR, "teacher_profile_summary.csv")
t2_sql = os.path.join(OUTPUT_DIR, "teacher_profile_summary.sql")
save_single_csv(df_teacher_summary, t2_csv)
generate_insert_sql(df_teacher_summary, "teacher_profile_summary", t2_sql)

print("\n【教师画像统计预览】")
df_teacher_summary.show(truncate=False)

# ====================== 模块3：学情预警系统 ======================
df_student_raw = df_all.fillna({
    "Login_Frequency": 0, "Assignment_Submission_Rate": 0, "Average_Session_Duration_Min": 0,
    "Progress_Percentage": 0, "Video_Completion_Rate": 0, "Quiz_Score_Avg": 0,
    "Days_Since_Last_Login": 0, "Assignments_Missed": 0, "Discussion_Participation": 0
})

df_student_filter = df_student_raw.filter("Time_Spent_Hours > 0.1 AND Time_Spent_Hours < 200") \
       .filter("Video_Completion_Rate BETWEEN 0 AND 100") \
       .filter("Quiz_Score_Avg BETWEEN 0 AND 100") \
       .filter("Progress_Percentage BETWEEN 0 AND 100")
total_valid = df_student_filter.count()
df_clean = df_student_filter

df_risk_tag = df_clean \
    .withColumn("is_login_risk", when((col("Login_Frequency") < lit(LOGIN_FREQ_RED)) | (col("Days_Since_Last_Login") > lit(DAYS_SINCE_RED)), lit(1)).otherwise(lit(0))) \
    .withColumn("is_homework_risk", when((col("Assignment_Submission_Rate") < lit(ASSIGN_SUBMIT_RED)) | (col("Assignments_Missed") > lit(MISS_ASSIGN_RED)), lit(1)).otherwise(lit(0))) \
    .withColumn("is_progress_risk", when((col("Progress_Percentage") < lit(PROGRESS_RED)) & (col("Video_Completion_Rate") < lit(VIDEO_COMPLETION_RED)), lit(1)).otherwise(lit(0))) \
    .withColumn("is_score_risk", when(col("Quiz_Score_Avg") < lit(QUIZ_SCORE_RED), lit(1)).otherwise(lit(0)))

df_sum = df_risk_tag.withColumn("risk_sum", col("is_login_risk") + col("is_homework_risk") + col("is_progress_risk") + col("is_score_risk"))
df_warning = df_sum.withColumn("warning_level",
    when(col("risk_sum") >= 3, "高风险")
    .when(col("risk_sum") == 2, "中风险")
    .when(col("risk_sum") == 1, "低风险")
    .otherwise("安全")
)

df_all_student = df_warning.select(
    "Student_ID", "Course_ID", "Course_Name", "warning_level", "risk_sum",
    "Quiz_Score_Avg", "Login_Frequency", "Days_Since_Last_Login",
    "Assignment_Submission_Rate", "Assignments_Missed",
    "Progress_Percentage", "Video_Completion_Rate",
    "is_login_risk", "is_homework_risk", "is_progress_risk", "is_score_risk"
).dropDuplicates(["Student_ID"])

df_full_summary = df_warning.groupBy("warning_level").agg(
    count("Student_ID").alias("student_count"),
    round(avg("Quiz_Score_Avg"), 2).alias("avg_score"),
    round(avg("Assignment_Submission_Rate"), 2).alias("avg_submit_rate"),
    round(avg("Progress_Percentage"), 2).alias("avg_progress")
).withColumn("risk_ratio_pct", round(col("student_count") / lit(total_valid) * 100, 2))

# 验证
print("\n" + "="*50)
print("【模型验证】学情预警规则模型逻辑校验")
print("="*50)

df_risk_sorted = df_full_summary.orderBy(
    F.when(F.col("warning_level") == "安全", 1)
     .when(F.col("warning_level") == "低风险", 2)
     .when(F.col("warning_level") == "中风险", 3)
     .when(F.col("warning_level") == "高风险", 4)
)
risk_rows = df_risk_sorted.collect()

def check_monotonic(rows, col_name):
    values = [float(row[col_name]) for row in rows]
    return all(values[i] >= values[i+1] for i in range(len(values)-1)), values

score_ok, score_vals = check_monotonic(risk_rows, "avg_score")
submit_ok, submit_vals = check_monotonic(risk_rows, "avg_submit_rate")
progress_ok, progress_vals = check_monotonic(risk_rows, "avg_progress")

print(f"1. 平均分 风险递减校验：{'✅ 通过' if score_ok else '❌ 不通过'}")
print(f"   各等级值：安全({score_vals[0]}) → 低风险({score_vals[1]}) → 中风险({score_vals[2]}) → 高风险({score_vals[3]})")
print(f"\n2. 作业提交率 风险递减校验：{'✅ 通过' if submit_ok else '❌ 不通过'}")
print(f"   各等级值：安全({submit_vals[0]}) → 低风险({submit_vals[1]}) → 中风险({submit_vals[2]}) → 高风险({submit_vals[3]})")
print(f"\n3. 学习进度 风险递减校验：{'✅ 通过' if progress_ok else '❌ 不通过'}")
print(f"   各等级值：安全({progress_vals[0]}) → 低风险({progress_vals[1]}) → 中风险({progress_vals[2]}) → 高风险({progress_vals[3]})")
all_pass = score_ok and submit_ok and progress_ok
print(f"\n结论：{'✅ 预警规则逻辑自洽，分级合理' if all_pass else '⚠️ 部分指标单调性异常，建议调整阈值'}")

# 输出CSV+SQL
w1_csv = os.path.join(OUTPUT_DIR, "student_warning_detail.csv")
w1_sql = os.path.join(OUTPUT_DIR, "student_warning_detail.sql")
save_single_csv(df_all_student, w1_csv)
generate_insert_sql(df_all_student, "student_warning_detail", w1_sql)

w2_csv = os.path.join(OUTPUT_DIR, "warning_level_summary.csv")
w2_sql = os.path.join(OUTPUT_DIR, "warning_level_summary.sql")
save_single_csv(df_full_summary, w2_csv)
generate_insert_sql(df_full_summary, "warning_level_summary", w2_sql)

print("\n【预警等级汇总】")
df_full_summary.show(truncate=False)

# ====================== 分维度评估：输出CSV+SQL ======================
# 分课程风险
df_course_risk = df_warning.groupBy("Course_ID", "Course_Name").agg(
    count("Student_ID").alias("student_count"),
    sum(when(col("warning_level") == "高风险", 1).otherwise(0)).alias("high_risk_count"),
    sum(when(col("warning_level") == "中风险", 1).otherwise(0)).alias("mid_risk_count"),
    sum(when(col("warning_level") == "低风险", 1).otherwise(0)).alias("low_risk_count"),
    sum(when(col("warning_level") == "安全", 1).otherwise(0)).alias("safe_count"),
    round(avg("Time_Spent_Hours"), 2).alias("avg_study_hours"),
    round(avg("Quiz_Score_Avg"), 2).alias("avg_quiz_score"),
    round(avg("Assignment_Submission_Rate"), 2).alias("avg_submit_rate"),
    round(avg("Progress_Percentage"), 2).alias("avg_progress"),
    round(avg("Video_Completion_Rate"), 2).alias("avg_video_completion")
).withColumn("high_risk_pct", round(col("high_risk_count") / col("student_count") * 100, 2)).orderBy(col("high_risk_pct").desc())

c1_csv = os.path.join(OUTPUT_DIR, "course_risk_summary.csv")
c1_sql = os.path.join(OUTPUT_DIR, "course_risk_summary.sql")
save_single_csv(df_course_risk, c1_csv)
generate_insert_sql(df_course_risk, "course_risk_summary", c1_sql)

print("\n【分课程风险统计】")
df_course_risk.show(truncate=False)

# 分学位学情
df_education_risk = df_warning.groupBy("Education_Level").agg(
    count("Student_ID").alias("student_count"),
    round(count("Student_ID") / lit(total_valid) * 100, 2).alias("ratio_pct"),
    round(avg("Time_Spent_Hours"), 2).alias("avg_total_study_hours"),
    round(avg("Quiz_Score_Avg"), 2).alias("avg_quiz_score"),
    round(avg("Assignment_Submission_Rate"), 2).alias("avg_submit_rate"),
    round(avg("Progress_Percentage"), 2).alias("avg_progress"),
    round(avg("Video_Completion_Rate"), 2).alias("avg_video_completion"),
    round(sum(when(col("warning_level") == "高风险", 1).otherwise(0)) / count("Student_ID") * 100, 2).alias("high_risk_pct"),
    round(sum(when(col("warning_level") == "中风险", 1).otherwise(0)) / count("Student_ID") * 100, 2).alias("mid_risk_pct"),
    round(sum(when(col("warning_level") == "低风险", 1).otherwise(0)) / count("Student_ID") * 100, 2).alias("low_risk_pct"),
    round(sum(when(col("warning_level") == "安全", 1).otherwise(0)) / count("Student_ID") * 100, 2).alias("safe_pct")
).orderBy(col("avg_total_study_hours").desc())

e1_csv = os.path.join(OUTPUT_DIR, "education_risk_summary.csv")
e1_sql = os.path.join(OUTPUT_DIR, "education_risk_summary.sql")
save_single_csv(df_education_risk, e1_csv)
generate_insert_sql(df_education_risk, "education_risk_summary", e1_sql)

print("\n【分学历学情统计】")
df_education_risk.show(truncate=False)

# 合并总SQL文件
all_sql_files = [s1_sql, s2_sql, t1_sql, t2_sql, w1_sql, w2_sql, c1_sql, e1_sql]
total_sql_path = os.path.join(OUTPUT_DIR, "online_learning_analysis_result.sql")
merge_all_sql(all_sql_files, total_sql_path)

# 最终输出统计
risk_count = df_all_student.filter(col("warning_level") != "安全").count()
print("\n" + "=" * 70)
print(f"清洗后有效学生样本：{total_valid} 条")
print(f"存在风险学生总数：{risk_count} 名")
print("\n✅ 所有文件已输出到目录：", OUTPUT_DIR)
print("  📄 总SQL文件：online_learning_analysis_result.sql")
print("  📊 单表CSV/SQL共8组")
print("=" * 70)

spark.stop()