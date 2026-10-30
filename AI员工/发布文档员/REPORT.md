# 发布文档员汇报

本轮基于实际 Python / pygame 项目准备 0.2.0 源码发布候选。

已更新 PROJECT_CONTEXT.md、资源授权记录；新建 RELEASE_GUIDE.md、CHANGELOG.md、打包脚本 build_source_release.ps1。旧 README/CURRENT_CONTROLS 标注历史规则避免误导。

源码包白名单仅包含当前运行代码、requirements和说明；排除旧 Unity/Godot资产、IDE设置、缓存和测试截图。默认不包含公开再分发许可待核实的用户音乐；开发目录不受影响。

初次隔离测试：dist 中白名单拷贝目录成功导入模块、打开开始菜单、退出；无音乐文件时不崩溃。最终包待程序最终稳定后重新生成并记录 SHA256。

最低配置没有实测，不写保证值。当前验证 Python 3.13.13、pygame 2.6.1、Windows，图形自动验证使用 dummy 驱动，不能冒称真实帧率/音箱听感。

第二轮候选包：dist/RogueFPS-0.2.0-source-20261006-022335.zip。
SHA256：E4A682AEED260DF5859741A2294F236EC109293F4F3CC99982DA0E9930ABE3C7。
已列举压缩包条目，仅7个白名单源文件/说明；隔离目录菜单、开始、退出验证通过。最终报告变化不影响源码内容，但最终交付会再次打包最新说明。

最终候选包：dist/RogueFPS-0.2.0-source-20261006-022706.zip；SHA256：9620F36F927B2D3A735B846CB907B117F25F42D98808F467F9CBDCB1F01AAC99。
入口SHA256：0E1E9BBF135580D1B548D4351EB4F800082D42E4D1FF3AECDB88516DD17B5DC0。
隔离包再次验证入口hash、菜单、霰弹射击、绘制、Q退出通过，已包含最后命中图缓存优化。
