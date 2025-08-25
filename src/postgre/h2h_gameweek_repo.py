from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from datetime import datetime, timezone
import logging

from .models import H2HGameweek


class H2HGameweekRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create(self, league_id: int, gameweek: int, matches: List[dict], standings: List[dict]) -> H2HGameweek:
        self.logger.debug("Creating gameweek league_id=%s gameweek=%s", league_id, gameweek)
        new_round = H2HGameweek(
            league_id=league_id,
            gameweek=gameweek,
            matches=matches,
            standings=standings
        )
        self.session.add(new_round)
        await self.session.commit()
        await self.session.refresh(new_round)
        self.logger.info("Created gameweek league_id=%s gameweek=%s id=%s", league_id, gameweek, new_round.id)
        return new_round

    async def get_by_gameweek(self, league_id: int, gameweek: int) -> Optional[H2HGameweek]:
        self.logger.debug("Fetching single gameweek league_id=%s gameweek=%s", league_id, gameweek)
        result = await self.session.execute(
            select(H2HGameweek).where(
                H2HGameweek.league_id == league_id,
                H2HGameweek.gameweek == gameweek
            )
        )
        return result.scalar_one_or_none()

    async def get_last_n(self, n: int, league_id: int) -> List[H2HGameweek]:
        self.logger.debug("Fetching last %s gameweeks for league_id=%s", n, league_id)
        stmt = (
            select(H2HGameweek)
            .where(H2HGameweek.league_id == league_id)
            .order_by(H2HGameweek.gameweek.desc())
            .limit(n)
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        self.logger.debug("Fetched %s gameweeks for league_id=%s", len(rows), league_id)
        return rows

    async def update(self, league_id: int, gameweek: int, matches: List[dict], standings: List[dict]) -> Optional[H2HGameweek]:
        self.logger.debug("Updating gameweek league_id=%s gameweek=%s", league_id, gameweek)
        round_obj = await self.get_by_gameweek(league_id, gameweek)
        if not round_obj:
            self.logger.warning("Update skipped; gameweek not found league_id=%s gameweek=%s", league_id, gameweek)
            return None
        round_obj.matches = matches
        round_obj.standings = standings
        self.session.add(round_obj)
        await self.session.commit()
        await self.session.refresh(round_obj)
        self.logger.info("Updated gameweek league_id=%s gameweek=%s id=%s", league_id, gameweek, round_obj.id)
        return round_obj

    async def upsert(self, league_id: int, gameweek: int, matches: List[dict], standings: List[dict]) -> H2HGameweek:
        self.logger.info("Upserting gameweek league_id=%s gameweek=%s", league_id, gameweek)
        round_obj = await self.get_by_gameweek(league_id, gameweek)
        if round_obj:
            return await self.update(league_id, gameweek, matches, standings)
        return await self.create(league_id, gameweek, matches, standings)

    async def delete(self, league_id: int, gameweek: int) -> bool:
        self.logger.debug("Deleting gameweek league_id=%s gameweek=%s", league_id, gameweek)
        round_obj = await self.get_by_gameweek(league_id, gameweek)
        if not round_obj:
            self.logger.warning("Delete skipped; gameweek not found league_id=%s gameweek=%s", league_id, gameweek)
            return False
        await self.session.delete(round_obj)
        await self.session.commit()
        self.logger.info("Deleted gameweek league_id=%s gameweek=%s", league_id, gameweek)
        return True
