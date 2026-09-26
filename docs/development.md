# Rovia 开发与运行

## 环境与启动

根目录 `environment.yml` 定义 Python 3.11、Node.js 22、Redis 7.4 与后端依赖。始终在 `rovia` Conda 环境执行 Python。已有环境需要更新时运行：

```bash
conda env update -n rovia -f environment.yml
conda run -n rovia npm ci --prefix frontend
conda run --no-capture-output -n rovia python scripts/dev.py
```

网页默认 `127.0.0.1:5373`，API 默认 `127.0.0.1:8000`。启动器不会停止已占用端口的其他程序，可用 `ROVIA_WEB_PORT`、`ROVIA_API_PORT` shell 环境变量改变端口。前端通过同源 `/api` 代理连接后端。

`.env.example` 是安全示例；本地 `.env`、数据库、上传、Redis 数据和日志已被 Git 忽略。管理员字段留空时，由首次访问者在本地登录页完成初始化。`LOAD_LOCAL_SKILL_CREDENTIALS=false` 默认禁止扫描技能目录读取凭据。

可选旅行检索依赖 FlyAI CLI。需要此服务时，在 Conda 环境内安装锁定版本并配置 `FLYAI_API_KEY`：

```bash
conda activate rovia
npm install --global --prefix "$CONDA_PREFIX" @fly-ai/flyai-cli@1.0.16
```

其他可选供应商配置及别名见 `.env.example`，不要将真实密钥写入示例或前端源码。前端地图变量用于浏览器 SDK；模型及后端服务密钥只由后端读取。

## 检查

在项目根目录执行：

```bash
PYTHONPATH=backend conda run -n rovia python -m pytest backend/tests evaluation -q
conda run -n rovia python evaluation/range_accuracy.py
PYTHONPATH=backend conda run -n rovia python evaluation/safety_scenarios.py
conda run -n rovia npm test --prefix frontend
conda run -n rovia npm run build --prefix frontend
```

续航数据集明确标注为模拟数据，结果不代表真实道路精度。安全场景覆盖低电量、补能缺失、天气与依赖失败等确定性约束。

浏览器测试：

```bash
cd frontend
conda run -n rovia npx playwright install chromium firefox
conda run -n rovia npm run test:e2e
```

默认测试自动启动隔离的 API（8765）和前端（5174），创建临时数据库及明确标记的测试账户；不会使用开发数据库或真实供应商凭据。覆盖两个桌面尺寸、390px 小屏、3D 车辆、规划阶段、折叠栏、预览确认与错误恢复，并保留 Firefox 兼容性检查。视觉基线按平台区分；新平台首次建立基线需人工审阅后执行 `--update-snapshots`。

真实在线验收需要已启动且已配置模型/地图的实例。浏览器测试可设置 `ROVIA_E2E_BASE_URL`、`ROVIA_E2E_EMAIL`、`ROVIA_E2E_PASSWORD`，再开启 `ROVIA_RUN_LIVE_AGENT_E2E=1`；已有完整行程用 `ROVIA_E2E_TRIP_ID` 指定。后端在线测试需单独运行，以免普通测试的凭据隔离覆盖 `.env`：

```bash
PYTHONPATH=backend ROVIA_LIVE_TESTS=1 conda run -n rovia python -m pytest --confcutdir=backend/tests/integration backend/tests/integration/test_live_stage_d.py -q
```

这些检查会访问真实服务；缺少凭据时默认跳过，不计为在线功能通过。

## 数据与迁移

```bash
conda run -n rovia python -m alembic -c backend/alembic.ini upgrade head
```

迁移由本地启动器自动执行。修改模型时同时核对 `shared/schemas`、前端类型、数据库迁移和关联测试。停止服务后再备份 SQLite 与上传目录；Redis 用于任务调度，不能代替数据库备份。

保留的 Docker Compose 配置提供 PostgreSQL、Redis、API、worker 和 Nginx。启动前需要可用的 Docker 服务及项目 `.env`，通过 `docker compose up --build` 启动。本机 Conda 验证不等于容器或公网部署验证；部署时需配置 HTTPS、Cookie 安全选项及自己的访问边界。
