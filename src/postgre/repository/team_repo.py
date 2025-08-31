import logging
from typing import List, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from ..models import TeamGameweek, PlayerGameweek, TeamGameweekPlayer
from .pydantic_model import PlayerModel, ContendersModel

class TeamRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _upsert_team_players_link(self, team_id_map: Dict[int, UUID], player_id_map: Dict[int, UUID],
                                        team_models: List[ContendersModel], player_factor_map: Dict[int, int]) -> None:
        link_inserts = []
        for team_model in team_models:
            team_db_id = team_id_map.get(team_model.team_id)
            if not team_db_id:
                continue
            for player_model in team_model.composition:
                player_db_id = player_id_map.get(player_model.player_id)
                player_factor = player_factor_map.get(player_model.player_id, 1)
                if not player_db_id:
                    continue
                link_inserts.append({
                    'team_gameweek_id': team_db_id,
                    'player_gameweek_id': player_db_id,
                    'factor': player_factor
                })
        if not link_inserts:
            return
        stmt = insert(TeamGameweekPlayer).values(link_inserts)
        stmt = stmt.on_conflict_do_update(
            index_elements=['team_gameweek_id', 'player_gameweek_id'],
            set_={'factor': stmt.excluded.factor}
        )
        result = await self.session.execute(stmt)
        self.logger.debug("Inserted %s team-player links", result.rowcount)

    async def _upsert_players(self, player_models: List[PlayerModel]) -> Dict[int, UUID]:
        stmt = insert(PlayerGameweek).values(
            [
                {
                    'name': player_model.name,
                    'player_id': player_model.player_id,
                    'team': player_model.team,
                    'points': player_model.points,
                    'gameweek': player_model.gameweek
                } for player_model in player_models
            ]
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['player_id', 'team', 'gameweek'],
            set_={'points': stmt.excluded.points, 'name': stmt.excluded.name}
        )
        stmt = stmt.returning(PlayerGameweek.id, PlayerGameweek.player_id)
        result = await self.session.execute(stmt)
        rows = result.fetchall()
        self.logger.debug("Updated %s players", len(rows))
        player_id_map: Dict[int, UUID] = {
            row.player_id: row.id
            for row in rows
        }
        return player_id_map

    async def upsert_teams(self, team_models: List[ContendersModel], update_points: bool=True) -> Dict[int, UUID]:
        players_dict: Dict[int, PlayerModel] = {}
        for team_model in team_models:
            # players_list.extend(team_model.composition)
            for player in team_model.composition:
                players_dict[player.player_id] = player
                player.gameweek = team_model.gameweek

        player_id_map = await self._upsert_players(list(players_dict.values()))
        player_factor_map = {p.player_id: p.factor for p in players_dict.values()}
        stmt = insert(TeamGameweek).values(
            [
                {
                    'name': team_model.name,
                    'leader': team_model.leader,
                    'gameweek': team_model.gameweek,
                    'points': team_model.score,
                    'team_id': team_model.team_id
                } for team_model in team_models
            ]
        )
        update_set = {'name': stmt.excluded.name, 'leader': stmt.excluded.leader}
        if update_points:
            update_set['points'] = stmt.excluded.points
        stmt = stmt.on_conflict_do_update(
            index_elements=['team_id', 'gameweek'],
            set_=update_set
        )
        stmt = stmt.returning(TeamGameweek.id, TeamGameweek.team_id)
        result = await self.session.execute(stmt)
        rows = result.fetchall()
        team_id_map: Dict[int, UUID] = {
            row.team_id: row.id
            for row in rows
        }
        await self._upsert_team_players_link(team_id_map, player_id_map, team_models, player_factor_map)
        self.logger.debug("Upserted %s teams", len(rows))
        return team_id_map