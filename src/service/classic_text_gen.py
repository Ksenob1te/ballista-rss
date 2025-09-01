from . import DatabaseException
from ..postgre import H2HGameweekRepo, ClassicGameweekRepo, H2HGameweek, ClassicGameweek, PlayerGameweek, H2HMatch
from .models import ClassicGameweekModel, H2HGameweekModel, PairResultModel, ContendersModel

from typing import Dict, List


async def form_matches_info(gw: ClassicGameweek) -> str:
    result_text = ""
    for contender in sorted(gw.contenders, key=lambda x: x.points, reverse=True):
        result_text += f"{contender.name} ({contender.leader}) {contender.points} pts\n"
        result_text += "Composition: "
        result_text += ", ".join(
            [f"{p.player_gameweek.name} {p.player_gameweek.team} ({p.factor * p.player_gameweek.points})" for p in
             sorted(
                 contender.composition_links, key=lambda x: x.factor * x.player_gameweek.points, reverse=True
             )])
        result_text += "\n\n"
    return result_text.strip()


async def form_top_info(gw: ClassicGameweek) -> List[str]:
    all_players: List[PlayerGameweek] = []
    captains_list: List[int] = []
    own_percent = {}

    for contender in gw.contenders:
        for link in contender.composition_links:
            if link.player_gameweek.player_id not in own_percent:
                all_players.append(link.player_gameweek)
            if link.factor == 2:
                captains_list.append(link.player_gameweek.player_id)
            own_percent[link.player_gameweek.player_id] = own_percent.get(link.player_gameweek.player_id, 0) + 1

    players_amount = len(own_percent.keys())

    top_5_performance = sorted(all_players, key=lambda x: x.points, reverse=True)[:5]
    top_5_ownership = sorted(all_players, key=lambda x: own_percent[x.player_id], reverse=True)[:5]
    top_5_captains = sorted(all_players, key=lambda x: x.points if x.player_id in captains_list else -999,
                            reverse=True)[:5]

    top_perf_text = f"TOP PRF (performance)\n"
    for index, player in enumerate(top_5_performance):
        top_perf_text += f"{index + 1}. {player.name} {player.team} ({player.points}) - {int(own_percent[player.player_id] / players_amount * 100)}%\n"

    top_own_text = f"TOP OWN (ownership)\n"
    for index, player in enumerate(top_5_ownership):
        top_own_text += f"{index + 1}. {player.name} {player.team} ({player.points}) - {int(own_percent[player.player_id] / players_amount * 100)}%\n"

    top_capt_text = f"TOP CPT (captains)\n"
    for index, player in enumerate(top_5_captains):
        if player.player_id in captains_list:
            top_capt_text += f"{index + 1}. {player.name} {player.team} ({player.points}) - {int(own_percent[player.player_id] / players_amount * 100)}%\n"
    return [top_perf_text.strip(), top_own_text.strip(), top_capt_text.strip()]