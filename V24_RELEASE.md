# V24：霰弹枪真实枪声

- 用户提供的 `散弹枪音效 .wav` 已复制为 `Assets/audio/shotgun_shot.wav`。
- 替换原合成 `shot1`，霰弹枪射击触发时播放，音量调高到0.90。
- 射速、九颗弹丸、伤害和换弹逻辑不变；静音逻辑兼容。

验证：`python -m unittest test_shotgun_audio -v`。
