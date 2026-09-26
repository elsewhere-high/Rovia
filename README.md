# Rovia

把远方排进日常。Rovia 是一个自驾旅行工作台，将出行需求、车辆信息、路线、沿途安排和行程调整放在同一处。

![Rovia 旅行工作台](docs/images/home.png)

## 功能

- 规划前集中澄清日期、目的地和出行约束，再确认开始规划。
- 按天、路段和活动查看行程；地图不可用时显示明确的降级状态。
- 管理车辆、历史行程、附件和版本；修改先预览，再应用或撤销。
- 校验驾驶时长、补能、SOC 连续性、餐饮住宿和返程闭环。
- 导出 Markdown、HTML、PDF、PPTX 和长图；查看任务进度及运行监控。
- 首次启动创建管理员，由管理员添加普通用户；账户数据按用户隔离。

## 本地启动

Python 统一使用 Conda。首次安装，在项目根目录执行：

```bash
conda env create -f environment.yml
conda run -n rovia npm ci --prefix frontend
```

启动：

```bash
conda run --no-capture-output -n rovia python scripts/dev.py
```

打开 <http://127.0.0.1:5373>，创建自己的管理员账户。启动器会准备 `.env`、执行数据库迁移，启动本地 Redis、API、worker 和前端。按 Ctrl+C 停止本次启动的进程。默认使用 SQLite，数据与凭据均不入库。

模型及地图参数在项目根目录 `.env` 中填写：

| 参数 | 用途 |
| --- | --- |
| `LLM_API_URL`、`LLM_API_KEY`、`LLM_MODEL` | 兼容 Chat Completions 的完整接口地址、凭据和模型名 |
| `LLM_PROVIDER` | 运行状态中显示的服务标识 |
| `AMAP_WEBSERVICE_KEY` | 后端地点检索与真实路线 |
| `VITE_AMAP_JSAPI_KEY`、`VITE_AMAP_SECURITY_JS_CODE` | 浏览器地图 |

修改配置后重启。缺少模型凭据时，语义规划会明确暂停；缺少地图凭据时显示降级提示。界面截图中的示例行程属于测试数据，不能作为实际道路或出行信息。

## 开发与接口

- [开发、验证与配置](docs/development.md)
- [架构与功能边界](docs/architecture.md)
- [接口说明](docs/api.md)，运行后也可访问 <http://127.0.0.1:8000/docs>

## 许可

Copyright (C) 2026 Ustinian5。项目代码采用 [AGPL-3.0-only](LICENSE)。第三方资源分别遵循其自身条款，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
