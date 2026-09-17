# 风瞳（Fengtong）

风瞳是一个面向新闻内容发布与风险审核的全栈项目。用户可注册登录、发布新闻、由 Dify 工作流辅助创作和审核，并使用搜索、地图、积分、礼品商城、秒杀和订单能力。管理端可审核新闻、管理礼品与秒杀活动、查看统计信息。

本仓库可直接开源：真实环境变量、支付宝私钥和历史配置备份均不随源码提交。请勿把自己的 `.env`、PEM 私钥或云服务密钥加入 Git。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Pinia、Vue Router、Axios、ECharts、TinyMCE |
| 后端 | Python 3.11、FastAPI、SQLAlchemy、Pydantic、JWT、bcrypt |
| 数据与中间件 | MySQL 8、Redis 7、Elasticsearch 8、RabbitMQ 3 |
| 部署 | Docker Compose、Nginx |
| 外部能力 | Dify、支付宝、阿里云短信、百度地图 |

## 项目结构

```text
fengtong/
├─ backend/                    # FastAPI 接口、模型、异步消费者与业务服务
│  ├─ app/routers/             # 认证、新闻、AI、订单、积分、商城、地图等路由
│  ├─ app/models/              # SQLAlchemy 数据模型
│  ├─ app/services/            # 搜索、库存、支付、短信、消息消费等服务
│  └─ create_admin.py          # 交互式创建管理员脚本
├─ frontend/user-app/          # Vue 前端
├─ nginx/                      # 前端生产环境 Nginx 配置
├─ secrets/                    # 本地私钥目录；仅提交 .gitkeep
├─ docker-compose.yml          # 基础服务编排
├─ docker-compose.alipay.yml.example # 支付宝可选覆盖配置
└─ .env.example                # 可提交的环境变量模板
```

## 功能概览

- 认证：用户名密码、短信登录、JWT access/refresh token、会话失效。
- 新闻：发布、Dify 风控审核、审核流、评论、点赞、收藏、我的发布。
- AI：创作辅助与个人生成记录。
- 地图与搜索：Elasticsearch 全文检索、区域统计、新闻地理标记。
- 商城：积分余额和流水、礼品、秒杀库存、订单、超时取消。
- 支付：支付宝扫码支付、异步通知验签、订单状态查询。
- 管理：内容审核、用户统计、AI 记录、礼品和秒杀活动管理。

后端启动后可在 `http://localhost:8000/docs` 查看完整 OpenAPI 文档；健康检查为 `GET /api/health`。

## 快速启动（推荐 Docker）

### 1. 准备环境

安装 Docker Desktop（含 Docker Compose）。克隆仓库后，在项目根目录执行：

```powershell
Copy-Item .env.example .env
notepad .env
```

请替换 `.env` 中全部 `CHANGE_ME_*` 值，至少要配置数据库、RabbitMQ、JWT 和管理员邀请码。可用 PowerShell 生成 JWT 密钥：

```powershell
$bytes = New-Object byte[] 48
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
[Convert]::ToBase64String($bytes)
```

将输出值填入 `JWT_SECRET_KEY`。数据库密码、RabbitMQ 密码和管理员邀请码应使用不同的长随机值。

### 2. 启动服务

```powershell
docker compose up -d --build
docker compose ps
```

访问地址：

| 服务 | 地址 |
| --- | --- |
| Web 前端 | `http://localhost:3000` |
| FastAPI / Swagger | `http://localhost:8000/docs` |
| MySQL | `localhost:3307` |
| Redis | `localhost:6379` |
| Elasticsearch | `http://localhost:9200` |
| RabbitMQ 管理台 | `http://localhost:15672` |

查看日志或停止服务：

```powershell
docker compose logs -f backend
docker compose down
```

### 3. 创建第一个管理员

启动成功后，执行交互式脚本。密码不会写入源码：

```powershell
docker compose exec backend python create_admin.py
```

也可通过注册接口使用 `.env` 中的 `ADMIN_INVITE_CODE` 创建管理员。生产环境建议仅保留脚本方式，并设置一个高强度、可轮换的邀请码。

## 环境变量说明

`.env.example` 是唯一可提交的配置模板；`.env` 仅保存在本地或通过部署平台的密钥管理功能注入。

| 分类 | 变量 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| MySQL | `DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME` | 是 | Docker 默认主机名为 `mysql`；`DB_PASSWORD` 必须自行设置。 |
| Redis | `REDIS_HOST`、`REDIS_PORT` | 是 | Docker 默认主机名为 `redis`。 |
| Elasticsearch | `ES_HOST`、`ES_URL` | 是 | Docker 默认主机名为 `elasticsearch`。 |
| RabbitMQ | `RABBITMQ_HOST`、`RABBITMQ_PORT`、`RABBITMQ_USER`、`RABBITMQ_PASSWORD` | 是 | Docker 默认主机名为 `rabbitmq`；账号和密码不得使用示例或默认值。 |
| JWT | `JWT_SECRET_KEY`、`JWT_EXPIRE_MINUTES`、`REFRESH_TOKEN_EXPIRE_DAYS` | 是 | `JWT_SECRET_KEY` 至少使用 32 字节随机值；泄漏后必须立即轮换。 |
| 管理与跨域 | `ADMIN_INVITE_CODE`、`CORS_ORIGINS`、`DEBUG` | 是 | `CORS_ORIGINS` 用英文逗号分隔；生产环境只允许实际前端域名，`DEBUG=false`。 |
| Dify | `DIFY_CREATIVE_API_KEY`、`DIFY_RISK_API_KEY`、`DIFY_API_URL` | 使用 AI 时 | 分别配置创作和风控工作流密钥。 |
| 阿里云短信 | `ALIBABA_CLOUD_ACCESS_KEY_ID`、`ALIBABA_CLOUD_ACCESS_KEY_SECRET`、`SMS_TEMPLATE_LOGIN`、`SMS_TEMPLATE_CHANGE` | 使用短信时 | 请使用最小权限的 RAM 凭据，并限制短信服务权限。 |
| 百度地图 | `BAIDU_MAP_AK` | 使用地理编码时 | 为密钥配置来源域名/IP 限制。 |
| 支付 | `ALIPAY_APP_ID`、`ALIPAY_GATEWAY`、`ALIPAY_REDIRECT_URI`、`ALIPAY_NOTIFY_URL` | 使用支付时 | 回调地址在生产环境必须使用 HTTPS。 |
| 订单 | `PAYMENT_WINDOW_MINUTES` | 否 | 未支付订单的超时分钟数，默认 15。 |

## 配置支付宝（可选）

基础 Compose 不读取支付宝 PEM，因此不配置支付也能运行其它功能。需要支付时：

```powershell
Copy-Item docker-compose.alipay.yml.example docker-compose.alipay.yml
New-Item -ItemType Directory -Force secrets
# 把你自己的两个 PEM 文件放入 secrets/，文件名必须如下：
# secrets/alipay_private_key.pem
# secrets/alipay_public_key.pem
docker compose -f docker-compose.yml -f docker-compose.alipay.yml up -d --build
```

同时在 `.env` 填写 `ALIPAY_APP_ID`、网关和两个回调地址。`secrets/` 与本地覆盖文件均被 `.gitignore` 忽略，不能提交。支付宝私钥泄漏时，应立即在支付宝平台更换密钥并撤销旧密钥；仅从仓库删除文件并不能使旧密钥失效。

## 本地开发（不使用完整 Docker）

前提：安装 Python 3.11、Node.js 22、MySQL、Redis、Elasticsearch 与 RabbitMQ，并将 `.env` 中的服务主机名改为本机实际地址（通常是 `localhost`）。

```powershell
# 后端：在项目根目录执行，确保根目录 .env 可以被读取
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH = "$PWD\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

新开一个终端启动前端：

```powershell
Set-Location frontend\user-app
npm ci
npm run dev
```

Vite 已将 `/api` 请求代理到 `http://localhost:8000`。

## 安全与开源发布清单

发布前请逐项确认：

- 不提交 `.env`、`.env.*`、`secrets/` 内容、`*.pem`、`*.key`、`*.p12` 或数据库备份。
- 不提交包含旧配置的压缩包、截图、日志、CI 输出或 Docker 镜像层。
- 本项目历史中出现过真实凭据。即使当前文件已移除，也应轮换 JWT、Dify、阿里云、百度地图、RabbitMQ、数据库和支付宝私钥；若曾推送到远端，还需清理 Git 历史。
- 生产环境不要公开暴露 MySQL、Redis、Elasticsearch 和 RabbitMQ 管理端口；通过内网、反向代理、防火墙或安全组限制访问。
- 当前 Elasticsearch Compose 配置关闭了内置安全认证，仅适用于受隔离的开发环境；生产环境必须启用认证与 TLS。
- 将 `CORS_ORIGINS` 收敛到可信前端域名，所有支付回调使用 HTTPS。
- 定期执行 `npm audit`、更新依赖，并在上线前进行鉴权、支付回调和并发库存的集成测试。

## 常用命令

```powershell
# 查看全部容器日志
docker compose logs -f

# 重建并启动
docker compose up -d --build

# 停止并删除容器（保留命名卷数据）
docker compose down

# 停止并连同数据库等命名卷一起删除（不可恢复）
docker compose down -v
```

## 贡献与漏洞报告

欢迎提交 Issue 和 Pull Request。请不要在公开 Issue、PR、日志或示例中粘贴密钥、令牌、手机号、订单信息或支付回调原文。涉及安全漏洞时，请先私下联系维护者，并提供最小复现信息。
