
# OpenStack Swift Django 网盘 - 简易配置步骤
## 一、环境准备（5 分钟）
1. **装 Python**：确保 Python 3.10+（推荐 3.12.11）

2. **创虚拟环境**：
```
\# 用venv（Windows/Linux通用）

python -m venv venv

\# 激活：Windows→venv\Scripts\activate；Linux→source venv/bin/activate
```
1. **装依赖**：

```
pip install django==5.2 python-swiftclient
```
## 二、核心配置（关键！）

### 1. 对接 OpenStack Swift

打开 `app/``views.py`，添加 Swift 连接（替换成你的 OpenStack 信息）：

```
import swiftclient

def get\_swift\_conn():

&#x20;   return swiftclient.Connection(

&#x20;       auth\_url="http://你的Keystone地址:5000/v3",  # 例：192.168.1.100:5000/v3

&#x20;       user="你的OpenStack用户名",                  # 例：admin

&#x20;       key="你的OpenStack密码",                    # 例：Admin123!

&#x20;       tenant\_name="你的项目名",                   # 例：admin

&#x20;       auth\_version="3",

&#x20;       insecure=True  # 开发环境用True，生产环境改False

&#x20;   )
```

### 2. 数据库（默认免配）

用自带 SQLite，无需额外安装，后续自动初始化。

## 三、启动项目（2 分钟）

1. **初始化数据库**：

```
python manage.py migrate
```

1. **启动服务**：

```
python manage.py runserver
```

1. **访问**：浏览器打开 `http://127.0.0.1:8000`，看到登录页即成功。

## 四、常见问题

* Swift 连不上：检查`auth_url/用户名/密码`是否对，确保能访问 OpenStack 5000/8080 端口

* 端口占用：换端口启动：`python ``manage.py`` runserver 8081`

> （注：文档部分内容可能由 AI 生成）
