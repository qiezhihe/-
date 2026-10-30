"""Remove confirmed character-containing FX, keeping recovery copies."""
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
folder=root/'Assets/Art/pixel_portal_v1/runtime'
targets=[folder/f'fx_boss_{kind}_{i}.png' for kind in ('charge','slam') for i in range(4)]
backup=root/'artifacts/art_cleanup/wrong_character_boss_fx.zip'
backup.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(backup,'a',zipfile.ZIP_DEFLATED) as archive:
 for path in targets:
  if path.exists():
   assert path.resolve().is_relative_to(folder.resolve())
   archive.write(path,path.relative_to(root).as_posix())
   path.unlink()
   print('Removed:',path.name)
