$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$out = Join-Path $root 'Assets/Art/pixel_portal_v1/source'
$designs = @{
 normal = 'adult female green armored alien infantry, short green hair, mechanical claw, sturdy boots'
 runner = 'yellow orange slim claw robot, pointed ear-like antennae, black joints, orange armor, three claw fingers, long mechanical legs'
 shooter = 'adult female blue alien energy gunner, blue hair, blue armored suit, compact energy rifle'
 tank = 'adult female broad blue ivory heavy armored guard, solid boots, bulky shoulder armor'
 elite = 'adult female violet crystal warrior, long silver lavender hair, purple crystalline armor, long purple spear'
 bat = 'small violet alien bat with cyan mouth, two large membranous wings'
}
foreach ($name in @('runner','elite','normal','shooter','tank','bat')) {
 $target = Join-Path $out ('locomotion_v2_' + $name + '.png')
 if (Test-Path -LiteralPath $target) { continue }
 $motion = 'Eight consecutive frames of ONE smooth forward walking cycle. Character ALWAYS faces camera directly, chest and face forward in every frame, zero yaw rotation. Frame 1 left heel contact right foot back; 2 left weight support right foot passing; 3 right knee forward; 4 right foot lowering; 5 right heel contact left foot back; 6 right support left foot passing; 7 left knee forward; 8 left foot lowering. Opposite arms counter swing. Feet separated sideways so both legs readable. No sideways walking, no spinning, no crossing legs. Head and pelvis stable. Same character, equipment and height in all cells.'
 if ($name -eq 'bat') { $motion = 'Eight consecutive frames of ONE wing flap cycle: wings high up, halfway down, horizontal, low down, fully down, halfway up, horizontal, high up. Face and chest ALWAYS face camera. Body center exactly fixed. Only symmetrical wings articulate at shoulder and elbow, no body rotation, no walking, no drifting.' }
 $prompt = 'Production game sprite sheet, premium anime 3D cel shaded render matching sci-fi fantasy game. Exactly FOUR columns TWO rows, eight equal square cells, reading order. Same ' + $designs[$name] + '. ' + $motion + ' Orthographic frontal camera, fixed scale and framing. Entire silhouette contained in each cell with generous padding. Foot ground baseline identical for grounded characters, torso registration identical. Pure flat magenta #FF00FF background, no shadow, no floor, no effects, no text, no labels, no watermark, no grid lines.'
 & 'C:\Users\qiezh\.codex\skills\apinebula-imagegen\run.ps1' -Prompt $prompt -OutFile $target
 if (-not (Test-Path -LiteralPath $target)) { throw ('Generation failed: ' + $name) }
}
