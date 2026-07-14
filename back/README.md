# Flask 后端接口（在线教学分析系统）

## 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

## 2. 配置环境变量

复制 `.env.example` 为 `.env`，并填写 MySQL 密码。

关键配置：
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`（默认 `online_learning_db`）
- `JWT_SECRET_KEY`

## 3. 启动服务

```bash
python app.py
```

服务默认运行在 `http://127.0.0.1:5000`。

## 4. 已提供接口

### 认证与权限
- `POST /api/auth/register` 注册（角色：`admin` / `teacher` / `student`）
- `POST /api/auth/login` 登录并返回 JWT
- `GET /api/auth/me` 当前登录用户信息

### 数据总览与大屏
- `GET /api/overview/metrics` 概览指标（管理员/教师）
- `GET /api/overview/weekly-trend?limit=24` 周学习趋势
- `GET /api/overview/course-enrollment` 课程报名排行
- `GET /api/overview/warning-distribution` 预警等级分布

### 资源效能
- `GET /api/resources/core-stats` 资源效能核心指标

### 画像
- `GET /api/profiles/students/<student_id>` 学生画像详情
- `GET /api/profiles/students/summary` 学生画像标签汇总
- `GET /api/profiles/teachers/<course_id>` 教师画像详情（按课程）
- `GET /api/profiles/teachers/summary` 教师画像等级汇总

### 预警
- `GET /api/warnings/students` 学生预警明细（支持筛选分页）
- `GET /api/warnings/levels` 预警等级统计
- `GET /api/warnings/courses` 课程风险汇总
- `GET /api/warnings/education` 学历维度风险汇总

## 5. 鉴权方式

请求头需带：

```text
Authorization: Bearer <token>
```

## 6. 角色控制说明

- `admin`: 全部接口
- `teacher`: 允许查看总览、预警、资源、教师画像，且仅能查看自己 `course_id` 的教师详情
- `student`: 仅允许查看自己的学生画像详情

注册时约束：
- `student` 必须传 `student_id` 且存在于 `student_info`
- `teacher` 必须传 `course_id` 且存在于 `teacher_profile_detail`

## 7. 前端对接建议

前端 4 号同学可按页面直接调用：
- 大屏：`overview` + `warnings/levels` + `warnings/courses`
- 数据总览页：`overview/metrics` + `overview/course-enrollment` + `resources/core-stats`
- 学生画像页：`profiles/students/<student_id>` + `profiles/students/summary`
- 教师画像页：`profiles/teachers/<course_id>` + `profiles/teachers/summary`
- 资源效能页：`resources/core-stats`
