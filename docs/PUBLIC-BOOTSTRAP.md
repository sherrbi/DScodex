# 公开版入口（准备，未实测）

START-PUBLIC.cmd 只检查现有 Codex CLI；缺失时默认停止。只有显式 -InstallCodexCli 才使用官方 README 的 npm install -g @openai/codex。需要朋友批准联网/全局 npm 变更，已有合法 Node.js/npm，可能受 Windows 配置和权限影响。无管理员自动提权、不下载桌面程序、不复制商业资产、没有填写/生成凭据。

这不是完整 DSCodex 的一键重建。原迁移版 bootstrap 和 supervisor 依赖 bundle 内匹配的 Python/GUI/assets/manifest；受限桌面组件缺失时不能运行原改造。CLI 可用仅验证 CLI，不验证 DeepSeek adapter、304 技能、31 启用插件、MCP、浏览器或 GUI。公开版完整重建还需要依赖版本锁定、各组件许可证与官方源、适配程序接线及干净机实测。现阶段明确停止在前置检查，不宣称降级完成。

官方源：https://github.com/openai/codex 。代码准备后未运行本脚本或安装 npm 包；未改变私人迁移 ZIP。
