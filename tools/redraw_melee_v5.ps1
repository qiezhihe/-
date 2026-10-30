$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$jobs=@{
 spear='ONE first person throwing spear ready pose. RIGHT navy gloved hand at far RIGHT grips one spear shaft behind its balance point, elbow pulled BACK beside right shoulder, spear tip pointing forward toward upper left, clear javelin windup ready to throw, left hand open forward for balance. White coat cuffs. Exactly one spear, no shield, no swords.'
 sword='FOUR columns TWO rows, eight equal cells. First person warrior with LEFT hand gripping ONE blue shield and RIGHT hand gripping ONE short cyan sword. Same equipment and arms all cells. Reading order: idle shield low sword lower right; windup; slash; followthrough; recovery; GUARD shield raised very close to camera filling left and center 70 percent of view, only tiny sword tip visible at extreme lower RIGHT; blocked impact shield raised; return idle. Anatomical hands, exactly ONE sword ONE shield, no guns, no extra blades, no full character.'
 bossfx='FOUR columns TWO rows eight equal cells. Pure abstract combat effects ONLY: orange hammer shockwave ring WITHOUT hammer; red claw ENERGY streaks WITHOUT claws; crimson cannon blast WITHOUT cannon; jade organic explosion WITHOUT creatures; violet sword ENERGY arc WITHOUT swords; warning rune; white armor sparks; orange disintegration smoke. ABSOLUTELY NO human, female figure, face, body, limbs, characters, silhouettes, weapons or swords in any cell.'
}
foreach($name in @('spear','sword','bossfx')) {
 $target=Join-Path $root ('Assets/Art/pixel_portal_v1/source/melee_v5_'+$name+'.png')
 if(Test-Path -LiteralPath $target){continue}
 $prompt='Premium anime 3D cel shaded sci fi game asset. '+$jobs[$name]+' Pure uniform magenta #FF00FF background, no text, no grid, no watermark, generous padding, consistent scale.'
 & 'C:\Users\qiezh\.codex\skills\apinebula-imagegen\run.ps1' -Prompt $prompt -OutFile $target
 if(-not(Test-Path -LiteralPath $target)){throw $name}
}
