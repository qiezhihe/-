$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$designs=@{smg='compact blue gray submachine gun';mg='belt fed dark teal machine gun';sniper='long cyan scoped sniper rifle'}
foreach ($name in @('smg','mg','sniper')) {
 $target=Join-Path $root ('Assets/Art/pixel_portal_v1/source/idle_clean_v4_'+$name+'.png')
 if (Test-Path -LiteralPath $target) {continue}
 $prompt='Single isolated first person game weapon sprite, premium anime 3D cel shaded render. '+$designs[$name]+', two navy armored gloves and white laboratory coat cuffs, cyan wrist module. Relaxed static ready stance, gun lower right pointing toward upper left, entire gun and both hands inside frame with padding, upper left mostly empty. Unfired weapon, black unlit open muzzle, solid opaque metal barrel. NO muzzle flash, NO flame, NO fire, NO sparks, NO smoke, NO light rays, NO projectile, NO glowing muzzle, NO recoil. This is a calm IDLE inventory pose. Pure uniform magenta #FF00FF background, no scene, no text, no watermark, no grid, square composition.'
 & 'C:\Users\qiezh\.codex\skills\apinebula-imagegen\run.ps1' -Prompt $prompt -OutFile $target
 if (-not (Test-Path -LiteralPath $target)) {throw ('Generation failed '+$name)}
}
