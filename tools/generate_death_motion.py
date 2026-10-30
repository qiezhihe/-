"""Generate death sequences using current motion sheets as edit references."""
import base64,json,os,urllib.request
from generate_pixel_pack import OUT
from generate_full_motion import enemies

for name,description in enemies.items():
    target=OUT/('death_'+name+'.png')
    if target.exists(): continue
    reference=OUT/('motion_enemy_'+name+'.png')
    boundary='----PixelDeathReference'
    prompt=('Use the attached sprite sheet as the EXACT character identity reference. Produce exactly '
        '4 columns by 1 row, four equal cells, pure magenta background. Same '+description+
        '. Four death poses: stagger and knees buckle, collapse, fallen, motionless. '
        'Preserve equipment, palette, proportions and pixel style from the reference. No text, no effects, no shadow.')
    fields={'model':'gpt-image-2','prompt':prompt,'n':'1','size':'1024x1024'}
    chunks=[]
    for key,value in fields.items():
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="reference.png"\r\nContent-Type: image/png\r\n\r\n'.encode()+reference.read_bytes()+b'\r\n')
    chunks.append(f'--{boundary}--\r\n'.encode())
    request=urllib.request.Request('https://img-api.apinebula.ai/v1/images/edits',data=b''.join(chunks),headers={'Authorization':'Bearer '+os.environ['APINEBULA_API_KEY'],'Content-Type':'multipart/form-data; boundary='+boundary})
    try:
        with urllib.request.urlopen(request,timeout=300) as response: item=json.load(response)['data'][0]
        target.write_bytes(base64.b64decode(item['b64_json']))
        print(name+' saved',flush=True)
    except Exception as exc:
        print(name+' FAILED '+type(exc).__name__,flush=True)
        break
