import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models import ClassicGameweek, TeamGameweek

class ClassicGameweekRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_by_gameweek(self, league_id: int, gameweek: int) -> Optional[ClassicGameweek]:
        self.logger.debug("Fetching classic gameweek league_id=%s gameweek=%s", league_id, gameweek)
        stmt = (
            select(ClassicGameweek)
            .options(selectinload(ClassicGameweek.standings))
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
            .options(selectinload(ClassicGameweek.standings))
            .where(ClassicGameweek.league_id == league_id)
            .order_by(ClassicGameweek.gameweek.desc())
            .limit(n)
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        self.logger.info("Fetched %s classic gameweeks for league_id=%s", len(rows), league_id)
        return rows

    async def _get_or_create(self, league_id: int, gameweek: int) -> Tuple[ClassicGameweek, bool]:
        existing = await self.get_by_gameweek(league_id, gameweek)
        if existing:
            return existing, False
        gw = ClassicGameweek(league_id=league_id, gameweek=gameweek)
        self.session.add(gw)
        await self.session.flush()
        return await self.get_by_gameweek(league_id, gameweek), True


    # async def _ensure_team(self, name: str, gameweek: int, points: int, composition: List[str]) -> TeamGameweek:
    #     stmt = select(TeamGameweek).where(TeamGameweek.name == name, TeamGameweek.gameweek == gameweek)
    #     team = await self.session.scalar(stmt)
    #     if not team:
    #         team = TeamGameweek(name=name, gameweek=gameweek, points=points, composition=composition)
    #         self.session.add(team)
    #         await self.session.flush()
    #     return team


    async def _create_team(self, name: str, gameweek: int, score: int, composition: List[str]) -> TeamGameweek:
        team = TeamGameweek(
            name=name,
            gameweek=gameweek,
            points=score,
            composition=composition
        )
        self.session.add(team)
        await self.session.flush()
        return team

    async def upsert_gameweek(self, league_id: int, gameweek: int, contenders: List[Dict[str, Any]]) -> ClassicGameweek:
        gw, created = await self._get_or_create(league_id, gameweek)
        existing_map = {t.name: t for t in gw.standings} if gw.standings else {}

        requested_teams = {c['name'] for c in contenders if c['name'] not in existing_map}
        if requested_teams:
            stmt = select(TeamGameweek).where(
                TeamGameweek.name.in_(requested_teams),
                TeamGameweek.gameweek == gameweek
            )
            result = await self.session.execute(stmt)
            for team in result.scalars().all():
                existing_map[team.name] = team

        added = 0
        updated = 0
        for contender in contenders:
            name = contender['name']
            score = contender['score']
            composition = contender.get('standings', [])
            team = existing_map.get(name)
            if team:
                team.points = score
                team.composition = composition
                updated += 1
            else:
                team = await self._create_team(name, gameweek, score, composition)
                existing_map[name] = team
                gw.standings.append(team)
                added += 1
            if team not in gw.standings:
                gw.standings.append(team)

        await self.session.flush()

        self.logger.info(
            "Upsert classic gameweek league_id=%s gw=%s id=%s added=%d updated=%d total_now=%d (created=%s)",
            league_id, gameweek, gw.id, added, updated, len(gw.standings), created
        )
        return gw

    async def create_or_replace(self, league_id: int, gameweek: int, contenders: List[Dict[str, Any]]) -> ClassicGameweek:
        return await self.upsert_gameweek(league_id, gameweek, contenders)
