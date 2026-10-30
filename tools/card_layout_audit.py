"""Audit card text using the exact release font and card layout constraints."""
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from fps_game import Game
from rogue_content import UPGRADES,WEAPONS


def main():
    game=Game()
    cards=list(UPGRADES)+[(f'unlock{i}',f'解锁·{weapon["name"]}',
                            '获得新枪械，数字键切换',1,1)
                           for i,weapon in enumerate(WEAPONS) if i]
    details=[]
    for key,title,description,rank,scale in cards:
        lines=[]
        current=''
        for char in description:
            if current and game.card_font.size(current+char)[0]>255:
                lines.append(current)
                current=char
            else:
                current+=char
        if current: lines.append(current)
        title_width=game.card_font.size('3  '+title)[0]
        details.append(dict(key=key,rank=rank,title_width=title_width,
                            title_scaled=title_width>255,description_lines=len(lines),
                            description_truncated=len(lines)>3))
    assert not any(row['description_truncated'] for row in details)
    random.seed(8921)
    counts=Counter()
    for _ in range(10000):
        game.offer_upgrade(True)
        assert len({c[0] for c in game.choices})==3
        assert all(not c[0].startswith('unlock') for c in game.choices)
        counts.update(c[3] for c in game.choices)
    assert counts[0]==0
    result=dict(cards_audited=len(details),
                max_title_width=max(row['title_width'] for row in details),
                scaled_titles=sum(row['title_scaled'] for row in details),
                max_description_lines=max(row['description_lines'] for row in details),
                truncated_descriptions=0,
                boss_samples=sum(counts.values()),
                boss_quality_counts=dict(counts),
                boss_high_quality_ratio=(counts[2]+counts[3])/sum(counts.values()))
    print(json.dumps(result,ensure_ascii=True,indent=2))
    pygame.quit()


if __name__=='__main__':
    main()
