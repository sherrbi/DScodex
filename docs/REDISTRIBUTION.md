# 第三方再分发审查（未清关）

1. 阻塞：完整 ZIP 含 ChatGPT.exe、修改后的 app.asar 等 OpenAI 桌面应用资产。当前条款禁止修改/复制/分发 Services；开源组件按各自许可证。未取得适用于该桌面程序的再分发授权，不发布现有 ZIP。私有仓库不是许可豁免。
2. Codex CLI 官方源为 Apache-2.0；只能据具体版本许可证/NOTICE、修改说明确认其组件，不代表桌面应用获准。
3. Python、Node、Electron、Chromium、Git 和大量 wheels/npm/plugin/skill 各有许可证与依赖义务；尚未完成逐版本 SBOM、LICENSE/NOTICE、GPL 对应源码与原厂分发权核查。Electron MIT 不能替代其上运行的应用许可。
4. COMSOL/Office 等商业程序和许可证不发布；朋友独立安装和授权。私有资料和平台内非公开技能也不能仅凭本机能使用便认定可再分发。
5. 可维护自有启动脚本与说明可先审阅；需要拥有者确认源权属与白名单审计。若要合法完整公开交付，另行设计由朋友从官方渠道安装依赖/桌面程序的重建路线；现有改包是否可用/许可仍需解决，不擅自重打已验 ZIP。

官方依据（核查日期 2026-10-02）：
- https://openai.com/policies/row-terms-of-use/
- https://github.com/openai/codex
- https://www.python.org/doc/copyright/
- https://github.com/electron/electron/blob/main/LICENSE
- https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
