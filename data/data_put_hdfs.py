from hdfs import InsecureClient
import os

# ===========================
# HDFS连接
# ===========================
client = InsecureClient(
    "http://192.168.75.129:9870",
    user="huadi"
)

print(client)

LOCAL_FILE = r"E:\huadifinalproject\data\processed\cleaned_online_learning.csv"

# ===========================
# HDFS目录
# ===========================
HDFS_DIR = "/project/online_learning/ods"

filename = os.path.basename(LOCAL_FILE)

# 检查本地文件
if not os.path.exists(LOCAL_FILE):
    raise FileNotFoundError(LOCAL_FILE)

# 如果HDFS存在旧文件，则删除
if client.status(f"{HDFS_DIR}/{filename}", strict=False):
    print("删除HDFS旧文件...")
    client.delete(f"{HDFS_DIR}/{filename}")
else:
    print("HDFS不存在旧文件")

# 上传
client.upload(
    HDFS_DIR,
    LOCAL_FILE,
    overwrite=True
)

print("上传成功！")
print(f"HDFS路径：{HDFS_DIR}/{filename}")