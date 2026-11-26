"""130 upgrade cards: tier-scaled effects plus two fixed-rarity kill rewards.

Descriptions contain the actual value of each card, rather than the common
tier's value. Special effects only enter the pool after their weapon unlocks.
"""
TIERS = [('普通', (80,215,125),1), ('稀有',(80,160,255),1.7), ('史诗',(245,205,65),2.6), ('传说',(245,80,90),4)]
# Central balance knobs.  Keep progression readable: enemy health grows
# linearly and is capped, while weapon damage leaves room for upgrades.
BALANCE = {
    'player_walk_speed': 1.6,
    'player_sprint_multiplier': 2.0,
    'enemy_base_hp': 45.0,
    'enemy_hp_per_wave': 10.0,
    'elite_multiplier': 3.2,
    'boss_multiplier': 9.0,
    'runner_multiplier': .62,
    'max_wave_hp_scale': 4.0,
}

# Five boss identities used on successive boss waves. Their multipliers keep
# the encounter readable while changing movement and attack rhythm.
BOSS_DESIGNS = (
    {'name':'灰烬巨像','hp':1.00,'speed':.80,'skills':('hammer','slam','hammer')},
    {'name':'裂隙猎王','hp':1.12,'speed':1.05,'skills':('hunt','charge','fan')},
    {'name':'猩红审判官','hp':.92,'speed':1.20,'skills':('laser','snipe','laser','split')},
    {'name':'深渊织母','hp':1.25,'speed':.72,'skills':('brood','fan','brood')},
    {'name':'星陨执刑者','hp':1.38,'speed':.95,'skills':('duel','laser','duel')},
)
BOSS_TELEGRAPH = (
    dict(color=(255,120,40), accent=(255,190,90), cue='cue_colossus', motif='rift',
         signature_cue='三连地锤 · 末击后反击', enabled=True),
    dict(color=(255,55,95), accent=(255,140,150), cue='cue_hunter', motif='lock',
         signature_cue='锁点突扑 · 横移避开', enabled=False),
    dict(color=(255,215,120), accent=(255,240,190), cue='cue_judge', motif='beam',
         signature_cue='贯穿狙击 · 躲入掩体', enabled=False),
    dict(color=(180,120,240), accent=(140,235,180), cue='cue_weaver', motif='spore',
         signature_cue='孵化仪式 · 清理护卫', enabled=False),
    dict(color=(90,190,255), accent=(170,230,255), cue='cue_executioner', motif='blade',
         signature_cue='延迟剑舞 · 躲开末段', enabled=False),
)
EFFECTS = [
 ('power','弹头强化','伤害 +12%'),('haste','扳机强化','射速 +10%'),
 ('health','生命装甲','最大生命 +15 并治疗'),('speed','动力靴','移速 +6%'),
 ('magazine','扩容弹匣','弹匣容量 +3'),('reload','装填机构','换弹速度 +10%'),
 ('regen','组织再生','每秒回血 +0.3'),('leech','击杀汲取','击杀回血 +2'),
 ('pierce','穿透弹','增加贯穿目标'),('blast','爆破弹','溅射伤害 +12%'),
 ('crit','弱点分析','暴击率 +5%'),('critpower','致命弹药','暴击倍率 +0.2'),
 ('armor','减伤装甲','伤害减免提高'),('dodge','相位闪避','闪避概率提高'),
 ('slow','冰冻弹','命中减速提高'),('burn','燃烧弹','命中持续灼烧'),
 ('poison','毒素弹','命中持续中毒'),('execute','处决协议','低血量目标额外伤害'),
 ('range','长程枪管','射程 +15%'),
 ('blue_supply','击杀补给','击杀补充各枪独立备弹，按弹匣容量折算'),('heal','应急修复','立即恢复生命'),
 ('xp','学习芯片','经验收益提高'),('knockback','冲击弹','命中击退'),
 ('shield','波次护盾','每波恢复临时护盾'),
 ('stamina_core','精力核心','精力上限 +15'),('stamina_regen','回能线圈','精力恢复速度 +18%'),
 ('sprint_efficiency','轻量步伐','冲刺精力消耗 -15%'),
]
UPGRADES = [(key,f'{tier}·{title}',desc,rank,scale) for key,title,desc in EFFECTS for rank,(tier,color,scale) in enumerate(TIERS)]
WEAPONS = [
 # Relative real-world roles, not a ballistics simulator: fast light pistol
 # rounds, slow buckshot, heavy sustained rifle fire, deliberate bolt action.
 dict(name='冲锋枪',kind='gun',damage=18,delay=80,mag=30,reload=1800,pellets=1,range=28,
      headshot=2.,ammo='9毫米',reserve=150,reserve_max=300,automatic=True),
 dict(name='霰弹枪',kind='gun',damage=15,delay=850,mag=8,reload=2800,pellets=8,range=20,
      headshot=1.5,ammo='12号霰弹',reserve=32,reserve_max=64,automatic=False),
 dict(name='机枪',kind='gun',damage=30,delay=100,mag=100,reload=4200,pellets=1,range=45,
      headshot=2.,ammo='7.62毫米',reserve=200,reserve_max=400,automatic=True),
 dict(name='狙击枪',kind='gun',damage=160,delay=1450,mag=5,reload=2800,pellets=1,range=70,
      headshot=3.,ammo='狙击弹',reserve=20,reserve_max=40,automatic=False),
 # Returning blades / blink remain authored sci-fi abilities; slower handling
 # and distinct reach separate them from a fast automatic firearm.
 dict(name='刀剑',kind='melee',damage=90,delay=600,mag=0,reload=0,pellets=1,range=2.3,arc=1.9),
 dict(name='回旋刀',kind='melee',damage=100,delay=650,mag=0,reload=0,pellets=1,range=6.5,arc=.55),
 dict(name='贯穿长矛',kind='melee',damage=145,delay=950,mag=0,reload=0,pellets=1,range=11,arc=.42),
 dict(name='闪现短刃',kind='melee',damage=175,delay=850,mag=0,reload=0,pellets=1,range=3.2,arc=1.05),
]
SPECIALS = [
 ('melee_armor','近战·护体','持近战额外减伤 +8%（上限40%）',4),
 ('melee_sustain','近战·饮血','近战命中回血 +1（每0.4秒触发一次，上限8）',4),
 ('melee_regen','近战·复苏','持近战每秒回血 +0.5（上限5）',4),
 ('melee_reach','近战·延锋','刀剑范围及投掷射程 +15%（上限100%）',4),
 ('melee_guard','近战·坚守','防御额外减伤 +10%（总减伤上限75%）',4),
 ('melee_stagger','近战·震慑','近战命中减速30%，持续 +0.15秒（上限1.5秒）',4),
 ('melee_power','近战·淬刃','近战伤害 +20%',4),
 ('melee_haste','近战·迅捷','近战冷却 -15%',4),
 ('sword_arc','刀剑·裂空','刀剑攻击范围 +25%',4),
 ('boomerang_return','回旋刀·双刃回旋','回旋刀返回时伤害 +35%',5),
 ('spear_pierce','长矛·贯星','长矛贯穿伤害 +45%',6),
 ('dagger_dash','短刃·残影','短刃冲刺距离与伤害 +30%',7),
 ('blink_efficiency','闪现短刃·闪现节流','仅闪现短刃：闪现精力消耗 -20%',7),
 ('pellets','霰弹枪·分裂弹','霰弹枪增加弹丸',1),
 ('smg_haste','冲锋枪·疾速机匣','冲锋枪射速 +18%',0),
 ('smg_mag','冲锋枪·加长弹匣','冲锋枪弹匣 +8',0),
 ('shot_tight','霰弹枪·聚束枪管','霰弹散布收紧 20%',1),
 ('shot_power','霰弹枪·重型鹿弹','霰弹伤害 +20%',1),
 ('mg_power','机枪·压制弹链','机枪伤害 +18%',2),
 ('mg_reload','机枪·快拆弹箱','机枪换弹速度 +25%',2),
 ('sniper_power','狙击枪·反器材弹','狙击伤害 +25%',3),
 ('sniper_haste','狙击枪·直拉枪栓','狙击射速 +20%',3),
 ('orange_reset','击杀快攻','击杀任意敌人刷新冷却并加速',0),
]
UPGRADES += [(key,f'{tier}·{title}',desc,rank,scale) for key,title,desc,_ in SPECIALS for rank,(tier,color,scale) in enumerate(TIERS)]
# These two kill effects have fixed rarity, unrelated to enemy colors.
UPGRADES = [u for u in UPGRADES if u[0] not in ('blue_supply','orange_reset')]
# Kill-reward cards now scale by rarity like every other card.
UPGRADES += [(key,f'{tier}·{title}',upgrade_description(key,scale) if False else
              (f'击杀获得 {int(8*scale)} 备弹' if key=='blue_supply' else f'击杀刷新冷却；2秒内射速 +{8*scale:g}%'),rank,scale)
             for key,title in (('blue_supply','击杀补给'),('orange_reset','击杀快攻'))
             for rank,(tier,_,scale) in enumerate(TIERS)]


def upgrade_description(key, scale):
    """Match the gameplay calculations; percentages add within special effects."""
    pct = lambda base: f'{base * scale:g}%'
    descriptions = {
        'power': f'全枪伤害 +{pct(12)}',
        'haste': f'全枪射速 +{pct(10)}',
        'health': f'生命上限 +{int(15*scale)}，治疗 {25*scale:g}',
        'speed': f'移动速度 +{pct(6)}（上限8）',
        'magazine': f'全枪弹匣 +{int(3*scale)} 发',
        'reload': f'全枪装填速度 +{pct(10)}',
        'regen': f'每秒恢复 {0.3*scale:g} 生命',
        'leech': f'每次击杀恢复 {2*scale:g} 生命',
        'pierce': f'每发额外贯穿 {max(1,int(scale))} 个目标',
        'blast': f'命中溅射伤害 +{pct(12)}',
        'crit': f'暴击概率 +{pct(5)}（上限80%）',
        'critpower': f'暴击倍率 +{0.2*scale:g}',
        'armor': f'伤害减免 +{pct(4)}（上限70%）',
        'dodge': f'闪避概率 +{pct(3)}（上限50%）',
        'slow': f'命中减速 +{pct(10)}（上限75%）',
        'burn': f'灼烧强度 +{3*scale:g}',
        'poison': f'中毒强度 +{2*scale:g}',
        'execute': f'低血量敌人伤害 +{pct(20)}',
        'range': f'全枪射程 +{pct(15)}',
        'pellets': f'霰弹枪每发额外弹丸 +{int(scale)}',
        'heal': f'立即治疗 {30*scale:g} 生命',
        'xp': f'击杀经验 +{pct(10)}',
        'knockback': f'命中击退强度 +{0.2*scale:g}',
        'shield': f'每波获得 {15*scale:g} 护盾',
        'stamina_core': f'精力上限 +{int(15*scale)}',
        'stamina_regen': f'精力恢复速度 +{pct(18)}',
        'sprint_efficiency': f'冲刺精力消耗 -{pct(15)}',
        'blink_efficiency': f'仅闪现短刃：闪现精力消耗 -{pct(20)}（最低4点）',
        'smg_haste': f'仅冲锋枪射速 +{pct(18)}',
        'smg_mag': f'仅冲锋枪弹匣 +{int(8*scale)} 发',
        'shot_tight': f'霰弹聚束强度 +{pct(20)}',
        'shot_power': f'仅霰弹枪伤害 +{pct(20)}',
        'mg_power': f'仅机枪伤害 +{pct(18)}',
        'mg_reload': f'仅机枪装填速度 +{pct(25)}',
        'sniper_power': f'仅狙击枪伤害 +{pct(25)}',
        'sniper_haste': f'仅狙击枪射速 +{pct(20)}',
        'blue_supply': f'击杀给各枪补弹（冲锋枪{8*scale:g}发基准，其他按弹匣折算）',
        'orange_reset': f'击杀刷新冷却；2秒内射速 +{8*scale:g}%',
        'melee_power': '近战伤害 +20%', 'melee_haste': '近战冷却 -15%',
        'sword_arc': '刀剑攻击范围 +25%', 'boomerang_return': '回旋刀返回伤害 +35%',
        'spear_pierce': '长矛贯穿伤害 +45%', 'dagger_dash': '短刃冲刺距离与伤害 +30%',
    }
    if key in ('melee_armor','melee_sustain','melee_regen','melee_reach','melee_guard','melee_stagger'):
        values={'melee_armor':(8,'持近战额外减伤','%（上限40%）'),
                'melee_sustain':(1,'近战命中回血','（0.4秒冷却，上限8）'),
                'melee_regen':(.5,'持近战每秒回血','（上限5）'),
                'melee_reach':(15,'刀剑范围及投掷射程','%（上限100%）'),
                'melee_guard':(10,'防御额外减伤','%（总减伤上限75%）'),
                'melee_stagger':(.15,'命中减速30%，持续','秒（上限1.5秒）')}
        value,label,suffix=values[key]
        return f'{label} +{value*scale:g}{suffix}'
    return descriptions[key]


UPGRADES = [(key,title,upgrade_description(key,scale),rank,scale)
            for key,title,_,rank,scale in UPGRADES]

# Hybrid cards trade peak raw scaling for two complementary, implemented effects.
HYBRID_CARDS = {
    'field_medic':('战地医师','health','regen'),
    'vampire_armor':('血铠','armor','leech'),
    'mobile_gunner':('游击手','speed','reload'),
    'critical_feed':('精准供弹','crit','magazine'),
    'toxic_fire':('腐蚀烈焰','burn','poison'),
    'ice_breaker':('碎冰弹','slow','critpower'),
    'siege_round':('攻坚弹','pierce','power'),
    'blast_master':('爆破专家','blast','range'),
    'survivalist':('生存专家','shield','regen'),
    'executioner':('处刑者','execute','crit'),
    'battle_scholar':('战斗学者','xp','health'),
    'quick_hands':('快手','reload','haste'),
}
for key,(title,a,b) in HYBRID_CARDS.items():
    for rank,(tier,_,scale) in enumerate(TIERS):
        value=scale*.6
        UPGRADES.append((key,f'{tier}·{title}',upgrade_description(a,value)+'；'+upgrade_description(b,value),rank,scale))

# Expansion cards are opt-in: gameplay must implement a key before offering it.
# (key, title, description template, required owned item, category, base amount)
EXPANSION_EFFECTS = [
    ('turret_damage','炮台·穿甲弹','炮台伤害 +{percent}%', 'turret','building',.15),
    ('turret_rate','炮台·高速伺服','炮台射速 +{percent}%', 'turret','building',.12),
    ('turret_range','炮台·侦测阵列','炮台射程 +{percent}%', 'turret','building',.15),
    ('barricade_health','掩体·复合结构','掩体生命 +{percent}%', 'barricade','building',.25),
    ('barricade_thorns','掩体·反击装甲','接触掩体每秒伤害 +{value}', 'barricade','building',5),
    ('medstation_heal','医疗站·治疗增幅','医疗站每秒治疗 +{value}', 'medstation','building',1),
    ('terrain_slow','减速场·引力网','区域减速强度 +{percent}%', 'slowfield','terrain',.08),
    ('terrain_damage','火焰场·高温燃料','区域每秒伤害 +{value}', 'firefield','terrain',5),
    ('terrain_duration','战术场·持续模块','战术场持续时间 +{percent}%', 'field','terrain',.20),
    ('pet_damage','无人机·强化弹头','无人机伤害 +{percent}%', 'drone','pet',.15),
    ('pet_rate','无人机·高速机芯','无人机射速 +{percent}%', 'drone','pet',.12),
    ('pet_range','无人机·长程扫描','无人机射程 +{percent}%', 'drone','pet',.15),
    ('blade_damage','刀刃·淬火锋刃','近战刀伤害 +{percent}%', 'blade','melee',.20),
    ('blade_rate','刀刃·迅捷挥击','近战刀攻击速度 +{percent}%', 'blade','melee',.15),
    ('blade_leech','刀刃·生命收割','近战刀击杀回血 +{value}', 'blade','melee',2),
    ('guard_capacity','盾牌·能量核心','盾牌格挡容量 +{value}', 'guard','melee',15),
    ('guard_recovery','盾牌·快速回充','盾牌每秒回充 +{value}', 'guard','melee',2),
    ('smg_crit','冲锋枪·精密扳机','冲锋枪暴击率 +{percent}%', 0,'weapon',.04),
    ('shot_reload','霰弹枪·快速装填','霰弹枪装填速度 +{percent}%', 1,'weapon',.18),
    ('mg_mag','机枪·弹链扩容','机枪弹匣 +{integer} 发', 2,'weapon',12),
 ('sniper_pierce','狙击枪·贯穿弹','狙击枪额外贯穿 {integer} 个目标', 3,'weapon',1),
 ('blade_arc','战术刀·宽刃','战术刀攻击弧 +{percent}%', 4,'weapon',.20),
 ('guard_block','防暴盾·强化护板','防暴盾格挡 +{percent}%', 5,'weapon',.10),
 ('axe_power','重型战斧·破甲斩','重型战斧伤害 +{percent}%', 6,'weapon',.25),
 ('spear_reach','动力长矛·伸缩枪杆','动力长矛射程 +{percent}%', 7,'weapon',.25),
]


def expansion_description(template, amount, scale):
    value=amount*scale
    return template.format(percent=f'{value*100:g}',value=f'{value:g}',
                           integer=max(1,int(value)))


EXPANSION_UPGRADES = [
    (key,f'{tier}·{title}',expansion_description(template,amount,scale),rank,scale)
    for key,title,template,required,category,amount in EXPANSION_EFFECTS
    for rank,(tier,color,scale) in enumerate(TIERS)
]


def expansion_pool(implemented_keys, owned_weapons, owned_items):
    """Never offer a card with no implementation or without its required item."""
    eligible=set()
    for key,_,_,required,_,_ in EXPANSION_EFFECTS:
        owned=(required in owned_weapons) if isinstance(required,int) else (required in owned_items)
        if key in implemented_keys and owned:
            eligible.add(key)
    return [card for card in EXPANSION_UPGRADES if card[0] in eligible]


WEAPON_SLOT_COUNT=3
WAVE_MODIFIERS = [
    ('balanced','混合遭遇','常规近战与少量远程'),
    ('rush','疾跑突袭','疾跑敌人增加，保持近战多数'),
    ('armored','装甲小队','加入少量重装近战敌人'),
    ('ranged','远程支援','远程最多4名，保留近战多数'),
    ('boss','首领挑战','每五波首领与高品质战利品'),
]
