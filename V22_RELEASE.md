# V22：刀剑攻击音效

- 用户提供的 `刀剑攻击.wav` 已复制为 `Assets/audio/sword_swing.wav`。
- 替换原 `sword_swing` 合成声，刀剑攻击触发时播放，音量0.55；静音逻辑和攻击冷却不变。
- 其他近战命中音效仍使用 `melee_hit`。

验证：`python -m unittest test_sword_audio -v`。
