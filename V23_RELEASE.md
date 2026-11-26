# V23：闪现短刃攻击音效

- 用户提供的 `闪现短刃攻击音效.mp3` 已复制为 `Assets/audio/dagger_dash.mp3`。
- 闪现短刃攻击触发时播放该音效，音量0.55；替换原合成 `dagger_dash`，不影响刀剑挥砍、近战命中和精力扣除。
- 静音逻辑兼容。

验证：`python -m unittest test_dagger_audio -v`。
