# 美术与音频授权记录

2026-10-30 低持冲锋枪/小幅举盾：`source/low_v8_smg.png`、`source/low_v8_guard.png`；项目 AI 生图，来源 https://img-api.apinebula.ai/ ，gpt-image-2；许可依账户条款，商用与署名未核实。用途：冲锋枪待机和刀盾格挡。提示词：`tools/redraw_low_v8.ps1`。删除已确认含女性角色的旧 Boss 蓄力/砸地八帧，恢复备份：`artifacts/art_cleanup/wrong_character_boss_fx.zip`。

2026-10-30 长矛与刀盾完整重构：`source/melee_v7_spear.png`、`source/melee_v7_sword.png`；项目 AI 生图，来源 https://img-api.apinebula.ai/ ，gpt-image-2；许可依账户服务条款，商用及署名条件未核实。各 16 帧，使用于 `runtime/low_spear_*`、`low_sword_*` 与武器图标。完整提示词：`tools/redraw_melee_v7.ps1`；导入工具：`tools/prepare_melee_v7.py`。

2026-10-30 冲锋枪待机重构：`source/smg_v6_idle.png`；作者：项目 AI 生图；来源：https://img-api.apinebula.ai/ ，gpt-image-2；许可依服务账户条款，商用及署名条件未核实。使用：`runtime/low_smg_idle.png`、`low_smg_idle_end.png`、`weapon_smg.png`。紧凑 MP5 类枪型，右手握把、左手前护木，无枪口火光。

2026-10-29 Boss 遭遇分镜：`story_v1_colossus/hunter/judge/weaver/executioner.png`，每组六个按事件顺序的画面；作者：项目 AI 生图；来源：https://img-api.apinebula.ai/ ，模型 gpt-image-2；许可：账户服务条款，商用与署名条件未核实。使用位置：`runtime/fx_story_*_0..5.png`，Boss 波登场短片，单帧 2.5 秒，总长 15 秒。提示词：`tools/redraw_boss_story.ps1`。

2026-10-29 长矛与剑盾及 Boss 特效：`melee_v5_spear/sword/bossfx.png`；作者：项目 AI 生图；来源：https://img-api.apinebula.ai/ ，gpt-image-2；许可：账户服务条款，商用/署名要求未核实。使用位置：`runtime/low_spear_idle.png`、`low_sword_*.png`、`fx_signature_*.png`。提示词保存在 `tools/redraw_melee_v5.ps1`。

2026-10-29 枪械无火光待机图：`idle_clean_v4_smg/mg/sniper.png`，作者为项目 AI 生图，来源 https://img-api.apinebula.ai/ ，模型 gpt-image-2。许可依账户服务条款，商用及署名条件尚未核实，不标记为 CC0。使用于 `runtime/low_*_idle.png`、`low_*_idle_end.png` 和 `weapon_*.png`，提示词保存于 `tools/redraw_gun_idle.ps1`。

已使用资源：

- 背景音乐 kiravale-gaming-music-593659.mp3：用户提供，位于 assets/audio；作者、来源链接与公开再分发许可尚未核实，公开发布前补齐许可或排除此音乐。
- pygame 2.6.1：LGPL，来源 https://www.pygame.org/ 。源码版由用户自行安装。
- Windows 字体：从系统目录加载，项目不分发字体文件。
- 其余模型、图标和音效由程序生成。

每项资源记录：名称、网址、作者、许可类型、下载日期、使用位置、是否需要署名、许可页面存档位置。

2026-10-29 敌人正面移动重绘：`locomotion_v2_runner/elite/normal/shooter/tank/bat.png`，由项目使用已配置的 Apinebula `gpt-image-2` 生图服务生成。服务网址：https://img-api.apinebula.ai/ ，生成提示词保存于 `tools/redraw_enemy_motion.ps1`。使用位置：`Assets/Art/pixel_portal_v1/source` 原图及 `runtime/anime_enemy_*_locomotion_*.png` 八帧动画。属于 AI 生成内容，不标注为 CC0；商用权限与署名要求依服务账户适用条款核实，尚未核实。未上传第三方参考图。
优先来源：Kenney、Poly Haven（通常 CC0）；Freesound 仅选择并记录明确允许项目用途的许可。

2026-10-29 整套一致性重绘：`cast_v3_runner/normal/shooter/tank/elite/bat.png`，同一生图服务生成，每类一张 16 格完整动作图。作者：项目 AI 生图；网址：https://img-api.apinebula.ai/；许可：服务账户条款，未核实商用与署名条件；使用位置：`Assets/Art/pixel_portal_v1/source/cast_v3_*.png` 和 `runtime/anime_enemy_*_cast3_*.png`。提示词及导入工具：`tools/redraw_enemy_complete.ps1`、`tools/prepare_cast_v3.py`。替代资源删除记录和恢复压缩包保存在 `artifacts/art_cleanup`。


## Combat v9（2026-10-30）
通过用户配置的 Apinebula gpt-image-2 生成 combat_v9_guns.png 与 combat_v9_bosses.png；源图位于 Assets/Art/pixel_portal_v1/source，切片位于 runtime（*_v9_*）。枪械以现有开枪帧的外观描述为设计参考，统一生成待机/发射/后坐/恢复；本次接口仅支持提示词，未上传原图作为图像参考。五个 Boss 各含专属起手/释放/恢复/激光发射姿势。

V10 连杀九宫格：用户配置 Apinebula gpt-image-2 生图，source/kill_medals_v10.png；提示词为 3×3 金属骷髅勋章，一至六星、火焰王冠、红色爆头准星、青色交叉刀，纯洋红背景无文字。运行时切片 icon_kill_*，脚本 tools/prepare_kill_medals_v10.py。

狙击枪拉栓音效：用户提供《狙击枪开完一枪后的拉栓.m4a》，转换为 Assets/audio/sniper_bolt.wav（单声道 44100Hz PCM，约1.13秒）。用于狙击枪每次开枪后的拉栓，原始文件未修改。

机枪开枪音效：用户提供《机枪开枪声.m4a》，转换为 Assets/audio/machinegun_shot.wav（单声道 44100Hz PCM，约2.22秒）。替换 shot2，音量0.4，连续开枪重触发以避免长采样叠音；原始文件未修改。

所有枪械换弹声：用户提供《换弹声.m4a》，转换为 Assets/audio/gun_reload.wav（约4.672秒，44100Hz单声道PCM）。运行时按当前换弹时长重采样，随速度改变音调；缓存最多16种时长。替换完整换弹音效，关闭旧分段插弹/拉栓音效，切枪取消、暂停跟随、支持静音。

冲锋枪开枪声：用户提供《冲锋枪枪声.m4a》，转换 Assets/audio/smg_shot.wav（0.704秒，44100Hz单声道PCM）。每次实际射击触发，保留原音调与起音，按实际射击间隔截短尾音并以5ms淡出；适配射速强化/临时加速/35ms下限，缓存最多24个时长，避免叠音。

回旋镖音效：用户提供《回旋镖.mp3》，转换为 Assets/audio/boomerang_throw.wav（约0.85秒，44100Hz单声道PCM），在实际投掷回旋镖时播放，音量0.5，重新投掷时避免同音效叠加。原始文件未修改。
