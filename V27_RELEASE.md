# V27：精力强化卡牌与图标

- 新增四张卡牌：精力核心（上限+15）、回能线圈（恢复速度+18%）、轻量步伐（冲刺消耗-15%）、闪现节流（闪现消耗-20%）。卡牌按普通/稀有/史诗/传说等级缩放。
- 新增四格精力图标精灵图，已切出 `runtime/icon_anime_stamina_core.png`、`stamina_regen.png`、`sprint_efficiency.png`、`blink_efficiency.png`，升级卡会优先显示这些图标。
- 精力强化只修改精力相关参数，不影响武器伤害、弹药和 Boss 机制。

生图源：`Assets/Art/pixel_portal_v1/source/energy_cards_v27.png`；提示词与导入：`tools/prepare_energy_cards_v27.py`。本次接口仅文字生成，未上传参考图。

验证：`python -m unittest test_energy_upgrades test_stamina_hud -v`。
