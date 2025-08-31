from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any, Tuple
import logging
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert

from ..models import H2HGameweek, H2HContenders, H2HMatch, TeamGameweek, TeamGameweekPlayer
from .team_repo import TeamRepo
from .pydantic_model import ContendersModel, MatchesModel

from uuid import UUID

class H2HGameweekRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)
        self.team_repo = TeamRepo(session)

    async def get_by_gameweek(self, league_id: int, gameweek: int) -> Optional[H2HGameweek]:
        self.logger.debug("Fetching H2H gameweek league_id=%s gameweek=%s", league_id, gameweek)
        stmt = (
            select(H2HGameweek)
            .options(
                selectinload(H2HGameweek.matches)
                .selectinload(H2HMatch.first_contender)
                .selectinload(TeamGameweek.composition_links).selectinload(TeamGameweekPlayer.player_gameweek),
                selectinload(H2HGameweek.matches)
                .selectinload(H2HMatch.second_contender)
                .selectinload(TeamGameweek.composition_links).selectinload(TeamGameweekPlayer.player_gameweek),
                selectinload(H2HGameweek.contenders)
                .selectinload(H2HContenders.team)
                .selectinload(TeamGameweek.composition_links).selectinload(TeamGameweekPlayer.player_gameweek),
            )
            .where(H2HGameweek.league_id == league_id, H2HGameweek.gameweek == gameweek)
        )
        result = await self.session.execute(stmt)
        gw = result.scalar_one_or_none()
        if not gw:
            self.logger.info("H2H gameweek not found league_id=%s gameweek=%s", league_id, gameweek)
        return gw

    async def get_last_n_gameweeks(self, league_id: int, n: int) -> List[H2HGameweek]:
        self.logger.debug("Fetching last %s H2H gameweeks league_id=%s", n, league_id)
        stmt = (
            select(H2HGameweek)
            .options(
                selectinload(H2HGameweek.matches)
                .selectinload(H2HMatch.first_contender)
                .selectinload(TeamGameweek.composition_links).selectinload(TeamGameweekPlayer.player_gameweek),
                selectinload(H2HGameweek.matches)
                .selectinload(H2HMatch.second_contender)
                .selectinload(TeamGameweek.composition_links).selectinload(TeamGameweekPlayer.player_gameweek),
                selectinload(H2HGameweek.contenders)
                .selectinload(H2HContenders.team)
                .selectinload(TeamGameweek.composition_links).selectinload(TeamGameweekPlayer.player_gameweek),
            )
            .where(H2HGameweek.league_id == league_id)
            .order_by(H2HGameweek.gameweek.desc())
            .limit(n)
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        self.logger.info("Fetched %s H2H gameweeks league_id=%s", len(rows), league_id)
        return rows

    async def _upsert_h2h_gameweek(self, league_id: int, gameweek: int) -> Optional[UUID]:
        stmt = insert(H2HGameweek).values(league_id=league_id, gameweek=gameweek)
        stmt = stmt.on_conflict_do_update(
            index_elements=["league_id", "gameweek"],
            set_={"league_id": stmt.excluded.league_id}
        ).returning(H2HGameweek.id)
        result = await self.session.execute(stmt)
        rows = result.fetchall()
        if rows:
            gw_id = rows[0].id
            self.logger.debug("Upserted H2H gameweek id=%s league_id=%s gameweek=%s", gw_id, league_id, gameweek)
            return gw_id
        return None

    async def _clear_children_matches(self, gw: H2HGameweek) -> None:
        if not gw.matches:
            return
        for m in list(gw.matches):
            await self.session.delete(m)

    async def _upsert_matches(self, gameweek_model: H2HGameweek, teams_pairs: List[Tuple[UUID, UUID]]) -> None:
        amount = 0
        await self._clear_children_matches(gameweek_model)
        for first_id, second_id in teams_pairs:
            if not first_id or not second_id:
                continue
            amount += 1
            match = H2HMatch(
                h2h_gameweek_id=gameweek_model.id,
                first_contender_id=first_id,
                second_contender_id=second_id
            )
            self.session.add(match)
        await self.session.flush()
        self.logger.debug("Upserted %s H2H matches for gameweek_id=%s", amount, gameweek_model.id)

    async def _upsert_contenders(self, league_uuid: UUID, contenders: List[dict]) -> None:
        stmt = insert(H2HContenders).values([
            {
                'h2h_gameweek_id': league_uuid,
                'team_id': contender.get("team_uuid", None),
                'points': contender.get("score", None),
            }
            for contender in contenders
        ])
        stmt = stmt.on_conflict_do_update(
            index_elements=['h2h_gameweek_id', 'team_id'],
            set_={'points': stmt.excluded.points}
        )
        result = await self.session.execute(stmt)
        self.logger.debug("Upserted %s H2H contenders for gameweek_id=%s", result.rowcount, league_uuid)

    async def upsert_league(self, league_id: int, gameweek: int, matches: List[Dict[str, Any]], contenders: List[Dict[str, Any]]) -> UUID:
        for contender in contenders:
            contender['gameweek'] = gameweek
        contenders_models = [ContendersModel.model_validate(contender) for contender in contenders]
        matches_models = [MatchesModel.model_validate(match) for match in matches]

        teams_id_map = await self.team_repo.upsert_teams(contenders_models, update_points=False)
        gameweek_uuid = await self._upsert_h2h_gameweek(league_id, gameweek)
        _matches_pairs = [
            (teams_id_map.get(match.first_contender_id), teams_id_map.get(match.second_contender_id))
            for match in matches_models
            if teams_id_map.get(match.first_contender_id) and teams_id_map.get(match.second_contender_id)
        ]
        if not gameweek_uuid:
            raise Exception(f"Failed to upsert H2H gameweek league_id={league_id} gameweek={gameweek}")
        gameweek_model = await self.get_by_gameweek(league_id, gameweek)
        await self._upsert_matches(gameweek_model, _matches_pairs)

        _contenders_parts = [
            {
                "score": contender.score,
                "team_uuid": teams_id_map.get(contender.team_id)
            }
            for contender in contenders_models
            if teams_id_map.get(contender.team_id)
        ]
        await self._upsert_contenders(gameweek_uuid, _contenders_parts)

        self.logger.info(
            "Stored H2H gameweek league_id=%s gw=%s id=%s",
            league_id, gameweek, gameweek_uuid
        )
        return gameweek_uuid
