"""Remove only legacy enemy art whose active anime replacement is complete."""
from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Assets/Art/pixel_portal_v1'

def main():
    candidates = []
    for unit in ('normal','runner','shooter','tank','elite','bat'):
        complete=[ART/'runtime'/f'anime_enemy_{unit}_cast3_{i}.png' for i in range(16)]
        if all(p.is_file() for p in complete):
            for pattern in (f'anime_enemy_{unit}_locomotion_*.png',):
                candidates.extend((ART/'runtime').glob(pattern))
            for state in ('idle','walk_left','walk_right','attack_ready','attack_swing','attack_recover','hit','dead'):
                old=ART/'runtime'/f'anime_enemy_{unit}_{state}.png'
                if old.is_file(): candidates.append(old)
            for name in (f'anime_enemy_{unit}.png',f'locomotion_v2_{unit}.png'):
                old=ART/'source'/name
                if old.is_file(): candidates.append(old)
        replacement = [ART/'runtime'/f'anime_enemy_{unit}_locomotion_{i}.png' for i in range(8)]
        replacement += [ART/'runtime'/f'anime_enemy_{unit}_{state}.png' for state in ('idle','hit','dead','attack_ready','attack_swing','attack_recover')]
        if not all(p.is_file() for p in replacement):
            continue
        # EnemyArt always selects anime_enemy_<kind> when its idle exists;
        # the old motion_* cycles cannot be selected for these six units.
        candidates.extend((ART/'runtime').glob(f'{unit}_motion_*.png'))
        old_source = ART/'source'/f'motion_enemy_{unit}.png'
        if old_source.is_file(): candidates.append(old_source)
    folder = ROOT/'artifacts'/'art_cleanup'
    folder.mkdir(parents=True, exist_ok=True)
    candidates = sorted(set(candidates))
    # Append preserves recovery copies across resumable imports.
    backup = folder/'superseded_enemy_art.zip'
    with zipfile.ZipFile(backup,'a',zipfile.ZIP_DEFLATED) as archive:
        for path in candidates:
            resolved = path.resolve()
            if not resolved.is_relative_to(ART.resolve()): raise ValueError(path)
            archive.write(path,path.relative_to(ROOT).as_posix())
    report = folder/'removed.json'
    previous = json.loads(report.read_text(encoding='utf-8')) if report.exists() else []
    records = previous + [{'path':str(p.relative_to(ROOT)), 'bytes':p.stat().st_size,
                          'reason':'Superseded by active generated enemy animation set'} for p in candidates]
    report.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    for path in candidates: path.unlink()
    print(f'Removed {len(candidates)} superseded files; recovery archive: {backup}')

if __name__=='__main__': main()
