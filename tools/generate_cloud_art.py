"""User-authorized Qwen cloud art batch. Never log credentials."""
import json, urllib.request, urllib.error, urllib.parse, base64
from pathlib import Path
import time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Assets/Art/cloud_v1'
STYLE='Precise realistic sci-fi wasteland FPS game raster asset, consistent brushed dark metal, readable silhouette. No text, logos, panels, contact sheets. '
JOBS=[]
enemies={'runner':'slender orange armored fast robot, long mechanical legs and claw hands',
 'shooter':'blue accented mechanical rifle soldier aiming energy rifle toward viewer',
 'elite':'heavy gold accented armored elite mechanical warrior',
 'boss_fan':'giant wide red reactor war mech with multiple arm cannon barrels',
 'boss_dash':'giant sharp teal armored charging mech with back thrusters',
 'boss_ring':'floating purple reactor with eight circular weapon emitters'}
for name,subject in enemies.items():
    states=('idle','walk_left','walk_right','attack_ready','attack_swing','hit','dead')
    for state in states:
        pose={'idle':'standing ready','walk_left':'left foot forward walking','walk_right':'right foot forward walking',
              'attack_ready':'raising weapon preparing attack','attack_swing':'weapon attacking toward viewer',
              'hit':'recoiling slightly from chest impact','dead':'collapsed sideways on floor'}[state]
        JOBS.append((f'{name}_{state}',STYLE+f'{subject}, {pose}. Full body front eye-level view, all limbs visible, centered 85 percent height, pure white background, no ground shadow. Keep character design identical across poses.'))
weapons={'smg':'compact tactical submachine gun','shotgun':'thick barrel pump shotgun','mg':'heavy belt fed machine gun','sniper':'long scoped precision rifle','sword':'silver tactical sword blue energy edge','boomerang':'gold double edged returning boomerang','spear':'long silver spear cyan energy tip','dagger':'purple energy short dagger'}
for name,subject in weapons.items():
    JOBS.append(('weapon_'+name,STYLE+subject+'. First person player view from behind weapon, lower center, tip aimed upper center, complete weapon, no hands, pure white background. Not side-view product photography.'))
pets={'healer':'small green healing orb drone','taunter':'stationary gold armored decoy robot','gunner':'blue machine gun quadcopter drone','minelayer':'purple small mine laying robot dog','berserker':'red rage buff energy spirit'}
for name,subject in pets.items(): JOBS.append(('pet_'+name,STYLE+subject+', isolated complete subject front three-quarter view, white background.'))
import sys
sys.path.insert(0,str(ROOT))
from rogue_content import UPGRADES
for key,title,desc,rank,scale in UPGRADES:
    if not any(n=='icon_'+key for n,_ in JOBS):
        JOBS.append(('icon_'+key,STYLE+f'Single square game upgrade icon expressing {title}: {desc}. One centered recognizable object, white background, no letters or numbers.'))
for name,subject in {'floor':'top down concrete floor seamless tile, fine cracks, no frame', 'wall':'front orthographic steel wall seamless texture no perspective','lava':'top down bright molten lava covering whole tile, seamless, no safe dark banks','metal':'top down tactical metal plate seamless texture','health_frame':'horizontal empty health bar metal frame white background','boss_frame':'horizontal empty boss health bar armored frame white background','card_frame':'portrait empty upgrade card frame white background','slot_frame':'square empty weapon slot frame white background','pet_frame':'empty companion status panel white background'}.items():
    JOBS.append((name,STYLE+subject))

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'prompts.json').write_text(json.dumps(dict(JOBS),ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[s.strip() for s in (ROOT/'生图配置.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    origin=urllib.parse.urlsplit(lines[0]); endpoint=f'{origin.scheme}://{origin.netloc}/api/v1/services/aigc/multimodal-generation/generation'
    log=[]
    for name,prompt in JOBS:
        target=OUT/(name+'.png')
        if target.exists(): continue
        payload={'model':'qwen-image-2.0','input':{'messages':[{'role':'user','content':[{'text':prompt}]}]},'parameters':{'size':'1024*1024','n':1,'prompt_extend':False,'watermark':False}}
        request=urllib.request.Request(endpoint,json.dumps(payload).encode(),{'Authorization':'Bearer '+lines[1],'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=180) as response: result=json.load(response)
            items=result['output']['choices'][0]['message']['content']
            url=next(i['image'] for i in items if 'image' in i)
            # No API credentials are forwarded to asset hosting URLs.
            if url.startswith('data:'): data=base64.b64decode(url.split(',',1)[1])
            else:
                if urllib.parse.urlsplit(url).scheme!='https': raise ValueError('non-HTTPS image URL')
                with urllib.request.urlopen(url,timeout=60) as response: data=response.read()
            if not data.startswith((b'\x89PNG',b'\xff\xd8',b'RIFF')): raise ValueError('not an image')
            target.write_bytes(data); log.append({'name':name,'status':'saved','usage':result.get('usage')})
            print('saved',name,flush=True)
        except Exception as error:
            # Stop rather than spend credits repeatedly on a broken batch.
            log.append({'name':name,'status':'failed','type':type(error).__name__,'http':getattr(error,'code',None)})
            print('stopped',name,type(error).__name__,getattr(error,'code',''),flush=True)
            break
        finally:
            (OUT/'generation_log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Batch finished',flush=True)
if __name__=='__main__': run()
