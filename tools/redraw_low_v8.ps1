$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
foreach($name in @('smg','guard')) {
 $target=Join-Path $root ('Assets/Art/pixel_portal_v1/source/low_v8_'+$name+'.png')
 if(Test-Path -LiteralPath $target){continue}
 $subject=if($name -eq 'smg'){'ONE compact blue gray 9mm MP5 submachine gun held LOW at hip ready, barrel nearly horizontal toward upper left, RIGHT hand pistol grip, LEFT hand forward handguard. Rear camera perspective identical to firing pose. NO raised arms, NO sight aiming, NO inspection pose, NO long stock displayed. Black unlit muzzle no fire smoke sparks.'}else{'LEFT hand holds compact blue shield raised slightly in front of left forearm, RIGHT hand short cyan sword at lower right. Small ordinary ready stance with shield lifted, NOT closeup shield, NOT full screen block. Exactly one sword one shield two navy gloved hands white cuffs.'}
 & 'C:\Users\qiezh\.codex\skills\apinebula-imagegen\run.ps1' -Prompt ('FPS weapon overlay anime 3D cel shaded. '+$subject+' ALL hands and equipment confined to BOTTOM RIGHT quadrant, top 55 percent and left 50 percent totally empty pure magenta #FF00FF. Small low silhouette, broad empty space above. No text grid scenery watermark.') -OutFile $target
 if(-not(Test-Path -LiteralPath $target)){throw $name}
}
