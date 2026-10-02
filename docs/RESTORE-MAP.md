# 恢复地图与源码边界

公开树含本次维护的 bootstrap/owned_process/session_supervisor/python313_runtime/START 源码，以及新增的公开前置检查、空 home/config 生成器、配置拓扑与依赖名称。原 launcher 源码留作审阅，不可单独运行：其匹配 manifest、adapter、Python/Node、MCP 实现、GUI、ASAR 和完整插件资产不在本树。

`restore-public.py --target <自己的新目录>` 默认只预览；显式 --apply 只生成 state/home 与空模板 config，不覆盖现有 config，不复制原 home，不启动/安装任何服务或工具。`START-PUBLIC.cmd` 检查朋友已有 Codex CLI，显式 -InstallCodexCli 才联网使用官方 npm；应先审阅全球安装权限和版本选择。Python/Node/Git 由朋友从官方安装或使用现有合法安装；不复制原虚拟环境。

依赖清单包含原环境技能目录名、插件 ID 与 MCP 名称，全部在公开版关闭。技能/插件内容和未知权属实现不分发，source_url 未核实则为 null，不编造自动下载地址。原配置拓扑仅为参考，{bundle} 需要将来合法完整资产；不能直接启用。朋友逐项确认来源、许可、账户订阅与凭据后恢复。原 source-enabled 只描述私用环境，不代表公开版已安装。

官方入口：Codex CLI https://github.com/openai/codex；Python https://www.python.org/downloads/windows/；Node https://nodejs.org/en/download；Git https://git-scm.com/downloads/win。网址引用不是本轮下载/许可证清关。版本来自既有证据：Codex CLI 0.155.0-alpha.9，Python 3.12.14/3.13.9，Node 24.21.0，Git 2.53.0.windows.3；公开 npm latest 不保证与这些版本功能兼容，公开版尚无版本锁定和重建验收。

自有 adapter/MCP、用户自定义技能与 guard/controller 等实现需独立权属与隐私审查，本次仅列依赖，未擅自公开。完整桌面改造依赖特定受限二进制，未用标准 CLI 替代后宣称全功能；没有一键完整重建成品。现有 1.89GB 私用 ZIP 保持不变且不进入本发行。
