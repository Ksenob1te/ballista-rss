from . import DatabaseException
from ..postgre import H2HGameweekRepo
from .models import H2HGameweekModel
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID
import logging
from typing import Dict
from feedgen.feed import FeedGenerator


class RSSService:
    def __init__(self, database_conn: AsyncSession):
        self._database_conn = database_conn
        self._standings_repo = H2HGameweekRepo(self._database_conn)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_item(self, item: Dict) -> UUID:
        self.logger.debug("Validating incoming item league_id=%s gameweek=%s", item.get('league_id'), item.get('gameweek'))
        H2HGameweekModel.model_validate(item)
        self.logger.debug("Upserting item league_id=%s gameweek=%s", item['league_id'], item['gameweek'])
        h2h_field = await self._standings_repo.upsert(
            item["league_id"], item["gameweek"], item["matches"], item["standings"]
        )
        return h2h_field.id

    @staticmethod
    async def _generate_match_info(gameweek_model: H2HGameweekModel) -> str:
        result_str = ""
        for index, match in enumerate(gameweek_model.matches):
            result_str += f"{index + 1}. {match.first_contender} - {match.second_contender} {match.first_score}:{match.second_score}\n"

            result_str += "\n"
            result_str += f"{match.first_contender}:\n"
            for player, pts in match.first_standings.items():
                result_str += f"{player} - {pts}\n"
            result_str += f"{match.second_contender}:\n"
            for player, pts in match.second_standings.items():
                result_str += f"{player} - {pts}\n"
            result_str += "\n"
        return result_str

    @staticmethod
    async def _generate_standings(gameweek_model: H2HGameweekModel) -> str:
        result_str = "Standings:\n"
        for index, standing in enumerate(gameweek_model.standings):
            result_str += f"{index + 1}. {standing[0]} - {standing[1]} pts\n"
        return result_str


    async def generate_rss(self, league_id: str) -> str:
        gameweeks = await self._standings_repo.get_last_n(50, league_id=league_id)
        if not gameweeks:
            raise DatabaseException(f"No gameweeks found for league {league_id}")

        fg = FeedGenerator()
        fg.id(f"ballista:h2hstandings:{league_id}")
        fg.title(f"Ballista H2H Standings (League {league_id})")
        fg.link(href=f"http://localhost/rss/{league_id}", rel="self")
        fg.description("RSS feed for Ballista H2H Standings")
        fg.language("en")

        for gw in gameweeks:
            validated = H2HGameweekModel.model_validate(gw)
            fe = fg.add_entry()
            fe.id(f"ballista:h2hstandings:{validated.league_id}:{validated.gameweek}")
            fe.title(
                f"Gameweek {validated.gameweek} Standings"
            )
            fe.published(gw.date)
            content_obj = await self._generate_match_info(validated) + await self._generate_standings(validated)
            fe.content(content_obj, type="text")

        rss_bytes = fg.rss_str(pretty=True)
        return rss_bytes.decode("utf-8")
