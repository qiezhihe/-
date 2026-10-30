$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$cast=@{
 colossus='towering basalt bronze humanoid with furnace hammer and ember fissures'
 hunter='ivory chitin crimson quadruped alien predator with hooked claws'
 judge='ceremonial armored marksman, crimson visor, ivory cloak, huge integrated cannon'
 weaver='huge six legged jade abyssal spider queen with luminous egg sacs'
 executioner='dark crowned knight with violet greatsword and battered bronze shield'
}
foreach($name in @('colossus','hunter','judge','weaver','executioner')) {
 $target=Join-Path $root ('Assets/Art/pixel_portal_v1/source/story_v1_'+$name+'.png')
 if(Test-Path -LiteralPath $target){continue}
 $prompt='Cinematic anime 3D cel shaded game storyboard, exactly TWO columns THREE rows, six equal wide cinematic panels in reading order, sequential events of ONE continuous encounter, consistent characters and location. Hero: original adult blue-haired scientist warrior white laboratory coat navy combat armor, navy gloves cyan wrist module. Boss: '+$cast[$name]+'. Dark blue space fortress arena. Panel 1 establishing shot hero enters deserted arena before boss wave. Panel 2 hero notices warning lights and ground cracks, turns toward disturbance. Panel 3 rift opens, boss silhouette emerges. Panel 4 boss fully arrives threatening hero, clear scale difference. Panel 5 over hero shoulder faceoff with boss, hero raises weapon ready. Panel 6 wide dramatic standoff with boss preparing first attack, segue to gameplay. Chronological narrative, each panel DIFFERENT event not repeated pose. No text, no captions, no UI, no borders, no logos. Same hero same boss in all relevant panels.'
 & 'C:\Users\qiezh\.codex\skills\apinebula-imagegen\run.ps1' -Prompt $prompt -OutFile $target -Size '1024x1792'
 if(-not(Test-Path -LiteralPath $target)){throw $name}
}
