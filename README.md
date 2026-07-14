# 在线教学数据可视化前端

这是一个零构建静态前端，直接对接当前 Flask 后端。

## 使用方式

1. 先启动后端：

```bash
python app.py
```

当前前端默认后端地址：

```txt
https://comma-outgrow-breach.ngrok-free.dev
```

本地后端默认地址：

```txt
http://127.0.0.1:5000
```

2. 用浏览器打开：

```txt
frontend/index.html
```

3. 默认测试账号：

```txt
admin01 / admin123
```

登录成功后会自动加载后端真实数据。如果后端没有返回对应数据，页面会直接报错或显示空态，不会自动切换到模拟数据。

## 已接入页面

- 数据大屏：指标卡、周学习趋势、课程报名排行、预警等级分布、课程风险
- 资源效能：资源使用率图表、资源表格
- 学生画像：人群标签分布、单学生详情查询
- 教师画像：教学效能分布、课程详情查询
- 预警分析：学历风险、学生预警明细

## 注意事项

- 页面使用 ECharts CDN：`https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js`
- 所有接口请求都会自动带上 `Authorization: Bearer <token>`
- 如果页面提示无法连接，请先确认 Flask 后端是否已经启动
- 页面不提供模拟数据兜底，所有内容都依赖后端接口
