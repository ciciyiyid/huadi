# 在线学习平台数据分析与学生画像系统

## 一、项目简介

本项目以在线学习平台数据为基础，构建完整的数据仓库，并实现学生学习行为分析、课程统计分析以及学生画像，为后端接口开发、数据可视化和学生聚类分析提供数据支持。

项目主要流程如下：

```
原始CSV数据
        │
        ▼
Python数据清洗
        │
        ▼
HDFS
        │
        ▼
Hive数据仓库
ODS → DWD → DIM → DWS
        │
        ▼
Spark
        │
        ▼
MySQL
        │
        ▼
Flask后端 + 数据分析 + 可视化
```

---

# 二、项目目录

```
huadifinalproject
│
├── data
│   ├── cleaned_online_learning.csv
│   ├── data_clean.py
│   └── data_put_hdfs.py
│
├── spark
│   └── hive_to_mysql.py
│
├── sql
│   ├── hive
│   │   ├── 01_ods.sql
│   │   ├── 02_dwd.sql
│   │   ├── 03_dim.sql
│   │   └── 04_dws.sql
│   │
│   └── mysql
│       ├── create_tables.sql
│       └── online_learning_db.sql
│
└── README.md
```

---

# 三、数据库说明

数据库名称：

```
online_learning_db
```

包含五张业务表：

| 表名 | 说明 |
|------|------|
| student_info | 学生基础信息 |
| course_info | 课程基础信息 |
| student_stat | 学生课程学情统计 |
| course_stat | 课程整体统计 |
| student_feature | 学生聚类分析特征 |

---

# 四、数据库恢复

安装 MySQL 8.x 后执行：

```bash
mysql -u root -p < sql/mysql/online_learning_db.sql
```

恢复完成后即可得到完整数据库。

---

# 五、后端开发说明（Flask）

后端负责人主要使用 MySQL 中的五张业务表进行接口开发。

建议数据库连接：

```
Host：127.0.0.1

Port：3306

Database：online_learning_db
```

主要接口建议：

- 学生信息接口
- 学生画像接口
- 学情统计接口
- 课程统计接口
- 首页数据总览接口

数据库已经整理完成，不需要再连接 Hive。

---

# 六、K-Means 聚类成员说明

建议直接使用：

```
student_feature
```

作为聚类输入数据。

该表已经完成：

- 学习时长统计
- 登录频率统计
- 完成率统计
- 成绩统计
- 讨论互动统计
- 活跃度统计

可以直接导出为 CSV 后进行：

- K-Means 聚类
- PCA 降维
- 学生画像分析

无需重新进行数据清洗。

---

# 七、数据仓库流程

```
CSV
 │
 ▼
ODS
 │
 ▼
DWD
 │
 ├── DIM
 │      ├── dim_student_info
 │      └── dim_course_info
 │
 ▼
DWS
 ├── dws_student_stat
 ├── dws_course_stat
 └── dws_student_feature
```

---

# 八、项目分工

### 数据仓库（已完成）

- 数据清洗
- HDFS 上传
- Hive ODS
- Hive DWD
- Hive DIM
- Hive DWS
- Spark 同步 MySQL

### 后端（待完成）

- Flask
- REST API
- 数据查询接口
- 数据可视化接口

### 聚类分析（待完成）

- K-Means 聚类
- 聚类结果分析
- 学生画像标签

---

# 九、注意事项

1. MySQL 版本建议使用 8.x。
2. 后端直接连接 MySQL，不需要安装 Hadoop、Hive。
3. student_feature 为聚类分析推荐数据源。
4. 所有业务数据均来源于 Hive DWS 层汇总结果。

---

# 十、项目当前状态

✅ 数据清洗完成

✅ Hive 数据仓库完成

✅ Spark 同步完成

✅ MySQL 数据库完成

⬜ Flask 后端开发（进行中）

⬜ 学生聚类分析（进行中）

⬜ 数据可视化（进行中）
