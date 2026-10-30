"""Generate coherent held weapon poses using the configured cloud workflow."""
from generate_cloud_art import STYLE, run
import generate_cloud_art as batch
names={'smg':'compact tactical submachine gun','shotgun':'pump action shotgun','mg':'belt fed machine gun','sniper':'precision scoped rifle','sword':'silver blue energy sword','boomerang':'gold double blade boomerang','spear':'cyan tipped long spear','dagger':'purple energy dagger'}
batch.JOBS=[]
for name,subject in names.items():
    for pose in ('idle','attack','recover'):
        grip='two dark tactical gloved hands, right hand on grip trigger, left supporting fore-end' if name in ('smg','shotgun','mg','sniper') else 'one dark tactical gloved right hand firmly wrapped around handle'
        action={'idle':'held ready','attack':'firing with small muzzle flash and recoil' if name in ('smg','shotgun','mg','sniper') else 'mid slash or throwing release, dynamic wrist posture','recover':'recovering to ready after attack'}[pose]
        prompt=STYLE+f'{subject}, {grip}, {action}. First person actual player eye view from BEHIND weapon, not looking into muzzle, weapon points away upper left. Hands and weapon occupy lower right, clear center sight line. Same design proportions across poses. Complete wrist and weapon, flat pure white background. Anatomically correct fingers holding grip, no floating hands, no collage.'
        batch.JOBS.append((f'held_{name}_{pose}',prompt))
if __name__=='__main__': run()
