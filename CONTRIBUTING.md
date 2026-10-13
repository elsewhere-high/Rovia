# 参与 Rovia

欢迎通过 GitHub Issues 提交问题、数据源适配建议和使用反馈。报告问题时请包含操作步骤、预期与实际结果、操作系统及已脱敏的错误信息，不要提交账户数据或服务凭据。

修改代码前请阅读 [开发说明](docs/development.md) 和 [架构边界](docs/architecture.md)。Python 统一使用 `rovia` Conda 环境。Pull Request 请说明具体问题、行为变化及相关验证结果；涉及共享数据结构时同步核对 JSON Schema、前端类型和数据库迁移。

## 相关检查

```bash
PYTHONPATH=backend conda run -n rovia python -m pytest backend/tests evaluation -q
conda run -n rovia npm test --prefix frontend
conda run -n rovia npm run build --prefix frontend
```

按改动范围执行相关检查。在线测试需要自行配置服务，未执行时明确说明，不能计为通过。续航回放数据是模拟数据，新增数据必须保留来源、使用条件和真实/模拟标记。

模型输出不能绕过独立约束校验。缺失、未知和估算信息应继续明确展示；行程修改保留用户确认和可追溯结果。

代码贡献遵循项目的 AGPL-3.0-only 许可。新增第三方资源时附来源、许可及必要说明，保留原有归属；不要把应用许可自动套用到模型、图片或服务数据。
