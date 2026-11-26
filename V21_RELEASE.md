# V21：走路脚步音效

- 用户提供的 `414325__unlistenable__walking_2.wav` 已复制为 `Assets/audio/footstep.wav`。
- 实际着地移动时播放；普通走路约460ms一声，冲刺约300ms一声；跳跃/空中不播放。
- 静音设置仍然有效。起跳、落地和材质专属脚步音仍待补充。

验证：`python -m unittest test_footstep_audio -v`。
