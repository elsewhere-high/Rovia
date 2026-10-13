# 2026 上海开源软件应用创新大赛

Rovia 参加开源 AI 工具赛道，以自驾旅行工作台展示需求理解、工具集成、独立约束校验和人工确认流程。

## 提交入口

- [参赛 Release](https://github.com/elsewhere-high/Rovia/releases/tag/os2026-v1.0)
- [作品介绍 PDF](https://github.com/elsewhere-high/Rovia/releases/download/os2026-v1.0/Rovia-OS2026-Introduction.pdf)
- [作品演示视频 MP4](https://github.com/elsewhere-high/Rovia/releases/download/os2026-v1.0/Rovia-OS2026-Demo.mp4)
- [中文字幕 SRT](https://github.com/elsewhere-high/Rovia/releases/download/os2026-v1.0/Rovia-OS2026-Demo.zh-CN.srt)
- [材料压缩包（PDF 与提交链接）](https://github.com/elsewhere-high/Rovia/releases/download/os2026-v1.0/Rovia-OS2026-Submission.zip)

视频为真实界面和后端操作的剪辑，配中文合成解说及字幕。使用内置合成行程，持续标注“内置示例 / 非实时生成”；未配置模型和地图凭据，展示其缺失提示，不声称完成实时 AI 规划。天气、费用、能耗及路线均不能作为实际出行依据。

## 复现示例

先按项目首页安装 Conda 环境和前端依赖，再运行：

```bash
conda run --no-capture-output -n rovia python scripts/contest_demo.py
```

打开 <http://127.0.0.1:5175>。演示账户 `demo@example.test`，密码 `local-contest-demo-only`。脚本仅监听本机，使用独立临时数据库并在退出后清理；显式关闭模型凭据，预载仓库内示例。该账户只供本地演示，不能用于生产部署。

视频展示车辆参数编辑、需求检查、历史行程、阶段与日期切换、风险提示、修改预览及放弃、版本保存、PDF 导出结果与管理员运行监控。

## 2026-10-13 验证记录

环境：macOS，rovia Conda 环境。本轮未配置在线模型与地图凭据。

| 检查 | 结果 |
| --- | --- |
| `pytest backend/tests evaluation -q` | 257 通过，1 项在线集成测试跳过 |
| 前端 Vitest | 2 通过 |
| TypeScript / Vite 生产构建 | 通过；3D 组件有大包体积提示 |
| 确定性安全场景 | 12/12 符合预期 |
| 浏览器实际操作 | 车辆保存、分段分日查看、修改预览及放弃、版本保存、PDF 下载完成 |
| 行程 PDF | 实际导出 3 页，中文文本可提取 |
| 介绍 PDF | 8 页，嵌入中文字体并逐页渲染检查 |

模拟续航回放共 12 条样本：能耗 MAPE 8.442%，续航 MAPE 9.302%，SOC MAE 2.799 个百分点。这些是仓库模拟数据的结果，不代表真实道路精度或在线供应商验收。安全场景中包含应阻止交付的补能缺失情况，不能把“通过场景检查”解释为所有路线可执行。

本轮同时固定两项测试的基准日期，避免 2026 年国庆日期过期后干扰其行程天数断言；将版本命名由原生 `prompt()` 改为页面内表单，以兼容内嵌浏览器。

## 官方要求

核对日期：2026-10-13。[大赛官网](https://www.oschina.net/os2026/)要求提交完整可运行的代码仓库、包含背景/架构/场景/创新点的介绍文档，以及展示核心功能与流程的视频链接。当前页面列出的材料截止时间为 2026-10-16 24:00，收件邮箱为 `oscc@oschina.cn`；入围名单 10 月 21 日公布，总决赛 10 月 29 日举行。报名审核及具体提交方式以组委会邮件指引为准。
