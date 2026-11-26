# V26：散弹枪音量增强

- 原录音峰值仅约4371/32767，播放器音量0.90仍偏小。
- 已对项目副本做限幅安全增益，峰值提升至约30000，并将播放音量调到1.0。
- 不改变射速、弹丸、伤害和换弹逻辑。

执行：`python tools/normalize_shotgun_audio.py`。
验证：`python -m unittest test_shotgun_audio -v`。
