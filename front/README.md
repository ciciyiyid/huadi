部署数据库的方法（要先配置mysql环境）：
进入项目路径：

cd huadi

进入 MySQL：

mysql -u root -p

执行：

mysql -u root -p < sql/mysql/online_learning_db.sql

最后验证：

USE online_learning_db;

SHOW TABLES;

如果能看到所有统计表，就说明数据库部署成功。
