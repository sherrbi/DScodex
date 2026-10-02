# DSCodex Portable — GitHub publication staging

公开源码准备版；用户允许公开并指定 `DScodex`；已明确授权新建公开仓库 `sherrbi/DScodex`；仓库已由拥有者创建，地址 https://github.com/sherrbi/DScodex 。本目录不含运行时、第三方桌面程序、个人数据或迁移 ZIP。不要从父目录执行 git add；只允许以本目录为独立仓库边界并按白名单暂存。

`src/` 是维护用的迁移启动/监督脚本，不是独立可运行安装包，需要匹配的资产与 manifest；克隆本仓库不能直接启动 DSCodex。源文件权属仍需拥有者确认。不能给未知第三方源码统一追加开源许可证。

候选完整迁移 ZIP 为 1,887,777,954 字节，SHA256 `5ea553afca75d200cb59c58e99c347cd6b31d59a50b0e4ca0b5aae1fb4d4b38e`。其本地验收通过，目标机器功能验收仍待完成。ZIP 不追踪进 Git；尺寸符合 Release 单资产小于 2GiB 的限制，但其中修改后的专有桌面程序再分发许可未确认，所以目前禁止发布该资产，私有仓库也不消除许可要求。

见 docs/INSTALL-ACCEPTANCE.md、docs/REDISTRIBUTION.md 与 PUBLISH-PLAN.json。当前没有自动发布工作流或有效凭据。

本仓库是源码与配置模板/前置检查，不是完整原环境一键重建。
