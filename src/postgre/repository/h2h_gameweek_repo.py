from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any, Tuple
import logging
from sqlalchemy.orm import selectinload

from ..models import H2HGameweek, H2HStandings, H2HMatch, TeamGameweek

class H2HGameweekRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_by_gameweek(self, league_id: int, gameweek: int) -> Optional[H2HGameweek]:
        self.logger.debug("Fetching H2H gameweek league_id=%s gameweek=%s", league_id, gameweek)
        stmt = (
            select(H2HGameweek)
            .options(
                selectinload(H2HGameweek.matches).selectinload(H2HMatch.first_contender),
                selectinload(H2HGameweek.matches).selectinload(H2HMatch.second_contender),
                selectinload(H2HGameweek.standings).selectinload(H2HStandings.team),
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
                selectinload(H2HGameweek.matches).selectinload(H2HMatch.first_contender),
                selectinload(H2HGameweek.matches).selectinload(H2HMatch.second_contender),
                selectinload(H2HGameweek.standings).selectinload(H2HStandings.team),
            )
            .where(H2HGameweek.league_id == league_id)
            .order_by(H2HGameweek.gameweek.desc())
            .limit(n)
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        self.logger.info("Fetched %s H2H gameweeks league_id=%s", len(rows), league_id)
        return rows

    async def _get_or_create(self, league_id: int, gameweek: int) -> Tuple[H2HGameweek, bool]:
        gw = await self.get_by_gameweek(league_id, gameweek)
        if gw:
            return gw, False
        gw = H2HGameweek(league_id=league_id, gameweek=gameweek)
        self.session.add(gw)
        await self.session.flush()
        return gw, True

    async def _clear_children(self, gw: H2HGameweek) -> None:
        if not gw.matches and not gw.standings:
            return
        for m in list(gw.matches):
            await self.session.delete(m)
        for s in list(gw.standings):
            await self.session.delete(s)
        await self.session.flush()

    async def _ensure_team(self, name: str, gameweek: int, points: int, composition: List[str], cache: Dict[str, TeamGameweek]) -> TeamGameweek:
        team = cache.get(name)
        if team:
            team.points = points
            team.composition = composition
            return team
        stmt = select(TeamGameweek).where(TeamGameweek.name == name, TeamGameweek.gameweek == gameweek)
        team = await self.session.scalar(stmt)
        if not team:
            team = TeamGameweek(name=name, gameweek=gameweek, points=points, composition=composition)
            self.session.add(team)
            await self.session.flush()
        cache[name] = team
        return team

    async def _create_matches(self, gw: H2HGameweek, matches: List[Dict[str, Any]], cache: Dict[str, TeamGameweek]) -> int:
        created = 0
        for idx, match in enumerate(matches):
            try:
                first_name = match['first_contender']
                second_name = match['second_contender']
            except KeyError as ke:
                self.logger.warning("Skipping match idx=%d missing key=%s", idx, ke)
                continue
            first_score = int(match.get('first_score', 0) or 0)
            second_score = int(match.get('second_score', 0) or 0)
            first_list = list(match.get('first_standings', []) or [])
            second_list = list(match.get('second_standings', []) or [])
            first_team = await self._ensure_team(first_name, gw.gameweek, first_score, first_list, cache)
            second_team = await self._ensure_team(second_name, gw.gameweek, second_score, second_list, cache)
            self.session.add(H2HMatch(
                h2h_gameweek_id=gw.id,
                first_contender=first_team,
                second_contender=second_team,
            ))
            created += 1
        return created

    async def _create_standings(self, gw: H2HGameweek, standings: List[Tuple[str, int]], cache: Dict[str, TeamGameweek]) -> int:
        created = 0
        for idx, row in enumerate(standings):
            try:
                team_name, points = row
            except ValueError:
                self.logger.warning("Invalid standings row skipped idx=%d value=%s", idx, row)
                continue
            team = cache.get(team_name) or await self._ensure_team(team_name, gw.gameweek, 0, [], cache)
            self.session.add(H2HStandings(
                h2h_gameweek_id=gw.id,
                team=team,
                points=int(points)
            ))
            created += 1
        return created

    async def create_or_replace(self, league_id: int, gameweek: int, matches: List[Dict[str, Any]], standings: List[Tuple[str, int]]) -> H2HGameweek:
        gw, created = await self._get_or_create(league_id, gameweek)
        if not created:
            self.logger.info("Replacing existing gameweek league_id=%s gameweek=%s id=%s", league_id, gameweek, gw.id)
            team_cache: Dict[str, TeamGameweek] = {standing.team_id: standing.team for standing in gw.standings} if gw.standings else {}
            await self._clear_children(gw)
        else:
            self.logger.info("Created new gameweek league_id=%s gameweek=%s id=%s", league_id, gameweek, gw.id)
            team_cache: Dict[str, TeamGameweek] = {}

        match_count = await self._create_matches(gw, matches, team_cache)
        await self.session.flush()
        standings_count = await self._create_standings(gw, standings, team_cache)
        await self.session.flush()

        self.logger.info(
            "Stored H2H gameweek league_id=%s gw=%s id=%s matches=%d standings=%d (created=%s)",
            league_id, gameweek, gw.id, match_count, standings_count, created
        )
        return gw
