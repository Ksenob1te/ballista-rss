import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from ..models import ClassicGameweek, TeamGameweek, TeamGameweekPlayer, classic_gameweek_teams
from .pydantic_model import PlayerModel, ContendersModel

from .team_repo import TeamRepo


class ClassicGameweekRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)
        self.team_repo = TeamRepo(session)

    async def get_by_gameweek(self, league_id: int, gameweek: int) -> Optional[ClassicGameweek]:
        self.logger.debug("Fetching classic gameweek league_id=%s gameweek=%s", league_id, gameweek)
        stmt = (
            select(ClassicGameweek)
            .options(
                selectinload(ClassicGameweek.contenders)
                .selectinload(TeamGameweek.composition_links).selectinload(TeamGameweekPlayer.player_gameweek)
            )
            .where(ClassicGameweek.league_id == league_id, ClassicGameweek.gameweek == gameweek)
        )
        result = await self.session.execute(stmt)
        gw = result.scalar_one_or_none()
        if gw:
            self.logger.debug("Found classic gameweek id=%s", gw.id)
        else:
            self.logger.debug("Classic gameweek not found league_id=%s gameweek=%s", league_id, gameweek)
        return gw

    async def get_last_n(self, league_id: int, n: int) -> List[ClassicGameweek]:
        self.logger.debug("Fetching last %s classic gameweeks for league_id=%s", n, league_id)
        stmt = (
            select(ClassicGameweek)
            .options(
                selectinload(ClassicGameweek.contenders)
                .selectinload(TeamGameweek.composition_links).selectinload(TeamGameweekPlayer.player_gameweek)
            )
            .where(ClassicGameweek.league_id == league_id)
            .order_by(ClassicGameweek.gameweek.desc())
            .limit(n)
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        self.logger.info("Fetched %s classic gameweeks for league_id=%s", len(rows), league_id)
        return rows

    async def _upsert_classic_gameweek(self, league_id: int, gameweek: int) -> Optional[UUID]:
        stmt = insert(ClassicGameweek).values(league_id=league_id, gameweek=gameweek)
        stmt = stmt.on_conflict_do_update(
            index_elements=["league_id", "gameweek"],
            set_={"league_id": stmt.excluded.league_id}
        ).returning(ClassicGameweek.id)
        result = await self.session.execute(stmt)
        rows = result.fetchall()
        if rows:
            gw_id = rows[0].id
            self.logger.debug("Upserted classic gameweek id=%s league_id=%s gameweek=%s", gw_id, league_id, gameweek)
            return gw_id
        self.logger.error("Failed to upsert classic gameweek league_id=%s gameweek=%s", league_id, gameweek)
        return None

    async def _upsert_league_players_link(self, league_uuid, teams_id_map: Dict[int, UUID]) -> None:
        link_inserts = [
            {
                'classic_gameweek_id': league_uuid,
                'team_id': team_db_id
            }
            for team_db_id in teams_id_map.values()
        ]
        stmt = insert(classic_gameweek_teams).values(link_inserts)
        stmt = stmt.on_conflict_do_nothing()
        result = await self.session.execute(stmt)
        self.logger.debug("Inserted %s classic gameweek-team links", result.rowcount)


    async def upsert_league(self, league_id: int, gameweek: int, contenders: List[Dict[str, Any]]) -> UUID:
        for contender in contenders:
            contender['gameweek'] = gameweek
        contenders_models = [ContendersModel.model_validate(contender) for contender in contenders]
        league_uuid = await self._upsert_classic_gameweek(league_id, gameweek)
        teams_id_map = await self.team_repo.upsert_teams(contenders_models)
        if not league_uuid:
            raise Exception(f"Failed to upsert classic gameweek league_id={league_id} gameweek={gameweek}")
        await self._upsert_league_players_link(league_uuid, teams_id_map)
        await self.session.flush()

        self.logger.info(
            "Upsert classic gameweek league_id=%s gw=%s id=%s",
            league_id, gameweek, league_uuid
        )
        return league_uuid
