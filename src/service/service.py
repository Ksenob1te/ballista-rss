from . import DatabaseException
from ..postgre import H2HGameweekRepo, ClassicGameweekRepo, H2HGameweek, ClassicGameweek
from .models import ClassicGameweekModel, H2HGameweekModel
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID
import logging
from typing import Dict
from feedgen.feed import FeedGenerator


class RSSService:
    def __init__(self, database_conn: AsyncSession):
        self._database_conn = database_conn
        self._h2h_repo = H2HGameweekRepo(self._database_conn)
        self._classic_repo = ClassicGameweekRepo(self._database_conn)

        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_h2h_item(self, item: Dict) -> UUID:
        self.logger.debug("Validating incoming item league_id=%s gameweek=%s", item.get('league_id'), item.get('gameweek'))
        model = H2HGameweekModel.model_validate(item)
        self.logger.debug("Upserting item league_id=%s gameweek=%s", item['league_id'], item['gameweek'])
        h2h_gameweek_uuid = await self._h2h_repo.upsert_league(
            model.league_id, model.gameweek, [m.model_dump() for m in model.matches],
            [m.model_dump() for m in model.contenders]
        )
        return h2h_gameweek_uuid

    async def create_classic_item(self, item: Dict) -> UUID:
        self.logger.debug("Validating incoming item gameweek=%s", item['gameweek'])
        model = ClassicGameweekModel.model_validate(item)
        self.logger.debug("Upserting item league_id=%s gameweek=%s", item['league_id'], item['gameweek'])
        classic_field = await self._classic_repo.upsert_league(
            model.league_id, model.gameweek, [c.model_dump() for c in model.contenders]
        )
        return classic_field

    # @staticmethod
    # async def _generate_match_info(gameweek_model: H2HGameweekModel) -> str:
    #     result_str = ""
    #     for index, match in enumerate(gameweek_model.matches):
    #         result_str += f"{index + 1}. {match.first_contender} - {match.second_contender} {match.first_score}:{match.second_score}\n"
    #
    #         result_str += "\n"
    #         result_str += f"{match.first_contender}:\n"
    #         for player_info in match.first_standings:
    #             result_str += f"{player_info}\n"
    #         result_str += f"{match.second_contender}:\n"
    #         for player_info in match.second_standings:
    #             result_str += f"{player_info}\n"
    #         result_str += "\n"
    #     return result_str
    #
    # @staticmethod
    # async def _generate_standings(gameweek_model: H2HGameweekModel) -> str:
    #     result_str = "Standings:\n"
    #     for index, standing in enumerate(gameweek_model.standings):
    #         result_str += f"{index + 1}. {standing[0]} - {standing[1]} pts\n"
    #     return result_str
    #
    @staticmethod
    async def _gw_to_h2h_model(gw: H2HGameweek) -> H2HGameweekModel:
        validated = H2HGameweekModel.model_validate({
            "league_id": gw.league_id,
            "gameweek": gw.gameweek,
            "matches": [
                {
                    "first_contender": match.first_contender.name,
                    "second_contender": match.second_contender.name,
                    "first_score": match.first_contender.points,
                    "second_score": match.second_contender.points,
                    "first_standings": match.first_contender.composition,
                    "second_standings": match.second_contender.composition,
                }
                for match in gw.matches
            ],
            "standings": [(s.team.name, s.points) for s in sorted(gw.contenders, key=lambda x: x.points, reverse=True)],
        })
        return validated

    @staticmethod
    async def _gw_to_classic_model(gw: ClassicGameweek) -> ClassicGameweekModel:
        validated = ClassicGameweekModel.model_validate({
            "league_id": gw.league_id,
            "gameweek": gw.gameweek,
            "contenders": [
                {
                    "name": contender.name,
                    "score": contender.points,
                    "composition": contender.composition,
                }
                for contender in gw.contenders
            ],
        })
        return validated
    #
    # async def generate_h2h_dict(self, league_id: int, n: int=1) -> Dict:
    #     gameweeks = await self._h2h_repo.get_last_n_gameweeks(league_id=league_id, n=n)
    #     if not gameweeks:
    #         raise DatabaseException(f"No gameweeks found for league {league_id}")
    #     result = {
    #         "type": "h2h",
    #         "gameweeks": []
    #     }
    #     for gw in gameweeks:
    #         validated = await self._gw_to_h2h_model(gw)
    #         result["gameweeks"].append(validated.model_dump())
    #     return result
    #
    # async def generate_classic_dict(self, league_id: int, n: int=1) -> Dict:
    #     gameweeks = await self._classic_repo.get_last_n(league_id=league_id, n=n)
    #     if not gameweeks:
    #         raise DatabaseException(f"No gameweeks found for league {league_id}")
    #     result = {
    #         "type": "classic",
    #         "gameweeks": []
    #     }
    #     for gw in gameweeks:
    #         validated = await self._gw_to_classic_model(gw)
    #         result["gameweeks"].append(validated.model_dump())
    #     return result
    #
    # async def generate_h2h_rss(self, league_id: int) -> str:
    #     gameweeks = await self._h2h_repo.get_last_n_gameweeks(league_id=league_id, n=50)
    #     if not gameweeks:
    #         raise DatabaseException(f"No gameweeks found for league {league_id}")
    #
    #     fg = FeedGenerator()
    #     fg.id(f"ballista:h2hstandings:{league_id}")
    #     fg.title(f"Ballista H2H Standings (League {league_id})")
    #     fg.link(href=f"http://localhost/rss/{league_id}", rel="self")
    #     fg.description("RSS feed for Ballista H2H Standings")
    #     fg.language("en")
    #
    #     for gw in gameweeks:
    #         validated = await self._gw_to_h2h_model(gw)
    #         fe = fg.add_entry()
    #         fe.id(f"ballista:h2hstandings:{validated.league_id}:{validated.gameweek}")
    #         fe.title(
    #             f"Gameweek {validated.gameweek} Standings"
    #         )
    #         fe.published(gw.date)
    #         content_obj = await self._generate_match_info(validated) + await self._generate_standings(validated)
    #         fe.content(content_obj, type="text")
    #
    #     rss_bytes = fg.rss_str(pretty=True)
    #     return rss_bytes.decode("utf-8")
    #
    # async def generate_classic_rss(self, league_id: int) -> str:
    #     gameweeks = await self._classic_repo.get_last_n(league_id=league_id, n=50)
    #     if not gameweeks:
    #         raise DatabaseException(f"No gameweeks found for league {league_id}")
    #
    #     fg = FeedGenerator()
    #     fg.id(f"ballista:classicstandings:{league_id}")
    #     fg.title(f"Ballista Classic Standings (League {league_id})")
    #     fg.link(href=f"http://localhost/rss/classic/{league_id}", rel="self")
    #     fg.description("RSS feed for Ballista Classic Standings")
    #     fg.language("en")
    #
    #     for gw in gameweeks:
    #         validated = await self._gw_to_classic_model(gw)
    #         fe = fg.add_entry()
    #         fe.id(f"ballista:classicstandings:{validated.league_id}:{validated.gameweek}")
    #         fe.title(
    #             f"Gameweek {validated.gameweek} Standings"
    #         )
    #         fe.published(gw.date)
    #         content_str = "Standings:\n"
    #         for index, contender in enumerate(sorted(validated.contenders, key=lambda x: x.score, reverse=True)):
    #             content_str += f"{index + 1}. {contender.name} - {contender.score} pts\n"
    #             for player_info in contender.standings:
    #                 content_str += f"{player_info}\n"
    #             content_str += "\n"
    #         fe.content(content_str, type="text")
    #
    #     rss_bytes = fg.rss_str(pretty=True)
    #     return rss_bytes.decode("utf-8")


