from pathlib import Path

import numpy as np
import pandas as pd


# ==================================================
# 1. 文件路径
# ==================================================
BASE_DIR = Path(__file__).resolve().parent

RAW_FILE = BASE_DIR / "raw" / "Course_Completion_Prediction.csv"
OUTPUT_DIR = BASE_DIR / "processed"
OUTPUT_FILE = OUTPUT_DIR / "cleaned_online_learning.csv"
REPORT_FILE = OUTPUT_DIR / "cleaning_report.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. 工具函数
# ==================================================
def clean_column_names(columns: pd.Index) -> pd.Index:
    """清理字段名前后的空格，并统一空白字符。"""
    return (
        columns.astype(str)
        .str.strip()
        .str.replace(r"\s+", "_", regex=True)
    )


def parse_percentage(series: pd.Series) -> pd.Series:
    """
    将百分比字段转换为 0~100 的数值。

    支持：
    80%  -> 80
    80   -> 80
    0.8  -> 80
    """
    text = series.astype("string").str.strip()
    has_percent_sign = text.str.contains("%", regex=False, na=False)

    values = pd.to_numeric(
        text.str.replace("%", "", regex=False),
        errors="coerce"
    )

    # 没有百分号且数值处于 0~1 时，认为原数据使用小数表示比例
    decimal_mask = (
        ~has_percent_sign
        & values.notna()
        & values.between(0, 1)
    )

    values.loc[decimal_mask] = values.loc[decimal_mask] * 100
    return values


def parse_boolean(series: pd.Series) -> pd.Series:
    """将多种真假写法统一转换为 1 和 0。"""
    mapping = {
        "yes": 1,
        "y": 1,
        "true": 1,
        "1": 1,
        "completed": 1,
        "complete": 1,
        "是": 1,
        "已完成": 1,

        "no": 0,
        "n": 0,
        "false": 0,
        "0": 0,
        "not completed": 0,
        "incomplete": 0,
        "dropout": 0,
        "否": 0,
        "未完成": 0,
    }

    cleaned = series.astype("string").str.strip().str.lower()
    result = cleaned.map(mapping)

    # 原字段本身可能已经是数值
    numeric = pd.to_numeric(series, errors="coerce")
    result = result.fillna(numeric)

    return result


# ==================================================
# 3. 读取原始数据
# ==================================================
if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"找不到原始数据文件：{RAW_FILE}\n"
        "请将数据集重命名为 online_learning.csv，"
        "并放入 data/raw 文件夹。"
    )

df = pd.read_csv(
    RAW_FILE,
    encoding="utf-8",
    low_memory=False
)

original_rows = len(df)
original_columns = len(df.columns)

print(f"原始数据：{original_rows} 行，{original_columns} 列")

df.columns = clean_column_names(df.columns)


# ==================================================
# 4. 检查必须字段
# ==================================================
required_columns = {
    "Student_ID",
    "Course_ID",
    "Course_Name",
    "Completed",
}

missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(
        f"数据中缺少必要字段：{sorted(missing_columns)}"
    )


# ==================================================
# 5. 清理字符串字段
# ==================================================
text_columns = [
    "Student_ID",
    "Name",
    "Gender",
    "Education_Level",
    "Employment_Status",
    "City",
    "Device_Type",
    "Internet_Connection_Quality",
    "Course_ID",
    "Course_Name",
    "Category",
    "Course_Level",
    "Payment_Mode",
]

for column in text_columns:
    if column in df.columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
        )

        # 将常见的空字符串统一成缺失值
        df[column] = df[column].replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "null": pd.NA,
                "NULL": pd.NA,
            }
        )


# ==================================================
# 6. 统一类别字段
# ==================================================
if "Gender" in df.columns:
    gender_mapping = {
        "male": "Male",
        "m": "Male",
        "男": "Male",
        "female": "Female",
        "f": "Female",
        "女": "Female",
        "other": "Other",
        "其他": "Other",
    }

    df["Gender"] = (
        df["Gender"]
        .str.lower()
        .map(gender_mapping)
        .fillna("Unknown")
    )

category_columns = [
    "Education_Level",
    "Employment_Status",
    "City",
    "Device_Type",
    "Internet_Connection_Quality",
    "Course_Name",
    "Category",
    "Course_Level",
    "Payment_Mode",
]

for column in category_columns:
    if column in df.columns:
        df[column] = df[column].fillna("Unknown")


# ==================================================
# 7. 转换数值字段
# ==================================================
integer_columns = [
    "Age",
    "Course_Duration_Days",
    "Login_Frequency",
    "Discussion_Participation",
    "Days_Since_Last_Login",
    "Notifications_Checked",
    "Assignments_Submitted",
    "Assignments_Missed",
    "Quiz_Attempts",
    "Rewatch_Count",
    "Reminder_Emails_Clicked",
    "Support_Tickets_Raised",
]

float_columns = [
    "Instructor_Rating",
    "Average_Session_Duration_Min",
    "Time_Spent_Hours",
    "Peer_Interaction_Score",
    "Quiz_Score_Avg",
    "Project_Grade",
    "Payment_Amount",
    "Satisfaction_Rating",
]

percentage_columns = [
    "Video_Completion_Rate",
    "Progress_Percentage",
    "App_Usage_Percentage",
]

for column in integer_columns + float_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

for column in percentage_columns:
    if column in df.columns:
        df[column] = parse_percentage(df[column])


# ==================================================
# 8. 布尔字段转换
# ==================================================
boolean_columns = [
    "Fee_Paid",
    "Discount_Used",
    "Completed",
]

for column in boolean_columns:
    if column in df.columns:
        df[column] = parse_boolean(df[column])


# ==================================================
# 9. 日期转换
# ==================================================
if "Enrollment_Date" in df.columns:
    df["Enrollment_Date"] = pd.to_datetime(
        df["Enrollment_Date"],
        errors="coerce"
    )


# ==================================================
# 10. 删除关键字段为空的数据
# ==================================================
critical_columns = [
    "Student_ID",
    "Course_ID",
    "Course_Name",
    "Completed",
]

before_critical_drop = len(df)
df = df.dropna(subset=critical_columns)
critical_missing_removed = before_critical_drop - len(df)


# ==================================================
# 11. 删除重复数据
# ==================================================
# 同一名学生可以参加多门课程，因此不能只按 Student_ID 去重
before_duplicates = len(df)

df = df.drop_duplicates(
    subset=["Student_ID", "Course_ID"],
    keep="last"
)

duplicate_rows_removed = before_duplicates - len(df)


# ==================================================
# 12. 过滤明显异常值
# ==================================================
range_rules = {
    "Age": (10, 100),
    "Course_Duration_Days": (1, 3650),
    "Instructor_Rating": (0, 5),
    "Average_Session_Duration_Min": (0, 1440),
    "Video_Completion_Rate": (0, 100),
    "Time_Spent_Hours": (0, 10000),
    "Peer_Interaction_Score": (0, 100),
    "Quiz_Score_Avg": (0, 100),
    "Project_Grade": (0, 100),
    "Progress_Percentage": (0, 100),
    "App_Usage_Percentage": (0, 100),
    "Satisfaction_Rating": (0, 5),
    "Completed": (0, 1),
    "Fee_Paid": (0, 1),
    "Discount_Used": (0, 1),
}

invalid_masks = []

for column, (minimum, maximum) in range_rules.items():
    if column in df.columns:
        invalid_masks.append(
            df[column].notna()
            & ~df[column].between(minimum, maximum)
        )

if invalid_masks:
    invalid_row_mask = np.logical_or.reduce(invalid_masks)
    abnormal_rows_removed = int(invalid_row_mask.sum())
    df = df.loc[~invalid_row_mask].copy()
else:
    abnormal_rows_removed = 0


# ==================================================
# 13. 处理剩余缺失值
# ==================================================
numeric_columns = df.select_dtypes(
    include=["number"]
).columns.tolist()

# Completed 是目标字段，不做中位数填充
numeric_fill_columns = [
    column
    for column in numeric_columns
    if column != "Completed"
]

for column in numeric_fill_columns:
    if df[column].isna().any():
        median_value = df[column].median()

        if pd.isna(median_value):
            median_value = 0

        df[column] = df[column].fillna(median_value)

remaining_text_columns = df.select_dtypes(
    include=["object", "string"]
).columns

for column in remaining_text_columns:
    df[column] = df[column].fillna("Unknown")


# ==================================================
# 14. 创建有用的标准字段
# ==================================================
if {
    "Assignments_Submitted",
    "Assignments_Missed"
}.issubset(df.columns):

    total_assignments = (
        df["Assignments_Submitted"]
        + df["Assignments_Missed"]
    )

    df["Assignment_Submission_Rate"] = np.where(
        total_assignments > 0,
        df["Assignments_Submitted"] / total_assignments * 100,
        0
    ).round(2)


# 姓名不是分析所必需，保留 Student_ID 即可
if "Name" in df.columns:
    df = df.drop(columns=["Name"])


# ==================================================
# 15. 调整数据类型
# ==================================================
for column in integer_columns:
    if column in df.columns:
        df[column] = df[column].round().astype("int64")

for column in boolean_columns:
    if column in df.columns:
        df[column] = df[column].round().astype("int64")

float_output_columns = [
    column
    for column in float_columns
    + percentage_columns
    + ["Assignment_Submission_Rate"]
    if column in df.columns
]

for column in float_output_columns:
    df[column] = df[column].astype(float).round(2)


# ==================================================
# 16. 保存结果
# ==================================================
df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
    date_format="%Y-%m-%d"
)

final_rows = len(df)
final_columns = len(df.columns)

report = pd.DataFrame(
    {
        "指标": [
            "原始行数",
            "原始列数",
            "删除的关键字段缺失行数",
            "删除的重复行数",
            "删除的异常行数",
            "清洗后行数",
            "清洗后列数",
        ],
        "数值": [
            original_rows,
            original_columns,
            critical_missing_removed,
            duplicate_rows_removed,
            abnormal_rows_removed,
            final_rows,
            final_columns,
        ],
    }
)

report.to_csv(
    REPORT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ==================================================
# 17. 输出清洗结果
# ==================================================
print("\n数据清洗完成")
print(f"清洗后数据：{final_rows} 行，{final_columns} 列")
print(f"删除关键字段缺失：{critical_missing_removed} 行")
print(f"删除重复数据：{duplicate_rows_removed} 行")
print(f"删除异常数据：{abnormal_rows_removed} 行")
print(f"清洗结果保存至：{OUTPUT_FILE}")
print(f"清洗报告保存至：{REPORT_FILE}")

print("\n清洗后的字段：")
print(df.columns.tolist())

print("\n清洗后前5行：")
print(df.head())