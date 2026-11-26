# V14：Boss 完整切图、世界范围特效、狙击枪重绘

- 根因：combat_v9_bosses.png 五行并非等高，旧 4×5 等分切图裁掉巨像腿脚。按原图实际行边界重新导入五 Boss 四姿态，共20张 v14 帧；脚底基准统一376/384。
- 地锤、突扑、剑舞、跃空震击、冲撞的判定和预警/命中特效共用世界半径。地锤逐击半径2.6/3.05/3.5，狂暴末击3.95；射线与狙击共用各自判定走廊宽度和长度。
- 危险区域近裁剪，玩家站在范围内也能显示；地面特效改到角色、持枪和HUD之前绘制。
- Apinebula gpt-image-2 成功生成 source/sniper_v14.png（16帧），已导入 runtime/low_sniper_v14_0..15.png；同款蓝灰枪体、青色镜片、白袖深蓝手套，包含待机、开火、后坐、拉栓、下方弹匣换弹。接口只支持文字，本次未上传参考图；生成提示词原文见 tools/redraw_sniper_v14.ps1。
- 保留上一版素材供回退，运行时优先新16帧。换弹按实际进度播放，拉栓随射击周期适配。
- requirements.txt 补充 numpy 依赖；音频盘点见 AUDIO_AUDIT.md。

复现：python tools/prepare_boss_v14.py；python tools/prepare_sniper_v14.py。
验证：test_boss_v14 + test_melee 22项通过；tools/qa_boss_signatures.py 五种技能正常/狂暴通过。画面验证脚本 tools/qa_boss_v14.py。
