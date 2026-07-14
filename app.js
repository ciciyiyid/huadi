const state = {
  token: localStorage.getItem("visual_token") || "",
  user: JSON.parse(localStorage.getItem("visual_user") || "null"),
  charts: {},
  cache: {},
  trendMode: "weekly",
  courseSort: "learner",
  degreeMetric: "study",
  riskSort: "total",
  performanceExtra: "core",
  adminDegreeBar: "ratio",
  warningPage: 1,
  pageSize: 10,
  selectedWarnings: new Set(),
  studentData: null,
  selectedStudentCourse: "",
  dataIssues: [],
};

const $ = (id) => document.getElementById(id);

const text = {
  preview: "\u8bf7\u5148\u767b\u5f55",
  login: "\u6b63\u5728\u767b\u5f55...",
  loginOk: "\u5df2\u767b\u5f55",
  loading: "\u6b63\u5728\u52a0\u8f7d\u6570\u636e...",
  updated: "\u6570\u636e\u5df2\u66f4\u65b0",
  loginFirst: "\u8bf7\u5148\u767b\u5f55",
  requestFailed: "\u8bf7\u6c42\u5931\u8d25",
  badCredentials: "\u7528\u6237\u540d\u6216\u5bc6\u7801\u4e0d\u6b63\u786e\uff0c\u8bf7\u68c0\u67e5\u540e\u91cd\u8bd5",
  serverUnavailable: "\u540e\u7aef\u6682\u65f6\u8fde\u4e0d\u4e0a\uff0c\u8bf7\u68c0\u67e5\u540e\u7aef\u5730\u5740\u6216\u7f51\u7edc",
};

const roleConfig = {
  admin: {
    label: "\u7ba1\u7406\u5458",
    scope: "\u53ef\u67e5\u770b\u5b66\u60c5\u603b\u89c8\u548c\u5168\u5c40\u7ba1\u7406\u5206\u6790",
    defaultSection: "overview",
    sections: ["overview", "admin"],
  },
  teacher: {
    label: "\u6559\u5e08",
    scope: "\u53ef\u67e5\u770b\u5b66\u60c5\u603b\u89c8\u548c\u672c\u4eba\u6388\u8bfe\u60c5\u51b5",
    defaultSection: "teacher",
    sections: ["overview", "teacher"],
  },
  student: {
    label: "\u5b66\u751f",
    scope: "\u53ef\u67e5\u770b\u5b66\u60c5\u603b\u89c8\u548c\u4e2a\u4eba\u5b66\u4e60\u9884\u8b66",
    defaultSection: "student",
    sections: ["overview", "student"],
  },
};

const courseNameZh = {
  C101: "\u0050\u0079\u0074\u0068\u006f\u006e\u57fa\u7840",
  C102: "\u0050\u0079\u0074\u0068\u006f\u006e\u6570\u636e\u5206\u6790",
  C103: "\u673a\u5668\u5b66\u4e60",
  C104: "\u0057\u0065\u0062\u5f00\u53d1",
  C105: "\u0055\u0049\u002f\u0055\u0058\u8bbe\u8ba1\u57fa\u7840",
  C106: "\u6570\u636e\u5e93\u7cfb\u7edf",
  C107: "\u4e91\u8ba1\u7b97",
  C108: "\u7f51\u7edc\u5b89\u5168",
};

const courseTypeAdvice = {
  "\u6807\u6746\u5f15\u9886\u578b": "\u6559\u5b66\u8868\u73b0\u4f18\u79c0\uff0c\u5efa\u8bae\u6c89\u6dc0\u8bfe\u7a0b\u7ecf\u9a8c\u5e76\u8fdb\u884c\u793a\u8303\u5206\u4eab\u3002",
  "\u7a33\u5065\u6df1\u8015\u578b": "\u8bfe\u7a0b\u8fd0\u884c\u7a33\u5b9a\uff0c\u5efa\u8bae\u6301\u7eed\u4f18\u5316\u4f5c\u4e1a\u53cd\u9988\u548c\u5b66\u751f\u4e92\u52a8\u3002",
  "\u6f5c\u529b\u6210\u957f\u578b": "\u8bfe\u7a0b\u4ecd\u6709\u63d0\u5347\u7a7a\u95f4\uff0c\u8bf7\u91cd\u70b9\u5173\u6ce8\u4f4e\u8fdb\u5ea6\u548c\u9ad8\u98ce\u9669\u5b66\u751f\u3002",
};

function setStatus(message, isError = false) {
  $("loginStatus").textContent = message;
  $("loginStatus").style.color = isError ? "#ffd1cc" : "#b7c8d8";
}

function baseUrl() {
  return $("baseUrl").value.replace(/\/$/, "");
}

function currentRole() {
  return state.user?.role || "admin";
}

function allowedSections() {
  return roleConfig[currentRole()]?.sections || roleConfig.admin.sections;
}

function isAllowed(section) {
  return allowedSections().includes(section);
}

function setActiveNav(section) {
  document.querySelectorAll("[data-section-link]").forEach((link) => {
    link.classList.toggle("active", link.dataset.sectionLink === section);
  });
}

function showSection(section) {
  const config = roleConfig[currentRole()] || roleConfig.admin;
  const target = config.sections.includes(section) ? section : config.defaultSection;
  document.querySelectorAll("[data-section]").forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.section !== target);
  });
  setActiveNav(target);
  history.replaceState(null, "", `#${target}`);
  setTimeout(resizeCharts, 50);
}

function applyRoleView() {
  const config = state.user ? roleConfig[currentRole()] || roleConfig.admin : {
    label: "",
    scope: "",
    defaultSection: "overview",
    sections: ["overview"],
  };
  document.querySelectorAll("[data-section-link]").forEach((link) => {
    link.classList.toggle("hidden", !config.sections.includes(link.dataset.sectionLink));
  });
  $("userBadge").classList.toggle("hidden", !state.user);
  if (state.user) {
    $("userRole").textContent = config.label;
    $("userName").textContent = state.user.username || "--";
    $("userScope").textContent = config.scope;
  }
  $("userMenuBtn").textContent = state.user?.username ? state.user.username.slice(0, 2).toUpperCase() : "\u767b\u5f55";
  document.querySelectorAll("[data-admin-tool]").forEach((item) => {
    item.classList.toggle("hidden", !state.user || currentRole() !== "admin");
  });
  const studentOwnOnly = state.user && currentRole() === "student";
  ["studentId", "loadStudentBtn"].forEach((id) => {
    const item = $(id);
    if (item) item.classList.toggle("hidden", studentOwnOnly);
  });
  if (state.user?.student_id) $("studentId").value = state.user.student_id;
  const savedBaseUrl = localStorage.getItem("visual_base_url");
  if (savedBaseUrl && $("baseUrl")) $("baseUrl").value = savedBaseUrl;
  showSection(config.defaultSection);
}

function friendlyError(error) {
  const message = String(error?.message || error || "");
  if (message.includes("401") || message.includes("password")) return text.badCredentials;
  return message || text.requestFailed;
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", "ngrok-skip-browser-warning": "true", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  try {
    const response = await fetch(`${baseUrl()}${path}`, { ...options, headers });
    const rawText = await response.text();
    const data = rawText ? JSON.parse(rawText) : null;
    if (!response.ok) throw new Error(`${response.status} ${data?.message || text.requestFailed}`);
    return data;
  } catch (error) {
    throw error;
  }
}

function formatNumber(value, suffix = "") {
  if (value === null || value === undefined || value === "") return "--";
  const number = Number(value);
  if (Number.isNaN(number)) return `${value}${suffix}`;
  return `${number.toLocaleString("zh-CN", { maximumFractionDigits: 2 })}${suffix}`;
}

function numberValue(...values) {
  for (const value of values) {
    const number = Number(value);
    if (!Number.isNaN(number)) return number;
  }
  return 0;
}

function percentFromRate(value) {
  const number = Number(value);
  if (Number.isNaN(number)) return 0;
  return number <= 1 ? number * 100 : number;
}

function chart(id) {
  if (!state.charts[id]) state.charts[id] = echarts.init($(id));
  return state.charts[id];
}

function resizeCharts() {
  Object.values(state.charts).forEach((instance) => instance.resize());
}

function riskColor(name) {
  const value = String(name);
  if (value.includes("\u9ad8")) return "#d92d20";
  if (value.includes("\u4e2d")) return "#f79009";
  if (value.includes("\u4f4e")) return "#12a594";
  return "#1976d2";
}

function pickTextValue(row, fallbackKeys) {
  for (const key of fallbackKeys) {
    if (row[key] !== undefined && row[key] !== null && row[key] !== "") return row[key];
  }
  const ignoredKeys = new Set(["student_count", "ratio_percent", "course_count", "avg_effect_score", "avg_student_count"]);
  const match = Object.entries(row).find(([key, value]) => !ignoredKeys.has(key) && typeof value === "string" && value.trim());
  return match?.[1] || "\u672a\u5206\u7c7b";
}

function initFilters(education = []) {
  const degreeFilter = $("degreeFilter");
  [degreeFilter].forEach((select) => {
    if (!select || select.dataset.ready === "1") return;
    education.forEach((row) => {
      const option = document.createElement("option");
      option.value = row.Education_Level;
      option.textContent = row.Education_Level;
      select.appendChild(option);
    });
    select.dataset.ready = "1";
  });
  const adminCourseFilter = document.getElementById("adminCourseFilter");
  if (adminCourseFilter && adminCourseFilter.dataset.ready !== "1") {
    (state.cache.enrollment || []).forEach((row) => {
      const option = document.createElement("option");
      option.value = row.course_id;
      option.textContent = `${row.course_id} ${row.course_name || ""}`;
      adminCourseFilter.appendChild(option);
    });
    adminCourseFilter.dataset.ready = "1";
  }
}

function filteredEducation() {
  const degree = $("degreeFilter")?.value || "";
  const rows = state.cache.education || [];
  return degree ? rows.filter((row) => row.Education_Level === degree) : rows;
}

function filteredWarnings(rows = warningRowsSource()) {
  const risk = document.getElementById("riskFilter")?.value || "";
  return risk ? rows.filter((row) => row.warning_level === risk) : rows;
}

function weeklyAsDaily(rows) {
  return rows.flatMap((row, index) => {
    const base = numberValue(row.total_study_time_hours) / 7;
    return Array.from({ length: 7 }, (_, day) => ({
      week_label: `${row.week_label}-D${day + 1}`,
      total_study_time_hours: Number((base * (0.86 + day * 0.04)).toFixed(2)),
      learner_count: Math.round(numberValue(row.learner_count) * (0.82 + day * 0.03)),
      avg_quiz_score: numberValue(row.avg_quiz_score),
      avg_session_duration_min: 28 + ((index + day) % 6),
    }));
  });
}

function renderTrendChart() {
  const weekly = state.cache.weekly || [];
  const rows = state.trendMode === "daily" ? weeklyAsDaily(weekly).slice(-28) : weekly;
  chart("weeklyChart").setOption({
    tooltip: {
      trigger: "axis",
      formatter(items) {
        const index = items[0]?.dataIndex || 0;
        const row = rows[index] || {};
        const lines = items.map((item) => `${item.marker}${item.seriesName}: ${formatNumber(item.value)}`);
        lines.push(`\u5e73\u5747\u5355\u6b21\u5b66\u4e60: ${formatNumber(row.avg_session_duration_min, "min")}`);
        lines.push(`\u5e73\u5747\u6d4b\u9a8c\u5206: ${formatNumber(row.avg_quiz_score)}`);
        return [`<strong>${row.week_label}</strong>`, ...lines].join("<br/>");
      },
    },
    dataZoom: currentRole() === "admin" ? [{ type: "inside" }, { type: "slider", height: 18, bottom: 6 }] : [],
    legend: { top: 0 },
    grid: { left: 54, right: 64, top: 44, bottom: currentRole() === "admin" ? 52 : 38, containLabel: true },
    xAxis: { type: "category", boundaryGap: true, data: rows.map((row) => row.week_label) },
    yAxis: [{ type: "value", name: "\u5b66\u4e60\u65f6\u957f" }, { type: "value", name: "\u5b66\u4e60\u4eba\u6570" }],
    series: [
      { name: "\u603b\u5b66\u4e60\u65f6\u957f", type: "line", smooth: true, data: rows.map((row) => numberValue(row.total_study_time_hours)), areaStyle: { opacity: 0.14 } },
      { name: "\u5b66\u4e60\u4eba\u6570", type: "bar", yAxisIndex: 1, data: rows.map((row) => numberValue(row.learner_count)), itemStyle: { color: "#12a594" } },
    ],
  });
}

function renderWarningPie() {
  const warnings = state.cache.warningDistribution || [];
  const chartDom = $("warningPie");
  const panel = chartDom?.parentElement;
  const existingLegend = panel?.querySelector(".warning-legend-grid");
  if (existingLegend) existingLegend.remove();
  if (panel) panel.insertAdjacentHTML("beforeend", warningLegendGridHtml(warnings));
  chart("warningPie").setOption({
    tooltip: { trigger: "item" },
    legend: { show: false },
    series: [{ type: "pie", radius: ["45%", "70%"], center: ["50%", "40%"], data: warnings.map((row) => ({ name: row.warning_level, value: numberValue(row.student_count), itemStyle: { color: riskColor(row.warning_level) } })) }],
  });
  chart("warningPie").off("click");
  chart("warningPie").on("click", (params) => {
    if (currentRole() === "admin") openRiskDrilldown(params.name);
  });
}

function warningRuleDetail(row) {
  const loginFrequency = numberValue(row.Login_Frequency, row.login_frequency, row.login_freq, row.Avg_Login_Frequency)
  const daysSinceLogin = numberValue(row.Days_Since_Last_Login, row.days_since_last_login, row.avg_days_since_login)
  const submitRate = numberValue(row.Assignment_Submission_Rate, row.assignment_submission_rate, row.submit_rate)
  const missedAssignments = numberValue(row.Missed_Assignment_Count, row.missed_assignment_count, row.total_assignments_missed)
  const progress = numberValue(row.Progress_Percentage, row.progress_percentage, row.avg_progress)
  const videoRate = numberValue(row.Video_Completion_Rate, row.video_completion_rate, row.avg_video_completion_rate)
  const quizScore = numberValue(row.Quiz_Score_Avg, row.quiz_score_avg, row.avg_quiz_score)

  const loginRisk = loginFrequency < 4 || daysSinceLogin > 10
  const assignmentRisk = submitRate < 50 || missedAssignments > 4
  const progressRisk = progress < 30 && videoRate < 40
  const scoreRisk = quizScore < 55

  const riskSum = [loginRisk, assignmentRisk, progressRisk, scoreRisk].filter(Boolean).length
  const warningLevel = riskSum >= 3 ? '高风险' : riskSum === 2 ? '中风险' : riskSum === 1 ? '低风险' : '安全'

  return {
    loginFrequency,
    daysSinceLogin,
    submitRate,
    missedAssignments,
    progress,
    videoRate,
    quizScore,
    loginRisk,
    assignmentRisk,
    progressRisk,
    scoreRisk,
    riskSum,
    warningLevel,
    ruleSummary: `登录:${loginRisk ? '风险' : '正常'} / 作业:${assignmentRisk ? '风险' : '正常'} / 进度:${progressRisk ? '风险' : '正常'} / 成绩:${scoreRisk ? '风险' : '正常'}`,
    ruleDetail: `登录频率 ${formatNumber(loginFrequency)} 次，距上次登录 ${formatNumber(daysSinceLogin, '天')}；作业提交率 ${formatNumber(submitRate, '%')}，漏交 ${formatNumber(missedAssignments)} 次；学习进度 ${formatNumber(progress, '%')}，视频完成率 ${formatNumber(videoRate, '%')}；测验成绩 ${formatNumber(quizScore)}。`,
  }
}

function warningLegendGridHtml(warnings) {
  if (!warnings.length) return ''
  return `
    <div class="warning-legend-grid">
      ${warnings.map((row) => `
        <div class="warning-legend-item">
          <span class="warning-legend-swatch" style="background:${riskColor(row.warning_level)}"></span>
          <span>${row.warning_level} ${formatNumber(row.student_count)}人 (${formatNumber(row.risk_ratio_pct, '%')})</span>
        </div>
      `).join('')}
    </div>
  `
}
function mergedCourseRows() {
  const enrollment = state.cache.enrollment || [];
  const courses = state.cache.courseRisk || [];
  return enrollment.map((row) => {
    const risk = courses.find((item) => item.Course_ID === row.course_id) || {};
    return { ...risk, ...row };
  });
}

function renderEnrollmentChart() {
  const rows = mergedCourseRows().sort((a, b) => {
    if (state.courseSort === "completion") return numberValue(b.avg_progress, b.avg_completion_rate) - numberValue(a.avg_progress, a.avg_completion_rate);
    if (state.courseSort === "score") return numberValue(b.avg_quiz_score) - numberValue(a.avg_quiz_score);
    return numberValue(b.learner_count) - numberValue(a.learner_count);
  });
  const valueKey = state.courseSort === "score" ? "avg_quiz_score" : state.courseSort === "completion" ? "avg_progress" : "learner_count";
  const seriesName = state.courseSort === "score" ? "\u5e73\u5747\u6d4b\u9a8c\u5206" : state.courseSort === "completion" ? "\u5e73\u5747\u5b8c\u6210\u7387" : "\u9009\u8bfe\u4eba\u6570";
  const unit = state.courseSort === "completion" ? "%" : "";
  chart("enrollmentChart").setOption({
    tooltip: { trigger: "axis" },
    grid: { left: 54, right: 18, top: 28, bottom: 86 },
    xAxis: { type: "category", axisLabel: { rotate: 28 }, data: rows.map((row) => row.course_name || row.Course_Name || row.course_id) },
    yAxis: { type: "value" },
    series: [{
      name: seriesName,
      type: "bar",
      data: rows.map((row) => numberValue(row[valueKey])),
      label: { show: true, position: "top", formatter: `{c}${unit}` },
      itemStyle: { color: "#1976d2", borderRadius: [4, 4, 0, 0] },
    }],
  });
  chart("enrollmentChart").off("click");
  chart("enrollmentChart").on("click", (params) => {
    if (currentRole() !== "admin") return;
    showSection("admin");
    setStatus(`\u5df2\u5207\u6362\u5230 ${rows[params.dataIndex]?.course_id || ""} \u7684\u8bfe\u7a0b\u98ce\u9669\u89c6\u56fe`);
  });
}

function renderDegreeChart() {
  const rows = filteredEducation();
  const config = {
    study: { name: "\u5e73\u5747\u603b\u5b66\u4e60\u65f6\u957f", key: "avg_total_study_hours", fallback: "avg_total_study_time_hours", unit: "h", color: "#12a594" },
    score: { name: "\u5e73\u5747\u6d4b\u9a8c\u6210\u7ee9", key: "avg_quiz_score", unit: "", color: "#1976d2" },
    submit: { name: "\u5e73\u5747\u4f5c\u4e1a\u63d0\u4ea4\u7387", key: "avg_submit_rate", unit: "%", color: "#7c3aed" },
    risk: { name: "\u9ad8\u98ce\u9669\u4eba\u6570\u5360\u6bd4", key: "high_risk_pct", unit: "%", color: "#d92d20" },
  }[state.degreeMetric];
  const allRows = state.cache.education || [];
  const allValues = allRows.map((row) => numberValue(row[config.key], row[config.fallback]));
  const maxValue = Math.max(...allValues, 0);
  const yMax = maxValue ? Math.ceil(maxValue * 1.18) : undefined;
  chart("degreeStudyChart").setOption({
    tooltip: { trigger: "axis" },
    grid: { left: 44, right: 18, top: 24, bottom: 40 },
    xAxis: { type: "category", data: rows.map((row) => row.Education_Level) },
    yAxis: { type: "value", name: config.unit, max: yMax },
    series: [{
      name: config.name,
      type: "bar",
      data: rows.map((row) => numberValue(row[config.key], row[config.fallback])),
      label: { show: true, position: "top", formatter: `{c}${config.unit}` },
      itemStyle: { color: config.color, borderRadius: [4, 4, 0, 0] },
    }],
  });
}

async function loadOverview() {
  const canReadMetrics = currentRole() !== "student";
  const overviewRequests = [
    ["概览指标", canReadMetrics ? request("/api/overview/metrics") : Promise.resolve({}), {}],
    ["学习趋势", request("/api/overview/weekly-trend?limit=24"), []],
    ["课程报名排行", request("/api/overview/course-enrollment"), []],
    ["预警等级分布", request("/api/overview/warning-distribution"), []],
    ["学历风险分布", request("/api/warnings/education"), []],
    ["教师画像汇总", request("/api/profiles/teachers/summary"), []],
    ["资源统计", request("/api/resources/core-stats"), []],
    ["课程风险汇总", request("/api/warnings/courses"), []],
  ];
  const results = await Promise.allSettled(overviewRequests.map(([, task]) => task));
  const [metrics, weekly, enrollment, warnings, education, teachers, resources, courseRisk] = results.map((result, index) => {
    if (result.status === "fulfilled") return result.value;
    state.dataIssues.push(`${overviewRequests[index][0]}：${friendlyError(result.reason)}`);
    return overviewRequests[index][2];
  });

  state.cache.metrics = metrics;
  state.cache.weekly = weekly;
  state.cache.enrollment = enrollment;
  state.cache.warningDistribution = warnings;
  state.cache.education = education;
  state.cache.teacherSummary = teachers;
  state.cache.resources = resources;
  state.cache.courseRisk = courseRisk;
  initFilters(education);

  const inferredStudents = warnings.reduce((sum, row) => sum + numberValue(row.student_count), 0);
  const teacherCount = numberValue(metrics.teacher_count, teachers.reduce((sum, row) => sum + numberValue(row.course_count), 0));
  const resourceCount = numberValue(metrics.resource_count, resources.length, metrics.course_count);
  const totalHours = weekly.reduce((sum, row) => sum + numberValue(row.total_study_time_hours), 0);

  $("studentCount").textContent = formatNumber(numberValue(metrics.student_count, inferredStudents));
  $("teacherCount").textContent = formatNumber(teacherCount);
  $("resourceCount").textContent = formatNumber(resourceCount);
  $("totalStudyHours").textContent = formatNumber(totalHours, "h");
  renderTrendChart();
  renderWarningPie();
  renderEnrollmentChart();
  renderDegreeChart();
}

function buildStudentCourses(data) {
  const baseFeature = data.feature || {};
  const baseWarning = data.warning || {};
  const rows = data.courses || data.course_profiles || data.enrollments;
  if (Array.isArray(rows) && rows.length) {
    return rows.map((row) => ({ feature: { ...baseFeature, ...row.feature, ...row }, warning: { ...baseWarning, ...row.warning, ...row } }));
  }
  const seed = { feature: baseFeature, warning: baseWarning };
  return [seed];
}

function studentCourseKey(course) {
  return course.warning.Course_ID || course.warning.Course_Name || "current";
}

function currentStudentCourse() {
  const courses = state.studentData?.courses || [];
  return courses.find((course) => studentCourseKey(course) === state.selectedStudentCourse) || courses[0] || { feature: {}, warning: {} };
}

function studentPersonaLabel(data, course, values, benchmark) {
  const profileLabel = data.profile?.["人群标签"] || data.profile?.persona_label || data.profile?.cluster_label;
  if (profileLabel) return profileLabel;
  if (values.completion >= benchmark.completion * 1.08 && values.score >= benchmark.score * 1.05 && values.time >= benchmark.time * 1.05) return "自律学霸";
  if (values.completion >= benchmark.completion && values.video >= benchmark.video && values.grade >= benchmark.grade) return "稳定进阶";
  if (String(course.warning?.warning_level || "").includes("高")) return "风险预警型";
  if (String(course.warning?.warning_level || "").includes("中")) return "波动跟进型";
  return "稳步提升型";
}

function renderStudentComparisonChart(values, benchmark, warning, personaLabel) {
  const strongPeer = {
    time: Number((benchmark.time * 1.28).toFixed(2)),
    completion: Math.min(100, Number((benchmark.completion * 1.14).toFixed(1))),
    video: Math.min(100, Number((benchmark.video * 1.16).toFixed(1))),
    grade: Math.min(100, Number((benchmark.grade * 1.12).toFixed(1))),
    score: Math.min(100, Number((benchmark.score * 1.1).toFixed(1))),
  };
  $("studentCompareTitle").textContent = `${warning.Course_ID || ""} ${warning.Course_Name || ""}`.trim() || personaLabel;
  chart("studentCompareChart").setOption({
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { left: 52, right: 22, top: 48, bottom: 46, containLabel: true },
    xAxis: { type: "category", data: ["学习时长", "课程完成率", "视频完课率", "作业成绩", "测验均分"] },
    yAxis: { type: "value", max: 100 },
    series: [
      { name: "本人", type: "bar", barGap: 0, data: [values.time * 10, values.completion, values.video, values.grade, values.score], itemStyle: { color: "#12a594" } },
      { name: "班级平均", type: "bar", data: [benchmark.time * 10, benchmark.completion, benchmark.video, benchmark.grade, benchmark.score], itemStyle: { color: "#f7c948" } },
      { name: "优秀学生", type: "bar", data: [strongPeer.time * 10, strongPeer.completion, strongPeer.video, strongPeer.grade, strongPeer.score], itemStyle: { color: "#1976d2" } },
    ],
  });
}
function buildStudentTagDistribution(summaryRows = []) {
  if (!Array.isArray(summaryRows) || !summaryRows.length) return [];
  return summaryRows.map((item, index) => ({
    name: item["人群标签"] || item.tag_label || item.name || item.label || `标签${index + 1}`,
    value: numberValue(item.ratio_percent, item.ratio_pct, item.ratio, item.percent),
    itemStyle: { color: ["#1976d2", "#12a594", "#f79009"][index % 3] },
  }));
}

function renderStudentTagPie(summaryRows = []) {
  const pie = $("studentTagPie");
  if (!pie) return;
  const data = buildStudentTagDistribution(summaryRows);
  if (!data.length) {
    chart("studentTagPie").clear();
    return;
  }
  chart("studentTagPie").setOption({
    tooltip: { trigger: "item", formatter: "{b}: {c}%" },
    legend: { bottom: 0, left: "center", textStyle: { color: "#667085", fontSize: 12 } },
    series: [{ type: "pie", radius: ["38%", "62%"], center: ["50%", "42%"], label: { color: "#344054", formatter: "{b}" }, data }],
  });
}
function benchmarkForCourse(course) {
  const id = course.warning.Course_ID;
  const row = (state.cache.courseRisk || []).find((item) => item.Course_ID === id) || {};
  return {
    time: numberValue(row.avg_study_time_hours),
    completion: numberValue(row.avg_progress),
    score: numberValue(row.avg_quiz_score),
    grade: numberValue(row.avg_submit_rate),
    video: numberValue(row.avg_video_completion_rate),
  };
}

function riskAdvice(course, values, benchmark) {
  const weak = [
    ["\u5b66\u4e60\u65f6\u957f", values.time, benchmark.time, "\u5efa\u8bae\u6bcf\u5468\u56fa\u5b9a\u5b89\u6392\u5b66\u4e60\u65f6\u6bb5\uff0c\u5148\u628a\u8bfe\u7a0b\u8fdb\u5ea6\u8865\u5230\u73ed\u7ea7\u5747\u503c\u9644\u8fd1\u3002"],
    ["\u8bfe\u7a0b\u8fdb\u5ea6", values.completion, benchmark.completion, "\u8bf7\u4f18\u5148\u5b8c\u6210\u672a\u5b66\u4e60\u7ae0\u8282\uff0c\u8fdb\u5ea6\u63d0\u5347\u540e\u98ce\u9669\u7b49\u7ea7\u4f1a\u660e\u663e\u4e0b\u964d\u3002"],
    ["\u89c6\u9891\u5b8c\u8bfe\u7387", values.video, benchmark.video, "\u5efa\u8bae\u6bcf\u5468\u5b8c\u6210\u5269\u4f59\u6559\u5b66\u89c6\u9891\uff0c\u8865\u8db3\u89c6\u9891\u5b8c\u8bfe\u7387\u3002"],
    ["\u4f5c\u4e1a\u63d0\u4ea4\u7387", values.grade, benchmark.grade, "\u8bf7\u68b3\u7406\u672a\u63d0\u4ea4\u4f5c\u4e1a\uff0c\u5148\u8865\u4ea4\u5206\u503c\u9ad8\u7684\u4efb\u52a1\u3002"],
    ["\u6d4b\u9a8c\u5e73\u5747\u5206", values.score, benchmark.score, "\u5efa\u8bae\u56de\u770b\u9519\u9898\u5bf9\u5e94\u77e5\u8bc6\u70b9\uff0c\u5b8c\u6210\u8bfe\u540e\u5c0f\u6d4b\u590d\u76d8\u3002"],
  ].filter((item) => item[1] < item[2] * 0.92).sort((a, b) => (a[1] / a[2]) - (b[1] / b[2]));
  const level = course.warning.warning_level || "--";
  const main = weak[0] || ["\u5b66\u4e60\u72b6\u6001", 1, 1, "\u5f53\u524d\u8868\u73b0\u8f83\u7a33\u5b9a\uff0c\u4fdd\u6301\u5b66\u4e60\u9891\u7387\u5e76\u6309\u65f6\u5b8c\u6210\u8bfe\u7a0b\u4efb\u52a1\u3002"];
  const prefix = String(level).includes("\u9ad8") ? "\u5f53\u524d\u98ce\u9669\u8f83\u9ad8\uff0c\u8bf7\u4f18\u5148\u5904\u7406\u6700\u8584\u5f31\u6307\u6807\u3002" : "\u5df2\u53d1\u73b0\u53ef\u4f18\u5316\u7684\u5b66\u4e60\u77ed\u677f\u3002";
  return { weakName: main[0], reason: `${main[0]}\u4f4e\u4e8e\u73ed\u7ea7\u5747\u503c`, advice: `${prefix}${main[3]}` };
}

function renderStudentCourseOptions() {
  const select = $("studentCourseSelect");
  const courses = state.studentData?.courses || [];
  if (!state.selectedStudentCourse || !courses.some((course) => studentCourseKey(course) === state.selectedStudentCourse)) {
    state.selectedStudentCourse = studentCourseKey(courses[0] || { warning: {} });
  }
  if (!select) return;
  select.innerHTML = courses.map((course) => {
    const key = studentCourseKey(course);
    const name = course.warning.Course_Name || key;
    return `<option value="${key}">${course.warning.Course_ID || "--"} ${name}</option>`;
  }).join("");
  select.value = state.selectedStudentCourse;
}

function renderStudentPage() {
  const data = state.studentData?.raw || {};
  const course = currentStudentCourse();
  const feature = course.feature || {};
  const warning = course.warning || {};
  const benchmark = benchmarkForCourse(course);
  const values = {
    time: numberValue(feature.total_study_time_hours, data.profile?.total_duration),
    completion: numberValue(feature.completion_rate, feature.avg_progress_percentage, warning.Progress_Percentage),
    grade: numberValue(feature.avg_project_grade, warning.Assignment_Submission_Rate),
    score: numberValue(feature.avg_quiz_score, warning.Quiz_Score_Avg),
    video: numberValue(feature.avg_video_completion_rate, warning.Video_Completion_Rate),
    days: numberValue(feature.learning_days, feature.study_days, data.profile?.learning_days, 12),
  };
  const advice = riskAdvice(course, values, benchmark);
  const level = warning.warning_level || "--";
  const riskTone = String(level).includes("\u9ad8") ? "high" : String(level).includes("\u4e2d") ? "mid" : String(level).includes("\u4f4e") ? "low" : "safe";
  const personaLabel = studentPersonaLabel(data, course, values, benchmark);

  $("studentSelectedCourse").textContent = warning.Course_Name || warning.Course_ID || "--";
  $("studentPersonaLabel").textContent = personaLabel;
  $("studentTotalTime").textContent = formatNumber(values.time, "h");
  $("studentCompletion").textContent = formatNumber(values.completion, "%");
  $("studentGrade").textContent = formatNumber(values.grade);
  $("studentQuizScore").textContent = formatNumber(values.score);
  $("studentVideoRate").textContent = formatNumber(values.video, "%");
  $("studentLearningDays").textContent = formatNumber(values.days, "\u5929");
  $("studentWarningLevel").textContent = level;
  $("studentDetailTitle").textContent = `${warning.Course_ID || ""} ${warning.Course_Name || ""}`.trim() || data.basic?.student_id || "--";
  $("studentCourseHint").textContent = `${(state.studentData?.courses || []).length}\u95e8\u8bfe`;
  if ($("studentPersonaHint")) $("studentPersonaHint").textContent = level;
  $("studentTimeHint").textContent = `\u73ed\u7ea7\u5747\u503c ${formatNumber(benchmark.time, "h")}`;
  $("studentCompletionHint").textContent = values.completion >= benchmark.completion ? "\u9ad8\u4e8e\u5747\u503c" : "\u4f4e\u4e8e\u5747\u503c";
  $("studentGradeHint").textContent = `\u63d0\u4ea4\u57fa\u51c6 ${formatNumber(benchmark.grade, "%")}`;
  $("studentQuizHint").textContent = `\u73ed\u7ea7\u5747\u5206 ${formatNumber(benchmark.score)}`;
  $("studentVideoHint").textContent = values.video >= benchmark.video ? "\u89c6\u9891\u8fbe\u6807" : "\u8fdb\u5ea6\u4e0d\u8db3";
  $("studentDaysHint").textContent = "\u8fd1\u671f\u6301\u7eed\u6027";
  $("studentRiskHint").textContent = advice.weakName;
  document.querySelector("#student .metric-card.warning")?.setAttribute("data-risk-tone", riskTone);

  renderStudentComparisonChart(values, benchmark, warning, personaLabel);
  renderStudentTagPie(state.studentData?.summaryRows || []);

  chart("studentRadar").setOption({
    tooltip: {
      trigger: "item",
      formatter(params) {
        const labels = ["\u5b66\u4e60\u65f6\u957f", "\u8bfe\u7a0b\u5b8c\u6210\u7387", "\u89c6\u9891\u5b8c\u8bfe", "\u4f5c\u4e1a\u6210\u7ee9", "\u6d4b\u9a8c\u5747\u5206"];
        return labels.map((label, index) => `${label}: ${formatNumber(params.value[index])}`).join("<br/>");
      },
    },
    legend: { top: 0 },
    radar: {
      center: ["50%", "56%"],
      radius: "82%",
      indicator: [
        { name: "\u5b66\u4e60\u65f6\u957f", max: 10 },
        { name: "\u8bfe\u7a0b\u5b8c\u6210\u7387", max: 100 },
        { name: "\u89c6\u9891\u5b8c\u8bfe", max: 100 },
        { name: "\u4f5c\u4e1a\u6210\u7ee9", max: 100 },
        { name: "\u6d4b\u9a8c\u5747\u5206", max: 100 },
      ],
    },
    series: [{
      type: "radar",
      data: [
        { name: "\u672c\u4eba", value: [values.time, values.completion, values.video, values.grade, values.score], areaStyle: { opacity: 0.18 }, lineStyle: { color: riskColor(level) }, itemStyle: { color: riskColor(level) } },
        { name: "\u73ed\u7ea7\u5e73\u5747", value: [benchmark.time, benchmark.completion, benchmark.video, benchmark.grade, benchmark.score], areaStyle: { opacity: 0.1, color: "rgba(91, 123, 255, 0.18)" }, lineStyle: { type: "dashed", width: 3, color: "#5b7bff" }, itemStyle: { color: "#5b7bff" } },
      ],
    }],
  });

  $("studentDetail").innerHTML = `
    <section>
      <h3>\u4e2a\u4eba\u57fa\u7840\u5b66\u60c5</h3>
      <dl class="detail-list compact">
        <dt>\u5b66\u53f7</dt><dd>${data.basic?.student_id || $("studentId").value || "--"}</dd>
        <dt>\u59d3\u540d</dt><dd>${data.basic?.student_name || "--"}</dd>
        <dt>\u5728\u8bfb\u5b66\u4f4d</dt><dd>${data.basic?.education_level || "--"}</dd>
        <dt>\u5f53\u524d\u8bfe\u7a0b</dt><dd>${warning.Course_Name || "--"}</dd>
      </dl>
    </section>
    <section>
      <h3>\u5b66\u4e60\u884c\u4e3a\u4e0e\u5b66\u4e1a\u6307\u6807</h3>
      <dl class="detail-list compact">
        <dt>\u603b\u65f6\u957f</dt><dd>${formatNumber(values.time, "h")}</dd>
        <dt>\u5355\u6b21\u65f6\u957f</dt><dd>${formatNumber(feature.avg_session_duration_min, "min")}</dd>
        <dt>\u8bfe\u7a0b\u8fdb\u5ea6</dt><dd>${formatNumber(values.completion, "%")}</dd>
        <dt>\u89c6\u9891\u5b8c\u64ad</dt><dd>${formatNumber(values.video, "%")}</dd>
        <dt>\u4f5c\u4e1a\u63d0\u4ea4</dt><dd>${formatNumber(warning.Assignment_Submission_Rate || values.grade, "%")}</dd>
        <dt>\u6d4b\u9a8c\u5747\u5206</dt><dd>${formatNumber(values.score)}</dd>
      </dl>
    </section>
    <section class="risk-advice ${riskTone}">
      <h3>\u98ce\u9669\u8bf4\u660e &amp; \u5b66\u4e60\u5efa\u8bae</h3>
      <p><strong>\u9884\u8b66\u7b49\u7ea7\uff1a${level}</strong></p>
      <p>\u98ce\u9669\u56e0\u5b50\uff1a${advice.reason}\uff0c\u5171 ${warning.risk_sum ?? "--"} \u9879\u9700\u5173\u6ce8\u3002</p>
      <p>\u5b66\u4e60\u5efa\u8bae\uff1a${advice.advice}</p>
    </section>
  `;
}

async function loadStudentPage() {
  const id = state.user?.role === "student" ? state.user.student_id || $("studentId").value.trim() : $("studentId").value.trim();
  if (id) $("studentId").value = id;
  if (!id) throw new Error("当前学生账号没有绑定 student_id，无法查询个人学习数据");
  const needsCourseRisk = !(state.cache.courseRisk || []).length;
  const data = await request(`/api/profiles/students/${encodeURIComponent(id)}`);
  const optionalRequests = [
    ["学生标签占比", request("/api/profiles/students/summary"), []],
    ["课程风险基准", needsCourseRisk ? request("/api/warnings/courses") : Promise.resolve(state.cache.courseRisk), state.cache.courseRisk || []],
  ];
  const optionalResults = await Promise.allSettled(optionalRequests.map(([, task]) => task));
  const [summary, courseRisk] = optionalResults.map((result, index) => {
    if (result.status === "fulfilled") return result.value;
    state.dataIssues.push(`${optionalRequests[index][0]}：${friendlyError(result.reason)}`);
    return optionalRequests[index][2];
  });
  state.cache.courseRisk = Array.isArray(courseRisk) ? courseRisk : [];
  state.studentData = { raw: data, courses: buildStudentCourses(data), summaryRows: Array.isArray(summary) ? summary : [] };
  renderStudentCourseOptions();
  renderStudentPage();
}

async function loadTeacherPage() {
  const id = state.user?.course_id || "C101";
  const [detail, risks] = await Promise.all([
    request(`/api/profiles/teachers/${encodeURIComponent(id)}`),
    request("/api/warnings/courses"),
  ]);
  const risk = risks.find((row) => row.Course_ID === detail.Course_ID) || {};
  const finishRate = percentFromRate(detail.course_finish_rate);
  const score = numberValue(detail.avg_quiz_score, risk.avg_quiz_score);
  const submitRate = numberValue(detail.avg_assignment_submit_rate, risk.avg_submit_rate);
  const progress = numberValue(detail.avg_student_progress, risk.avg_progress);
  const video = numberValue(detail.avg_video_completion, risk.avg_video_completion_rate);
  const courseType = pickTextValue(detail, ["\u6559\u5b66\u6548\u80fd\u8bc4\u7ea7"]);
  const advice = courseTypeAdvice[courseType] || "\u8bf7\u7ed3\u5408\u5b66\u751f\u5b8c\u6210\u7387\u3001\u4f5c\u4e1a\u63d0\u4ea4\u7387\u548c\u9884\u8b66\u5206\u5e03\u6301\u7eed\u4f18\u5316\u6559\u5b66\u3002";
  const zhName = courseNameZh[detail.Course_ID] || "";
  const peers = risks.length ? risks : state.cache.courseRisk || [];
  const platform = {
    score: peers.reduce((sum, row) => sum + numberValue(row.avg_quiz_score), 0) / Math.max(peers.length, 1),
    submit: peers.reduce((sum, row) => sum + numberValue(row.avg_submit_rate), 0) / Math.max(peers.length, 1),
    progress: peers.reduce((sum, row) => sum + numberValue(row.avg_progress), 0) / Math.max(peers.length, 1),
    video: peers.reduce((sum, row) => sum + numberValue(row.avg_video_completion_rate), 0) / Math.max(peers.length, 1),
    risk: peers.reduce((sum, row) => sum + numberValue(row.high_risk_pct), 0) / Math.max(peers.length, 1),
  };
  const rankByScore = [...peers].sort((a, b) => numberValue(b.avg_quiz_score) - numberValue(a.avg_quiz_score)).findIndex((row) => row.Course_ID === detail.Course_ID) + 1;
  const rankByRisk = [...peers].sort((a, b) => numberValue(a.high_risk_pct) - numberValue(b.high_risk_pct)).findIndex((row) => row.Course_ID === detail.Course_ID) + 1;
  const weakItems = [
    ["\u5e73\u5747\u5f97\u5206", score, platform.score],
    ["\u4f5c\u4e1a\u63d0\u4ea4", submitRate, platform.submit],
    ["\u8bfe\u7a0b\u8fdb\u5ea6", progress, platform.progress],
    ["\u89c6\u9891\u5b8c\u8bfe", video, platform.video],
  ].filter((item) => item[1] < item[2]).map((item) => item[0]);
  const teacherAdvice = weakItems.length
    ? `\u76f8\u6bd4\u5e73\u53f0\u5747\u503c\uff0c${weakItems.join("\u3001")}\u504f\u4f4e\uff0c\u5efa\u8bae\u9488\u5bf9\u8be5\u73af\u8282\u505a\u8865\u6559\u3001\u4f5c\u4e1a\u8ffd\u8e2a\u548c\u89c6\u9891\u5b66\u4e60\u63d0\u9192\u3002`
    : "\u5404\u9879\u6838\u5fc3\u6307\u6807\u5747\u4e0d\u4f4e\u4e8e\u5e73\u53f0\u5747\u503c\uff0c\u5efa\u8bae\u6c89\u6dc0\u6559\u5b66\u7ecf\u9a8c\u5e76\u5206\u4eab\u7ed9\u540c\u7c7b\u8bfe\u7a0b\u3002";

  $("teacherCourseCode").textContent = detail.Course_ID || id;
  $("teacherCourseNameEn").textContent = detail.Course_Name || "--";
  $("teacherCourseNameZh").textContent = zhName || detail.course_category || "";
  $("teacherCourseType").textContent = courseType;
  $("teacherCourseAdvice").textContent = advice;
  $("teacherStudentCount").textContent = formatNumber(detail.total_student_count || risk.student_count);
  $("teacherFinishRate").textContent = formatNumber(finishRate, "%");
  $("teacherAvgScore").textContent = formatNumber(score);
  $("teacherSubmitRate").textContent = formatNumber(submitRate, "%");
  $("teacherProgress").textContent = formatNumber(progress, "%");
  $("teacherVideoRate").textContent = formatNumber(video, "%");
  $("teacherSatisfaction").textContent = formatNumber(detail.avg_student_satisfaction);
  $("teacherHighRisk").textContent = formatNumber(risk.high_risk_pct, "%");
  $("teacherDetailTitle").textContent = `${detail.Course_ID} 路 ${detail.Course_Name}`;

  chart("teacherRadar").setOption({
    tooltip: { trigger: "item" },
    legend: { top: 0 },
    radar: {
      center: ["50%", "56%"],
      radius: "82%",
      indicator: [
        { name: "\u5b8c\u6210\u7387", max: 100 },
        { name: "\u5e73\u5747\u5f97\u5206", max: 100 },
        { name: "\u4f5c\u4e1a\u63d0\u4ea4", max: 100 },
        { name: "\u8bfe\u7a0b\u8fdb\u5ea6", max: 100 },
        { name: "\u89c6\u9891\u5b8c\u8bfe", max: 100 },
      ],
    },
    series: [{
      type: "radar",
      areaStyle: { opacity: 0.12 },
      data: [
        { name: "\u6240\u6388\u8bfe\u7a0b", value: [finishRate, score, submitRate, progress, video] },
        { name: "\u5e73\u53f0\u5747\u503c", value: [platform.progress, platform.score, platform.submit, platform.progress, platform.video], areaStyle: { opacity: 0.08, color: "rgba(255, 145, 77, 0.16)" }, lineStyle: { type: "dashed", width: 3, color: "#ff914d" }, itemStyle: { color: "#ff914d" } },
      ],
    }],
  });
  renderTeacherRiskPie(risk);

  $("teacherDetail").innerHTML = `
    <section>
      <h3>\u8bfe\u7a0b\u57fa\u7840\u4fe1\u606f</h3>
      <dl class="detail-list compact">
        <dt>\u8bfe\u7a0b</dt><dd>${detail.Course_Name || "--"}</dd>
        <dt>\u8bfe\u7a0b\u7c7b\u522b</dt><dd>${detail.course_category || "--"}</dd>
        <dt>\u8bfe\u7a0b\u7c7b\u578b</dt><dd>${courseType}</dd>
      </dl>
    </section>
    <section>
      <h3>\u5e73\u53f0\u5bf9\u6bd4\u8868\u73b0</h3>
      <dl class="detail-list compact">
        <dt>\u5f97\u5206\u6392\u540d</dt><dd>${rankByScore ? `${rankByScore} / ${peers.length}` : "--"}</dd>
        <dt>\u4f4e\u98ce\u9669\u6392\u540d</dt><dd>${rankByRisk ? `${rankByRisk} / ${peers.length}` : "--"}</dd>
        <dt>\u5e73\u53f0\u5747\u5206</dt><dd>${formatNumber(platform.score)}</dd>
        <dt>\u5e73\u53f0\u63d0\u4ea4</dt><dd>${formatNumber(platform.submit, "%")}</dd>
        <dt>\u5e73\u53f0\u5b8c\u8bfe</dt><dd>${formatNumber(platform.video, "%")}</dd>
        <dt>\u6559\u5b66\u6548\u80fd</dt><dd>${formatNumber(detail.teaching_effect_score)}</dd>
      </dl>
    </section>
    <section class="risk-advice ${numberValue(risk.high_risk_pct) > platform.risk ? "high" : "low"}">
      <h3>\u8bca\u65ad\u5efa\u8bae</h3>
      <p><strong>${advice}</strong></p>
      <p>${teacherAdvice}</p>
      <p>\u5b66\u751f\u603b\u6570 ${formatNumber(detail.total_student_count || risk.student_count)}\uff0c\u9ad8\u98ce\u9669 ${formatNumber(risk.high_risk_count)}\uff0c\u4e2d\u98ce\u9669 ${formatNumber(risk.mid_risk_count)}\uff0c\u5b89\u5168 ${formatNumber(risk.safe_count)}\u3002</p>
    </section>
  `;
  renderTeacherComparison(detail, peers, platform);
}

function renderTeacherRiskPie(risk) {
  const rows = [
    { name: "\u9ad8\u98ce\u9669", value: numberValue(risk.high_risk_count), color: "#d92d20" },
    { name: "\u4e2d\u98ce\u9669", value: numberValue(risk.mid_risk_count), color: "#f79009" },
    { name: "\u4f4e\u98ce\u9669", value: numberValue(risk.low_risk_count), color: "#12a594" },
    { name: "\u5b89\u5168", value: numberValue(risk.safe_count), color: "#1976d2" },
  ];
  chart("teacherRiskPie").setOption({
    tooltip: {
      trigger: "item",
      formatter: "{b}: {c} ({d}%)",
    },
    legend: {
      bottom: 0,
      type: "scroll",
      formatter(name) {
        const row = rows.find((item) => item.name === name);
        return `${name} ${formatNumber(row?.value)}`;
      },
    },
    series: [{
      type: "pie",
      radius: ["52%", "76%"],
      center: ["50%", "42%"],
      data: rows.map((row) => ({ name: row.name, value: row.value, itemStyle: { color: row.color } })),
      label: {
        show: false,
      },
      emphasis: { label: { show: true, formatter: "{b}\n{d}%" } },
    }],
  });
}

function renderTeacherComparison(detail, peers, platform) {
  const currentId = detail.Course_ID;
  const rows = [...peers].sort((a, b) => {
    if (a.Course_ID === currentId) return -1;
    if (b.Course_ID === currentId) return 1;
    return numberValue(b.avg_quiz_score) - numberValue(a.avg_quiz_score);
  });
  chart("teacherComparisonChart").setOption({
    tooltip: {
      trigger: "axis",
      formatter(items) {
        const row = rows[items[0]?.dataIndex] || {};
        return [
          `<strong>${row.Course_ID} ${row.Course_Name || ""}</strong>`,
          `\u9009\u8bfe\u4eba\u6570: ${formatNumber(row.student_count)}`,
          `\u5e73\u5747\u5206: ${formatNumber(row.avg_quiz_score)}`,
          `\u63d0\u4ea4\u7387: ${formatNumber(row.avg_submit_rate, "%")}`,
          `\u8fdb\u5ea6: ${formatNumber(row.avg_progress, "%")}`,
          `\u9ad8\u98ce\u9669: ${formatNumber(row.high_risk_pct, "%")}`,
        ].join("<br/>");
      },
    },
    legend: { top: 0 },
    grid: { left: 46, right: 44, top: 48, bottom: 46 },
    xAxis: {
      type: "category",
      data: rows.map((row) => row.Course_ID),
      axisLabel: {
        color(value) {
          return value === currentId ? "#1976d2" : "#667085";
        },
        fontWeight(value) {
          return value === currentId ? 800 : 400;
        },
      },
    },
    yAxis: [{ type: "value", name: "%" }, { type: "value", name: "\u4eba", position: "right" }],
    series: [
      { name: "\u5e73\u5747\u5206", type: "line", smooth: true, data: rows.map((row) => numberValue(row.avg_quiz_score)), markLine: { symbol: "none", lineStyle: { type: "dashed", color: "#98a2b3" }, data: [{ yAxis: platform.score, name: "\u5e73\u53f0\u5747\u5206" }] }, itemStyle: { color: "#1976d2" } },
      { name: "\u4f5c\u4e1a\u63d0\u4ea4", type: "line", smooth: true, data: rows.map((row) => numberValue(row.avg_submit_rate)), markLine: { symbol: "none", lineStyle: { type: "dashed", color: "#98a2b3" }, data: [{ yAxis: platform.submit, name: "\u5e73\u53f0\u63d0\u4ea4" }] }, itemStyle: { color: "#12a594" } },
      { name: "\u9ad8\u98ce\u9669\u7387", type: "line", smooth: true, data: rows.map((row) => numberValue(row.high_risk_pct)), markLine: { symbol: "none", lineStyle: { type: "dashed", color: "#d0d5dd" }, data: [{ yAxis: platform.risk, name: "\u5e73\u53f0\u98ce\u9669" }] }, itemStyle: { color: "#d92d20" } },
      { name: "\u9009\u8bfe\u4eba\u6570", type: "bar", yAxisIndex: 1, data: rows.map((row) => ({ value: numberValue(row.student_count), itemStyle: { color: row.Course_ID === currentId ? "#f79009" : "#c9d8e5" } })), barMaxWidth: 34 },
    ],
  });
}

async function loadAdminPage() {
  const [courses, education, warnings] = await Promise.all([
    request("/api/warnings/courses"),
    request("/api/warnings/education"),
    request("/api/warnings/students?page=1&page_size=20"),
  ]);
  state.cache.courseRisk = courses;
  state.cache.education = education;
  state.cache.warningRows = warnings;
  renderAdminRiskCards();
  renderCourseRiskStack();
  renderCoursePerformance();
  renderAdminEducationRisk();
  renderWarningTable();
  renderResourceHeat();
}

function adminCourseRows() {
  const course = document.getElementById("adminCourseFilter")?.value || "";
  const rows = state.cache.courseRisk || [];
  return course ? rows.filter((row) => row.Course_ID === course) : rows;
}

function renderAdminRiskCards() {
  const warnings = state.cache.warningDistribution || [];
  const courses = state.cache.courseRisk || [];
  const total = warnings.reduce((sum, row) => sum + numberValue(row.student_count), 0);
  const high = warnings.find((row) => String(row.warning_level).includes("\u9ad8")) || {};
  const avgCompletion = courses.length ? courses.reduce((sum, row) => sum + numberValue(row.avg_progress), 0) / courses.length : numberValue(state.cache.metrics?.avg_completion_rate);
  const avgQuiz = courses.length ? courses.reduce((sum, row) => sum + numberValue(row.avg_quiz_score), 0) / courses.length : 0;
  $("adminTotalStudents").textContent = formatNumber(total || state.cache.metrics?.student_count);
  $("adminHighRiskStudents").textContent = formatNumber(high.student_count);
  $("adminHighRiskRatio").textContent = formatNumber(high.risk_ratio_pct, "%");
  $("adminAvgCompletion").textContent = formatNumber(avgCompletion, "%");
  $("adminAvgQuiz").textContent = formatNumber(avgQuiz);
}

function courseRiskLegendName(name, rows) {
  const keyMap = {
    "\u9ad8\u98ce\u9669": "high_risk_count",
    "\u4e2d\u98ce\u9669": "mid_risk_count",
    "\u4f4e\u98ce\u9669": "low_risk_count",
    "\u5b89\u5168": "safe_count",
  };
  const total = rows.reduce((sum, row) => sum + numberValue(row[keyMap[name]]), 0);
  return `${name} (${formatNumber(total)})`;
}

function renderCourseRiskStack() {
  const rows = adminCourseRows().sort((a, b) => {
    if (state.riskSort === "high") return numberValue(b.high_risk_count) - numberValue(a.high_risk_count);
    if (state.riskSort === "mid") return numberValue(b.mid_risk_count) - numberValue(a.mid_risk_count);
    if (state.riskSort === "low") return numberValue(b.low_risk_count) - numberValue(a.low_risk_count);
    if (state.riskSort === "safe") return numberValue(b.safe_count) - numberValue(a.safe_count);
    return numberValue(b.student_count) - numberValue(a.student_count);
  });
  const names = ["\u9ad8\u98ce\u9669", "\u4e2d\u98ce\u9669", "\u4f4e\u98ce\u9669", "\u5b89\u5168"];
  chart("courseRiskStackChart").setOption({
    tooltip: {
      trigger: "axis",
      formatter(items) {
        const row = rows[items[0]?.dataIndex] || {};
        const riskLines = items.map((item) => `${item.marker}${item.seriesName}: ${formatNumber(item.value)}`);
        return [
          `<strong>${row.Course_ID} ${row.Course_Name || ""}</strong>`,
          `\u603b\u9009\u8bfe\u4eba\u6570: ${formatNumber(row.student_count)}`,
          ...riskLines,
          `\u5e73\u5747\u5206: ${formatNumber(row.avg_quiz_score)}`,
          `\u4f5c\u4e1a\u63d0\u4ea4\u7387: ${formatNumber(row.avg_submit_rate, "%")}`,
          `\u5e73\u5747\u8fdb\u5ea6: ${formatNumber(row.avg_progress, "%")}`,
        ].join("<br/>");
      },
    },
    legend: { top: 0, formatter: (name) => courseRiskLegendName(name, rows) },
    grid: { left: 48, right: 18, top: 44, bottom: 54 },
    xAxis: { type: "category", data: rows.map((row) => row.Course_ID) },
    yAxis: { type: "value" },
    series: [
      { name: names[0], type: "bar", stack: "risk", data: rows.map((row) => numberValue(row.high_risk_count)), itemStyle: { color: "#d92d20" } },
      { name: names[1], type: "bar", stack: "risk", data: rows.map((row) => numberValue(row.mid_risk_count)), itemStyle: { color: "#f79009" } },
      { name: names[2], type: "bar", stack: "risk", data: rows.map((row) => numberValue(row.low_risk_count)), itemStyle: { color: "#12a594" } },
      { name: names[3], type: "bar", stack: "risk", data: rows.map((row) => numberValue(row.safe_count)), itemStyle: { color: "#1976d2" }, label: { show: true, position: "top", formatter(params) { return formatNumber(rows[params.dataIndex]?.student_count); } } },
    ],
  });
  chart("courseRiskStackChart").off("click");
  chart("courseRiskStackChart").on("click", (params) => {
    const row = rows[params.dataIndex];
    if (!row) return;
    document.getElementById("adminCourseFilter").value = row.Course_ID;
    if (params.seriesName.includes("\u9ad8")) document.getElementById("tableRiskFilter").value = "\u9ad8\u98ce\u9669";
    renderCourseRiskStack();
    renderWarningTable();
  });
}

function renderCoursePerformance() {
  const courses = state.cache.courseRisk || [];
  const avgScore = courses.reduce((sum, row) => sum + numberValue(row.avg_quiz_score), 0) / Math.max(courses.length, 1);
  const avgSubmit = courses.reduce((sum, row) => sum + numberValue(row.avg_submit_rate), 0) / Math.max(courses.length, 1);
  const avgProgress = courses.reduce((sum, row) => sum + numberValue(row.avg_progress), 0) / Math.max(courses.length, 1);
  const series = [
    { name: "\u6d4b\u9a8c\u5206", type: "line", smooth: true, data: courses.map((row) => numberValue(row.avg_quiz_score)), markLine: { symbol: "none", lineStyle: { type: "dashed", color: "#98a2b3" }, data: [{ yAxis: avgScore, name: "\u5747\u503c" }] } },
    { name: "\u63d0\u4ea4\u7387", type: "line", smooth: true, data: courses.map((row) => numberValue(row.avg_submit_rate)), markLine: { symbol: "none", lineStyle: { type: "dashed", color: "#98a2b3" }, data: [{ yAxis: avgSubmit, name: "\u5747\u503c" }] } },
    { name: "\u8fdb\u5ea6", type: "line", smooth: true, data: courses.map((row) => numberValue(row.avg_progress)), markLine: { symbol: "none", lineStyle: { type: "dashed", color: "#98a2b3" }, data: [{ yAxis: avgProgress, name: "\u5747\u503c" }] } },
  ];
  if (state.performanceExtra === "video") series.push({ name: "\u89c6\u9891\u5b8c\u64ad", type: "line", smooth: true, data: courses.map((row) => numberValue(row.avg_video_completion_rate)) });
  if (state.performanceExtra === "session") series.push({ name: "\u5355\u6b21\u65f6\u957f", type: "line", smooth: true, data: courses.map((row) => numberValue(row.avg_session_duration_min, row.avg_study_time_hours)) });
  chart("coursePerformanceChart").setOption({
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { left: 42, right: 18, top: 44, bottom: 54 },
    xAxis: { type: "category", data: courses.map((row) => row.Course_ID) },
    yAxis: { type: "value", max: 100 },
    series,
  });
}

function renderAdminEducationRisk() {
  const rows = (state.cache.education || []).map((row) => ({
    ...row,
    study_hours: numberValue(row.avg_total_study_hours, row.avg_total_study_time_hours),
    score_value: numberValue(row.avg_quiz_score, row.avg_score, row.quiz_score_avg),
    ratio_value: numberValue(row.ratio_pct, row.ratio_percent, row.student_ratio_pct),
    high_risk_value: numberValue(row.high_risk_pct, row.high_risk_ratio, row.high_risk_percent),
    safe_value: numberValue(row.safe_pct, row.safe_ratio, row.safe_percent),
  }));
  const barKey = state.adminDegreeBar === "score" ? "score_value" : state.adminDegreeBar === "study" ? "study_hours" : "ratio_value";
  const barName = state.adminDegreeBar === "score" ? "平均测验分" : state.adminDegreeBar === "study" ? "平均学习时长" : "人数占比";
  const barUnit = state.adminDegreeBar === "study" ? "h" : state.adminDegreeBar === "ratio" ? "%" : "";
  chart("educationRiskChart").setOption({
    tooltip: {
      trigger: "axis",
      formatter(items) {
        const row = rows[items[0]?.dataIndex] || {};
        return [
          `<strong>${row.Education_Level || '--'}</strong>`,
          `${items[0]?.marker || ''}${barName}: ${formatNumber(row[barKey], barUnit)}`,
          `${items[1]?.marker || ''}高风险占比: ${formatNumber(row.high_risk_value, '%')}`,
          `${items[2]?.marker || ''}安全占比: ${formatNumber(row.safe_value, '%')}`,
          `平均学习时长: ${formatNumber(row.study_hours, 'h')}`,
          `平均测验分: ${formatNumber(row.score_value)}`,
          `人数占比: ${formatNumber(row.ratio_value, '%')}`,
        ].join('<br/>');
      },
    },
    legend: { top: 0 },
    grid: { left: 54, right: 68, top: 44, bottom: 42, containLabel: true },
    xAxis: { type: "category", data: rows.map((row) => row.Education_Level) },
    yAxis: [
      { type: "value", name: barName, axisLabel: { formatter: (value) => state.adminDegreeBar === 'study' ? `${value}h` : state.adminDegreeBar === 'ratio' ? `${value}%` : value } },
      { type: "value", name: "风险%", axisLabel: { formatter: '{value}%' } },
    ],
    series: [
      { name: barName, type: "bar", barWidth: 34, z: 3, data: rows.map((row) => row[barKey]), label: { show: true, position: "top", formatter: (params) => state.adminDegreeBar === "study" ? `${params.value}h` : state.adminDegreeBar === "ratio" ? `${params.value}%` : params.value }, itemStyle: { color: "#1976d2" } },
      { name: "高风险占比", type: "line", yAxisIndex: 1, smooth: true, data: rows.map((row) => row.high_risk_value), label: { show: true, position: "top", distance: 6, formatter: "{c}%" }, itemStyle: { color: "#d92d20" } },
      { name: "安全占比", type: "line", yAxisIndex: 1, smooth: true, data: rows.map((row) => row.safe_value), label: { show: true, position: "bottom", distance: 6, formatter: "{c}%" }, itemStyle: { color: "#12a594" } },
    ],
  });
  chart("educationRiskChart").off("click");
  chart("educationRiskChart").on("click", () => {
    document.getElementById("tableRiskFilter").value = "高风险";
    renderWarningTable();
  });
}

function warningTableRows() {
  const keyword = document.getElementById("studentKeyword")?.value.trim() || "";
  const courseKeyword = document.getElementById("courseKeyword")?.value.trim() || "";
  const risk = document.getElementById("tableRiskFilter")?.value || "";
  const course = document.getElementById("adminCourseFilter")?.value || "";
  const source = warningRowsSource();
  return source.filter((row) => {
    if (keyword && !String(row.Student_ID).includes(keyword)) return false;
    if (courseKeyword && !String(row.Course_ID + row.Course_Name).includes(courseKeyword)) return false;
    if (risk && row.warning_level !== risk) return false;
    if (course && row.Course_ID !== course) return false;
    return true;
  });
}

function warningRowsSource() {
  return Array.isArray(state.cache.warningRows) ? state.cache.warningRows : state.cache.warningRows?.rows || [];
}

function renderWarningTable() {
  const rows = warningTableRows();
  const pageSize = state.pageSize;
  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  state.warningPage = Math.min(state.warningPage, pageCount);
  const pageRows = rows.slice((state.warningPage - 1) * pageSize, state.warningPage * pageSize);
  const totalStudents = numberValue(state.cache.metrics?.student_count, state.cache.warningDistribution?.reduce((sum, row) => sum + numberValue(row.student_count), 0));
  $("riskTableSummary").textContent = `\u5f53\u524d\u7b5b\u9009 ${rows.length} \u540d\uff0c\u5360\u603b\u4eba\u6570 ${formatNumber(totalStudents ? rows.length / totalStudents * 100 : 0, "%")}`;
  $("pageInfo").textContent = `${state.warningPage} / ${pageCount}`;
  $("warningRows").innerHTML = pageRows.map((row) => `
    <tr>
      <td><input class="warning-check" type="checkbox" data-id="${row.Student_ID}" ${state.selectedWarnings.has(row.Student_ID) ? "checked" : ""} /></td>
      <td>${row.Student_ID}</td>
      <td>${row.Course_ID}</td>
      <td class="${String(row.warning_level).includes("\u9ad8") ? "risk-high" : ""}">${row.warning_level}</td>
      <td class="${numberValue(row.Progress_Percentage) < 40 ? "progress-low" : ""}">${formatNumber(row.Progress_Percentage, "%")}</td>
      <td>
        <button class="mini-button" data-profile="${row.Student_ID}">\u753b\u50cf</button>
        <button class="mini-button" data-report="${row.Student_ID}">\u62a5\u544a</button>
      </td>
    </tr>
  `).join("");
  document.querySelectorAll(".warning-check").forEach((item) => {
    item.addEventListener("change", () => {
      if (item.checked) state.selectedWarnings.add(item.dataset.id);
      else state.selectedWarnings.delete(item.dataset.id);
    });
  });
  document.querySelectorAll("[data-profile]").forEach((button) => button.addEventListener("click", () => openStudentProfile(button.dataset.profile)));
  document.querySelectorAll("[data-report]").forEach((button) => button.addEventListener("click", () => exportSingleStudent(button.dataset.report)));
}

function renderResourceHeat() {
  const rows = [...(state.cache.resources || [])]
    .sort((a, b) => numberValue(b.access_volume) - numberValue(a.access_volume))
    .reverse();
  chart("resourceHeatChart").setOption({
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { left: 230, right: 28, top: 44, bottom: 28 },
    xAxis: { type: "value" },
    yAxis: {
      type: "category",
      data: rows.map((row) => row.resource_name || row.resource_id),
      axisLabel: {
        width: 210,
        overflow: "truncate",
      },
    },
    series: [
      { name: "\u8bbf\u95ee\u91cf", type: "bar", data: rows.map((row) => numberValue(row.access_volume)), itemStyle: { color: "#1976d2" } },
      { name: "\u91cd\u590d\u89c2\u770b", type: "bar", data: rows.map((row) => numberValue(row.total_rewatch_count)), itemStyle: { color: "#12a594" } },
    ],
  });
  chart("resourceHeatChart").off("click");
  chart("resourceHeatChart").on("click", (params) => {
    const row = rows[params.dataIndex];
    if (row?.resource_id) {
      document.getElementById("adminCourseFilter").value = row.resource_id;
      renderCourseRiskStack();
      renderWarningTable();
    }
  });
}

function openModal(title, html) {
  $("modalTitle").textContent = title;
  $("modalBody").innerHTML = html;
  $("drillModal").classList.remove("hidden");
}

function closeModal() {
  $("drillModal").classList.add("hidden");
}

async function openStudentDrilldown() {
  if (currentRole() !== "admin") return;
  const rows = warningRowsSource().length ? warningRowsSource() : await request("/api/warnings/students?page=1&page_size=50");
  state.cache.warningRows = rows;
  openModal("\u5168\u91cf\u5b66\u751f\u5206\u9875\u5217\u8868\uff08\u793a\u4f8b\uff09", tableHtml(Array.isArray(rows) ? rows : rows.rows || [], ["Student_ID", "Course_ID", "warning_level", "Progress_Percentage"]));
}

async function openRiskDrilldown(level) {
  if (currentRole() !== "admin") return;
  const rows = await request(`/api/warnings/students?warning_level=${encodeURIComponent(level)}&page=1&page_size=50`).catch(() => filteredWarnings(warningRowsSource()).filter((row) => row.warning_level === level));
  state.cache.warningRows = rows;
  const list = (Array.isArray(rows) ? rows : rows.rows || []).map((row) => {
    const detail = warningRuleDetail(row);
    return {
      ...row,
      warning_level: row.warning_level || detail.warningLevel,
      risk_sum: row.risk_sum ?? detail.riskSum,
      total_rule_judgement: detail.ruleSummary,
      four_rule_metrics: detail.ruleDetail,
      login_rule: detail.loginRisk ? '登录风险' : '登录正常',
      assignment_rule: detail.assignmentRisk ? '作业风险' : '作业正常',
      progress_rule: detail.progressRisk ? '进度风险' : '进度正常',
      score_rule: detail.scoreRisk ? '成绩风险' : '成绩正常',
    };
  });
  openModal(`${level} 学生明细`, tableHtml(list, ["Student_ID", "Course_ID", "Course_Name", "warning_level", "risk_sum", "login_rule", "assignment_rule", "progress_rule", "score_rule", "Progress_Percentage"]));
}

function tableHtml(rows, keys) {
  return `
    <table>
      <thead><tr>${keys.map((key) => `<th>${key}</th>`).join("")}</tr></thead>
      <tbody>
        ${rows.map((row) => `<tr>${keys.map((key) => `<td>${row[key] ?? "--"}</td>`).join("")}</tr>`).join("")}
      </tbody>
    </table>
  `;
}

function exportReport() {
  if (currentRole() !== "admin") return;
  const sheets = [
    ["overview_metrics", [state.cache.metrics || {}]],
    ["weekly_learning_statistics", state.cache.weekly || []],
    ["course_enrollment_ranking", state.cache.enrollment || []],
    ["warning_level_summary", state.cache.warningDistribution || []],
    ["course_risk_summary", state.cache.courseRisk || []],
    ["education_risk_summary", state.cache.education || []],
    ["student_warning_detail", warningRowsSource()],
  ];
  const html = `
    <html><head><meta charset="UTF-8"></head><body>
      ${sheets.map(([name, rows]) => `<h2>${name}</h2>${tableHtml(rows, Object.keys(rows[0] || { empty: "" }))}`).join("<br/>")}
    </body></html>
  `;
  const blob = new Blob([html], { type: "application/vnd.ms-excel;charset=utf-8" });
  downloadBlob(blob, `learning-report-${Date.now()}.xls`);
}

function exportTrendRange() {
  if (currentRole() !== "admin") return;
  const rows = state.trendMode === "daily" ? weeklyAsDaily(state.cache.weekly || []).slice(-28) : state.cache.weekly || [];
  const csv = toCsv(rows);
  downloadBlob(new Blob([csv], { type: "text/csv;charset=utf-8" }), `trend-${state.trendMode}-${Date.now()}.csv`);
}

function toCsv(rows) {
  const keys = Object.keys(rows[0] || {});
  return [keys.join(","), ...rows.map((row) => keys.map((key) => `"${String(row[key] ?? "").replace(/"/g, '""')}"`).join(","))].join("\n");
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

async function openStudentProfile(studentId) {
  const data = await request(`/api/profiles/students/${encodeURIComponent(studentId)}`).catch(() => null);
  if (!data) {
    openModal("\u5b66\u751f\u753b\u50cf", `\u6682\u65e0 ${studentId} \u7684\u753b\u50cf\u6570\u636e`);
    return;
  }
  const basic = data.basic || {};
  const feature = data.feature || {};
  const warning = data.warning || {};
  const profile = data.profile || {};
  openModal(`${studentId} \u5b66\u751f\u753b\u50cf`, `
    <div class="profile-grid">
      <article>
        <h3>\u57fa\u672c\u4fe1\u606f</h3>
        <dl class="detail-list compact">
          <dt>\u5b66\u53f7</dt><dd>${basic.student_id || studentId}</dd>
          <dt>\u59d3\u540d</dt><dd>${basic.student_name || "--"}</dd>
          <dt>\u6027\u522b</dt><dd>${basic.gender || "--"}</dd>
          <dt>\u5e74\u9f84</dt><dd>${basic.age ?? "--"}</dd>
          <dt>\u5b66\u5386</dt><dd>${basic.education_level || "--"}</dd>
          <dt>\u57ce\u5e02</dt><dd>${basic.city || "--"}</dd>
          <dt>\u8bbe\u5907</dt><dd>${basic.device_type || "--"}</dd>
        </dl>
      </article>
      <article>
        <h3>\u6240\u9009\u8bfe\u7a0b</h3>
        <dl class="detail-list compact">
          <dt>\u8bfe\u7a0b\u7f16\u53f7</dt><dd>${warning.Course_ID || "--"}</dd>
          <dt>\u8bfe\u7a0b\u540d\u79f0</dt><dd>${warning.Course_Name || "--"}</dd>
          <dt>\u603b\u5b66\u4e60\u65f6\u957f</dt><dd>${formatNumber(feature.total_study_time_hours, "h")}</dd>
          <dt>\u5b8c\u6210\u7387</dt><dd>${formatNumber(feature.completion_rate, "%")}</dd>
          <dt>\u8bfe\u7a0b\u8fdb\u5ea6</dt><dd>${formatNumber(feature.avg_progress_percentage || warning.Progress_Percentage, "%")}</dd>
          <dt>\u89c6\u9891\u5b8c\u8bfe\u7387</dt><dd>${formatNumber(feature.avg_video_completion_rate || warning.Video_Completion_Rate, "%")}</dd>
        </dl>
      </article>
      <article>
        <h3>\u6210\u7ee9\u4e0e\u4e92\u52a8</h3>
        <dl class="detail-list compact">
          <dt>\u6d4b\u9a8c\u5e73\u5747\u5206</dt><dd>${formatNumber(feature.avg_quiz_score || warning.Quiz_Score_Avg)}</dd>
          <dt>\u9879\u76ee\u6210\u7ee9</dt><dd>${formatNumber(feature.avg_project_grade)}</dd>
          <dt>\u4f5c\u4e1a\u63d0\u4ea4\u7387</dt><dd>${formatNumber(warning.Assignment_Submission_Rate, "%")}</dd>
          <dt>\u8ba8\u8bba\u53c2\u4e0e</dt><dd>${formatNumber(feature.avg_discussion_participation)}</dd>
          <dt>\u540c\u4f34\u4e92\u52a8</dt><dd>${formatNumber(feature.avg_peer_interaction_score)}</dd>
          <dt>\u7f3a\u4ea4\u4f5c\u4e1a</dt><dd>${feature.total_assignments_missed ?? "--"}</dd>
        </dl>
      </article>
      <article>
        <h3>\u98ce\u9669\u9884\u8b66</h3>
        <dl class="detail-list compact">
          <dt>\u9884\u8b66\u7b49\u7ea7</dt><dd class="${String(warning.warning_level).includes("\u9ad8") ? "risk-high" : ""}">${warning.warning_level || "--"}</dd>
          <dt>\u98ce\u9669\u56e0\u5b50\u6570</dt><dd>${warning.risk_sum ?? "--"}</dd>
          <dt>\u6700\u8fd1\u767b\u5f55\u95f4\u9694</dt><dd>${formatNumber(profile.avg_days_since_login, "\u5929")}</dd>
          <dt>\u767b\u5f55\u9891\u7387</dt><dd>${formatNumber(profile.login_freq || feature.avg_login_frequency)}</dd>
        </dl>
      </article>
    </div>
  `);
}

function exportSingleStudent(studentId) {
  const rows = warningRowsSource().filter((row) => row.Student_ID === studentId);
  downloadBlob(new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" }), `${studentId}-learning-report.csv`);
}

function exportStudentReport() {
  const data = state.studentData?.raw || {};
  const course = currentStudentCourse();
  const feature = course.feature || {};
  const warning = course.warning || {};
  const benchmark = benchmarkForCourse(course);
  const values = {
    student_id: data.basic?.student_id || $("studentId").value || "--",
    student_name: data.basic?.student_name || "--",
    education_level: data.basic?.education_level || "--",
    course_id: warning.Course_ID || "--",
    course_name: warning.Course_Name || "--",
    total_study_time_hours: numberValue(feature.total_study_time_hours, data.profile?.total_duration),
    class_avg_study_time_hours: benchmark.time,
    completion_rate: numberValue(feature.completion_rate, feature.avg_progress_percentage, warning.Progress_Percentage),
    video_completion_rate: numberValue(feature.avg_video_completion_rate, warning.Video_Completion_Rate),
    assignment_submission_rate: numberValue(warning.Assignment_Submission_Rate, feature.avg_project_grade),
    avg_quiz_score: numberValue(feature.avg_quiz_score, warning.Quiz_Score_Avg),
    warning_level: warning.warning_level || "--",
    risk_sum: warning.risk_sum ?? "--",
  };
  downloadBlob(new Blob([toCsv([values])], { type: "text/csv;charset=utf-8" }), `${values.student_id}-${values.course_id}-learning-report.csv`);
}


function exportSelectedWarnings() {
  const rows = warningRowsSource().filter((row) => state.selectedWarnings.has(row.Student_ID));
  downloadBlob(new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" }), `selected-high-risk-${Date.now()}.csv`);
}


function renderDetail(targetId, fields) {
  $(targetId).innerHTML = fields.map(([label, value]) => `<dt>${label}</dt><dd>${value ?? "--"}</dd>`).join("");
}

async function loadAll() {
  if (!state.token) {
    setStatus(text.loginFirst, true);
    return;
  }
  setStatus(text.loading);
  state.dataIssues = [];
  const tasks = [];
  if (isAllowed("overview")) tasks.push(["学情总览", loadOverview()]);
  if (isAllowed("student")) tasks.push(["我的学习", loadStudentPage()]);
  if (isAllowed("teacher")) tasks.push(["教师画像", loadTeacherPage()]);
  if (isAllowed("admin")) tasks.push(["管理分析", loadAdminPage()]);
  const results = await Promise.allSettled(tasks.map(([, task]) => task));
  const failed = results
    .map((result, index) => result.status === "rejected" ? `${tasks[index][0]}：${friendlyError(result.reason)}` : "")
    .filter(Boolean);
  const messages = [...failed, ...state.dataIssues];
  setStatus(messages.length ? messages.join("；") : text.updated, Boolean(messages.length));
  resizeCharts();
}

function bindEvents() {
  $("logoutBtn").addEventListener("click", () => {
    state.token = "";
    state.user = null;
    localStorage.removeItem("visual_token");
    localStorage.removeItem("visual_user");
    window.location.href = "./login.html";
  });
  $("userMenuBtn").addEventListener("click", () => $("userPopover").classList.toggle("hidden"));
  if ($("refreshBtn")) {
    $("refreshBtn").addEventListener("click", () => {
      loadAll().catch((error) => setStatus(friendlyError(error), true));
    });
  }
  $("exportReportBtn").addEventListener("click", exportReport);
  $("exportCourseRiskBtn").addEventListener("click", () => downloadBlob(new Blob([toCsv(state.cache.courseRisk || [])], { type: "text/csv;charset=utf-8" }), `course-risk-${Date.now()}.csv`));
  $("exportHighRiskBtn").addEventListener("click", () => {
    const rows = warningRowsSource().filter((row) => String(row.warning_level).includes("\u9ad8"));
    downloadBlob(new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" }), `high-risk-students-${Date.now()}.csv`);
  });
  $("exportTrendBtn").addEventListener("click", exportTrendRange);
  $("modalCloseBtn").addEventListener("click", closeModal);
  $("drillModal").addEventListener("click", (event) => {
    if (event.target.id === "drillModal") closeModal();
  });
  $("degreeFilter").addEventListener("change", () => {
    renderDegreeChart();
    if (currentRole() === "admin" && state.cache.warningRows) loadAdminPage().catch((error) => setStatus(friendlyError(error), true));
  });
  ["adminCourseFilter"].forEach((id) => {
    const element = document.getElementById(id);
    if (!element) return;
    element.addEventListener("change", () => {
      renderCourseRiskStack();
      renderWarningTable();
    });
  });
  if (document.getElementById("riskFilter")) {
    $("riskFilter").addEventListener("change", () => {
      if (currentRole() === "admin" && state.cache.warningRows) {
        $("warningRows").innerHTML = filteredWarnings().map((row) => `
          <tr>
            <td>${row.Student_ID}</td>
            <td>${row.Course_ID}</td>
            <td>${row.warning_level}</td>
            <td>${formatNumber(row.Progress_Percentage, "%")}</td>
          </tr>
        `).join("");
      }
    });
  }
  $("loadStudentBtn").addEventListener("click", () => loadStudentPage().catch((error) => setStatus(friendlyError(error), true)));
  if ($("studentCourseSelect")) {
    $("studentCourseSelect").addEventListener("change", () => {
      state.selectedStudentCourse = $("studentCourseSelect").value;
      renderStudentPage();
    });
  }
  $("exportStudentReportBtn").addEventListener("click", exportStudentReport);
  if ($("loadTeacherBtn")) $("loadTeacherBtn").addEventListener("click", () => loadTeacherPage().catch((error) => setStatus(friendlyError(error), true)));
  document.querySelectorAll("[data-trend-mode]").forEach((button) => {
    button.addEventListener("click", () => {
      state.trendMode = button.dataset.trendMode;
      document.querySelectorAll("[data-trend-mode]").forEach((item) => item.classList.toggle("active", item === button));
      renderTrendChart();
    });
  });
  document.querySelectorAll("[data-course-sort]").forEach((button) => {
    button.addEventListener("click", () => {
      state.courseSort = button.dataset.courseSort;
      document.querySelectorAll("[data-course-sort]").forEach((item) => item.classList.toggle("active", item === button));
      renderEnrollmentChart();
    });
  });
  document.querySelectorAll("[data-degree-metric]").forEach((button) => {
    button.addEventListener("click", () => {
      state.degreeMetric = button.dataset.degreeMetric;
      document.querySelectorAll("[data-degree-metric]").forEach((item) => item.classList.toggle("active", item === button));
      renderDegreeChart();
    });
  });
  document.querySelectorAll("[data-risk-sort]").forEach((button) => {
    button.addEventListener("click", () => {
      state.riskSort = button.dataset.riskSort;
      document.querySelectorAll("[data-risk-sort]").forEach((item) => item.classList.toggle("active", item === button));
      const adminRiskSortSelect = document.getElementById("adminRiskSortSelect");
      if (adminRiskSortSelect && state.riskSort === "total") adminRiskSortSelect.value = "high";
      renderCourseRiskStack();
    });
  });
  const adminRiskSortSelect = document.getElementById("adminRiskSortSelect");
  if (adminRiskSortSelect) {
    adminRiskSortSelect.addEventListener("change", () => {
      state.riskSort = adminRiskSortSelect.value;
      document.querySelectorAll("[data-risk-sort]").forEach((item) => item.classList.remove("active"));
      renderCourseRiskStack();
    });
  }
  document.querySelectorAll("[data-performance-extra]").forEach((button) => {
    button.addEventListener("click", () => {
      state.performanceExtra = button.dataset.performanceExtra;
      document.querySelectorAll("[data-performance-extra]").forEach((item) => item.classList.toggle("active", item === button));
      renderCoursePerformance();
    });
  });
  document.querySelectorAll("[data-admin-degree-bar]").forEach((button) => {
    button.addEventListener("click", () => {
      state.adminDegreeBar = button.dataset.adminDegreeBar;
      document.querySelectorAll("[data-admin-degree-bar]").forEach((item) => item.classList.toggle("active", item === button));
      renderAdminEducationRisk();
    });
  });
  ["studentKeyword", "courseKeyword", "tableRiskFilter"].forEach((id) => {
    document.getElementById(id)?.addEventListener("input", () => {
      state.warningPage = 1;
      renderWarningTable();
    });
    document.getElementById(id)?.addEventListener("change", () => {
      state.warningPage = 1;
      renderWarningTable();
    });
  });
  $("pageSizeSelect").addEventListener("change", () => {
    state.pageSize = Number($("pageSizeSelect").value);
    state.warningPage = 1;
    renderWarningTable();
  });
  $("prevPageBtn").addEventListener("click", () => {
    state.warningPage = Math.max(1, state.warningPage - 1);
    renderWarningTable();
  });
  $("nextPageBtn").addEventListener("click", () => {
    state.warningPage += 1;
    renderWarningTable();
  });
  $("selectAllWarnings").addEventListener("change", () => {
    document.querySelectorAll(".warning-check").forEach((item) => {
      item.checked = $("selectAllWarnings").checked;
      if (item.checked) state.selectedWarnings.add(item.dataset.id);
      else state.selectedWarnings.delete(item.dataset.id);
    });
  });
  $("batchExportBtn").addEventListener("click", exportSelectedWarnings);
  document.querySelectorAll("[data-drill]").forEach((card) => {
    card.addEventListener("click", () => {
      if (currentRole() !== "admin") return;
      if (card.dataset.drill === "students") openStudentDrilldown().catch((error) => setStatus(friendlyError(error), true));
      if (card.dataset.drill === "study-hours") {
        state.trendMode = state.trendMode === "weekly" ? "daily" : "weekly";
        document.querySelectorAll("[data-trend-mode]").forEach((item) => item.classList.toggle("active", item.dataset.trendMode === state.trendMode));
        renderTrendChart();
      }
    });
  });
  document.querySelectorAll("[data-admin-focus]").forEach((card) => {
    card.addEventListener("click", () => {
      if (currentRole() !== "admin") return;
      if (card.dataset.adminFocus === "high-risk") {
        document.getElementById("tableRiskFilter").value = "\u9ad8\u98ce\u9669";
        showSection("admin");
        renderWarningTable();
      }
      if (card.dataset.adminFocus === "all-students") {
        document.getElementById("tableRiskFilter").value = "";
        showSection("admin");
        renderWarningTable();
      }
    });
  });
  document.querySelectorAll("[data-section-link]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      showSection(link.dataset.sectionLink);
    });
  });
  window.addEventListener("resize", resizeCharts);
}

bindEvents();
setStatus(text.preview);
applyRoleView();

if (!state.token) {
  window.location.href = "./login.html";
} else {
  loadAll().catch((error) => setStatus(friendlyError(error), true));
}





















