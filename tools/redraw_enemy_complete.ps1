$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$designs = @{
 runner = 'genderless yellow-orange claw robot, pointed antennae, black mechanical joints, orange armor, three claw fingers, long mechanical legs'
 normal = 'male green armored alien infantry soldier, broad chest, green sealed helmet, mechanical claw, heavy boots, no exposed skin'
 shooter = 'nonhuman squat blue alien energy gunner, broad amphibian head, short sturdy legs, blue armored energy rifle, no human hair'
 tank = 'male massive blue ivory heavy armored guard, enclosed helmet, broad shoulders, heavy boots'
 elite = 'adult female violet crystal warrior, long silver lavender hair, purple crystalline armor, long purple spear'
 bat = 'nonhuman small violet alien bat, cyan mouth, two broad membranous wings, two short feet'
}
foreach ($name in @('runner','normal','shooter','tank','elite','bat')) {
 $target = Join-Path $root ('Assets/Art/pixel_portal_v1/source/cast_v3_' + $name + '.png')
 if (Test-Path -LiteralPath $target) { continue }
 $motion = 'Cells 1-8: eight consecutive frontal walking poses, obvious LEFT heel forward, left support right leg passing, right knee forward, right foot lowering, RIGHT heel forward, right support left leg passing, left knee forward, left foot lowering. Feet clearly separated, opposite arm swing, readable large leg motion. Always faces camera, no turning or mirrored torso.'
 if ($name -eq 'bat') { $motion = 'Cells 1-8: wing flap loop, wings fully UP, halfway down, horizontal, low, fully DOWN, halfway up, horizontal, high. Body center fixed, faces camera, only wings articulate, do not walk.' }
 $prompt = 'Premium anime 3D cel shaded game sprite sheet. EXACTLY FOUR columns FOUR rows, sixteen equal square cells. SAME SINGLE CHARACTER IN EVERY CELL: ' + $designs[$name] + '. ' + $motion + ' Cells 9-16: neutral idle, attack windup, attack strike, attack recovery, light hit reaction, heavy hit reaction, collapsing dying, fully fallen corpse lying on ground. All sixteen poses have IDENTICAL face, gender, colors, armor, equipment, limb count and body proportions. Front orthographic view facing player. Common scale and feet ground baseline, fixed torso center in all standing frames, generous padding, full silhouettes inside each cell. Pure uniform magenta #FF00FF background. No text, no grid lines, no shadow, no floor, no scene, no glow particles. No duplicate characters inside cells.'
 & 'C:\Users\qiezh\.codex\skills\apinebula-imagegen\run.ps1' -Prompt $prompt -OutFile $target
 if (-not (Test-Path -LiteralPath $target)) { throw ('Generation failed: ' + $name) }
}
