from . import DatabaseException
from ..postgre import H2HGameweekRepo, ClassicGameweekRepo, H2HGameweek, ClassicGameweek, PlayerGameweek, H2HMatch
from .models import ClassicGameweekModel, H2HGameweekModel, PairResultModel, ContendersModel

from typing import Dict, List



async def form_matches_info(gw: H2HGameweek) -> str:
    results: List[PairResultModel] = []
    for match in gw.matches:
        intersect_amount = 0
        for p1 in match.first_contender.composition:
            for p2 in match.second_contender.composition:
                if p1.player_id == p2.player_id:
                    intersect_amount += 1
        total_players = max(len(match.first_contender.composition), len(match.second_contender.composition))
        similarity = intersect_amount / total_players if total_players > 0 else 0.

        first_top = [p.player_gameweek for p in sorted(
            match.first_contender.composition_links, key=lambda x: x.factor * x.player_gameweek.points,
            reverse=True
        )[:3]]
        second_top = [p.player_gameweek for p in sorted(
            match.second_contender.composition_links, key=lambda x: x.factor * x.player_gameweek.points,
            reverse=True
        )[:3]]

        first_captain = next((p.player_gameweek for p in match.first_contender.composition_links if p.factor == 2),
                             None)
        second_captain = next(
            (p.player_gameweek for p in match.second_contender.composition_links if p.factor == 2), None)

        validated = PairResultModel.model_validate({
            "first_name": match.first_contender.name,
            "first_leader": match.first_contender.leader,
            "first_score": match.first_contender.points,
            "first_captain": first_captain,
            "first_top": first_top,

            "second_name": match.second_contender.name,
            "second_leader": match.second_contender.leader,
            "second_score": match.second_contender.points,
            "second_top": second_top,
            "second_captain": second_captain,

            "similarity": similarity * 100,
        })
        results.append(validated)

    result_text = ""
    for res in results:
        result_text += f"{res.first_name} ({res.first_leader}) {res.first_score}:{res.second_score} {res.second_name} ({res.second_leader})\n"
        result_text += f"Similarity: {int(res.similarity)}%\n"
        if res.first_captain and res.second_captain:
            result_text += f"Captains: {res.first_captain.name} {res.first_captain.team} {res.first_captain.points * 2}:{res.second_captain.points * 2} {res.second_captain.name} {res.second_captain.team}\n"
        result_text += f"{res.first_name}: "
        result_text += ", ".join(
            [
                f"{p.name} {p.team} ({p.points})"
                if p.player_id != (res.first_captain.player_id if res.first_captain else -1)
                else f"{p.name} {p.team} ({p.points*2})"
                for p in res.first_top
            ]
        )
        result_text += f"\n{res.second_name}: "
        result_text += ", ".join(
            [
                f"{p.name} {p.team} ({p.points})"
                if p.player_id != (res.second_captain.player_id if res.second_captain else -1)
                else f"{p.name} {p.team} ({p.points*2})"
                for p in res.second_top
            ]
        )
        result_text += "\n\n"
    return result_text.strip()


async def form_top_info(gw: H2HGameweek) -> List[str]:
    all_players: List[PlayerGameweek] = []
    captains_list: List[int] = []
    own_percent = {}

    def add_player(_player: PlayerGameweek):
        if _player.player_id not in own_percent:
            all_players.append(_player)
        if p1.factor == 2:
            captains_list.append(_player.player_id)
        own_percent[_player.player_id] = own_percent.get(_player.player_id, 0) + 1

    for match in gw.matches:
        for p1 in match.first_contender.composition_links:
            add_player(p1.player_gameweek)
        for p2 in match.second_contender.composition_links:
            add_player(p2.player_gameweek)

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


async def form_top_diff(gw: H2HGameweek) -> str:
    top_match_diff: List[H2HMatch] = [match for match in sorted(gw.matches, key=lambda x: abs(x.first_contender.points - x.second_contender.points), reverse=True)[:3]]

    result_text = "TOP WIN\n"
    for match in top_match_diff:
        diff = abs(match.first_contender.points - match.second_contender.points)
        result_text += f"{diff}: {match.first_contender.name} {match.first_contender.points}:{match.second_contender.points} {match.second_contender.name}\n"
    return result_text.strip()

async def form_top_pts(gw: H2HGameweek) -> str:
    top_match_pts: List[H2HMatch] = [match for match in sorted(gw.matches, key=lambda x: x.first_contender.points + x.second_contender.points, reverse=True)[:3]]

    result_text = "TOP PTS\n"
    for match in top_match_pts:
        total = match.first_contender.points + match.second_contender.points
        result_text += f"{total}: {match.first_contender.name} {match.first_contender.points}:{match.second_contender.points} {match.second_contender.name}\n"
    return result_text.strip()

async def form_leaderboard(gw: H2HGameweek) -> str:
    result_text = "LEADERBOARD\n"
    for index, contender in enumerate(sorted(gw.contenders, key=lambda x: x.points, reverse=True)):
        result_text += f"{index + 1}. {contender.team.name} ({contender.team.leader}) {contender.points} pts\n"
    return result_text.strip()
