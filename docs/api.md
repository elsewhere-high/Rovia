# Rovia API

运行后访问 `/docs` 查看完整 OpenAPI，`/openapi.json` 获取机器可读契约。以下路径相对 API 根地址，默认 <http://127.0.0.1:8000>。版本为 `0.1.0`，业务路由前缀为 `/api/v1`。

## 认证

`GET /api/v1/auth/status` 返回初始化状态。空数据库仅允许一次 `POST /api/v1/auth/setup` 创建管理员。随后通过 `POST /api/v1/auth/login` 登录，响应设置 HttpOnly `rovia_session` Cookie；`GET /api/v1/auth/me` 读取当前用户，`POST /api/v1/auth/logout` 退出。浏览器跨域调用需携带 credentials 并匹配服务端 CORS 配置。

管理员通过 `GET/POST /api/v1/auth/users` 管理用户。受保护资源必须登录，资源标识不能绕过所属用户检查。

## 业务接口

| 路径 | 方法与用途 |
| --- | --- |
| `/health` | GET：服务与供应商配置摘要，不返回密钥 |
| `/api/v1/trips` | GET/POST：列表、创建行程 |
| `/api/v1/trips/preflight` | POST：澄清需求与确认状态 |
| `/api/v1/trips/{id}` | GET/PATCH/DELETE：详情、更新、级联删除 |
| `/api/v1/trips/{id}/planning/start` | POST：排入异步规划任务，返回 202 |
| `/api/v1/trips/{id}/planning` | GET：当前规划快照 |
| `/api/v1/trips/{id}/planning/events` | GET：SSE 进度事件 |
| `/api/v1/trips/{id}/patches/preview` | POST：预览候选修改 |
| `/api/v1/trips/{id}/patches/{patch_id}/{action}` | POST：`apply`、`reject` 或 `rollback` |
| `/api/v1/trips/{id}/versions` | GET/POST：列出或保存版本 |
| `/api/v1/trips/{id}/versions/{version_id}/restore` | POST：恢复版本 |
| `/api/v1/trips/{id}/roadbook` | GET：Markdown 行程 |
| `/api/v1/trips/{id}/roadbook.{format}` | GET：`html`、`pdf`、`pptx` 或 `png` 导出 |
| `/api/v1/vehicles` | GET/POST：车辆列表与创建；`/{id}` 支持 GET/PATCH/DELETE |
| `/api/v1/files` | POST：multipart 上传，字段为 `upload` 和可选 `trip_id` |
| `/api/v1/files/{id}/content` | GET：附件下载 |
| `/api/v1/files/{id}/extract`、`/confirm` | POST：提取预览、确认地点 |
| `/api/v1/jobs` | POST：创建任务；`/{id}` 查询，`/{id}/cancel` 取消 |
| `/api/v1/skills/health` | GET：工具健康状态；各供应商接口详见 OpenAPI |
| `/api/v1/ops/metrics` | GET：管理员运行监控 |

创建行程的最小请求：

```json
{"title":"安吉周末","request":{"raw_text":"周六从杭州出发去安吉，两天后返回"}}
```

预检返回 `ready`、`confirmation_required`、`semantic_checked`、`issues`、`extracted` 等字段。HTTP 200 不代表工具或规划成功，还应检查业务状态及校验结果。

错误通常包含 `error.code`、`error.message`、`error.details` 与 `error.request_id`，响应头带 `X-Request-ID`、`X-Trace-ID`。缺少凭据、限流、任务队列不可用和资源不存在均有明确状态；调用方应显示可恢复提示并保留用户输入。
