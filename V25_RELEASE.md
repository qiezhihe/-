# V25：刀剑节奏与脚步声道平衡

- 刀剑攻击间隔从300ms放慢到440ms，动作和音效更容易辨认。
- 刀剑攻击音量从0.55提高到0.78。
- 脚步录音原本左右声道音量不一致，已转为双声道同相同音量，左右耳同时播放；长度、采样率和音调不变。

验证：`python tools/normalize_stereo_audio.py`；`python -m unittest test_audio_balance -v`。
