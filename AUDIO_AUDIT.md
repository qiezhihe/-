# 音频缺项盘点（2026-10-30）

检查范围：`Assets/audio`、`fps_game.py:make_sounds` 与实际播放事件。下面区分「已有录音」「合成占位声」「尚无独立音效事件」，并不是所有缺项都完全无声。

## 已有用户录音，不必重复提供

| 用途 | 已接入文件 |
| --- | --- |
| 冲锋枪射击 | smg_shot_single.wav（从 smg_shot.wav 提取） |
| 机枪射击 | machinegun_shot_single.wav（从 machinegun_shot.wav 提取） |
| 狙击枪射击、拉栓 | sniper_shot.wav、sniper_bolt.wav |
| 全枪械换弹 | gun_reload.wav，运行时适配换弹时长 |
| 回旋镖投出 | boomerang_throw.wav |
| 长矛投出、接回 | spear_throw.wav、spear_catch.wav |
| 一至四杀、五杀及以上 | kill_1.wav 至 kill_5.wav |
| 背景音乐 | kiravale-gaming-music-593659.mp3 |
| 走路单步 | footstep.wav |
| 刀剑攻击 | sword_swing.wav |
| 闪现短刃攻击 | dagger_dash.mp3 |
| 霰弹枪射击 | shotgun_shot.wav |

冲锋枪、机枪、狙击枪已不再生成旧合成开枪声，缺文件也不会回退旧枪声。

## 优先补：当前只有合成占位声

| 优先级 | 建议提供的录音 | 当前状态 / 对应事件 |
| --- | --- | --- |
| 高 | 子弹命中肉体、玩家受伤（分开两条更好） | 目前共用 hit |
| 高 | 近战命中 | melee_hit（刀剑挥砍和闪现短刃已替换为用户录音） |
| 高 | Boss 蓄力预警 | boss_charge |
| 高 | 巨像砸地、猎王扑击、审判官狙击、织母召唤、执刑者剑舞 | boss_hammer、boss_hunt、boss_snipe、boss_brood、boss_duel |
| 中 | 普通敌人攻击 | enemy，多个敌人共用一条合成声 |
| 中 | 治疗、嘲讽、炮手射击、布雷、狂暴 | pet_healer、pet_taunter、pet_gunner、pet_minelayer、pet_berserker |
| 低 | 强化升级、弹药补给 | upgrade、insert |

## 可补：目前没有独立音效或专属触发

- 起跳、落地；走路单步和跑步已复用用户脚步录音。
- 普通敌人死亡、Boss 死亡；爆头独立提示音（当前仍可播放连杀播报）。
- Boss 激光启动/持续/结束、冲撞、跃空落地、分裂弹发射/命中。现有 enemy 提示不能代替专属技能音效。
- 地雷爆炸：目前只有布雷时的合成提示声，爆炸命中没有独立播放事件。
- 霰弹枪泵动、武器切换、回旋镖接回。
- 菜单确认、暂停/继续、波次开始/结束、低血量警报。

这些项目需要在拿到录音后增加或细分播放事件；把文件放进目录不会自动接入。

## 提供素材建议

最先提供：**霰弹枪开枪、砸地、激光、命中、脚步**。M4A/MP3/WAV 都可以，尽量去掉开头静音、避免削波；持续激光适合另给一段能循环的中间声。版权来源和再分发许可仍需确认。
