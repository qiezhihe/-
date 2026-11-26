# V16：机枪换弹八帧

- 根因：机枪v11整套源图/运行帧并不存在，仅保留了导入脚本和调用分支；v9待机/开火分支无条件覆盖旧换弹选择。
- Apinebula生图绘制8帧：伸手、开盖、取下弹箱、拿新弹箱、装弹箱、铺弹链、关盖、拉机柄。黑灰枪体、左侧橄榄绿弹箱、金色弹链，深蓝手套/白袖/青色护腕。
- 新版仅覆盖换弹；v9待机和射击不变。换弹不再被最后一枪残余的火光计时或旧版待机覆盖。
- 按真实换弹时长取帧，适配强化加速；保留原有换弹录音、补弹判定和切枪取消。图片缺失时仍能回退旧换弹帧，而非待机。
- 统一裁切范围和等比缩放，固定右下枪托锚点，去洋红底及分格边线，不逐帧自动放大裁切。

生成图：Assets/Art/pixel_portal_v1/source/mg_reload_v16.png。
帧：Assets/Art/pixel_portal_v1/runtime/low_mg_reload_v16_0..7.png。
生成入口及完整提示词：tools/redraw_mg_reload_v16.ps1。此次接口仅文字生成，未上传原图。

验证：python -m unittest test_mg_reload_v16 test_motion_switch -v。
画面：python tools/qa_mg_reload_v16.py，输出 artifacts/mg_reload_v16_preview.gif 和 mg_reload_v16_ingame.png。
