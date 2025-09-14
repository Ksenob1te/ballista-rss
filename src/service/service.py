from . import DatabaseException, ExternalAPIException
from . import h2h_text_gen
from . import classic_text_gen
from ..postgre import H2HGameweekRepo, ClassicGameweekRepo, H2HGameweek, ClassicGameweek, PlayerGameweek
from .models import ClassicGameweekModel, H2HGameweekModel, PairResultModel, ContendersModel
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID
import logging
from typing import Dict, List

import json
import requests

WEBHOOK_URL = "https://n8n.ontext.info/webhook/106de94f-9628-49c4-bbde-4d48dfbcc173"


class RSSService:
    def __init__(self, database_conn: AsyncSession):
        self._database_conn = database_conn
        self._h2h_repo = H2HGameweekRepo(self._database_conn)
        self._classic_repo = ClassicGameweekRepo(self._database_conn)

        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_h2h_item(self, item: Dict) -> UUID:
        self.logger.debug("Validating incoming item league_id=%s gameweek=%s", item.get('league_id'),
                          item.get('gameweek'))
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

    async def generate_h2h_report(self, league_id: int, gameweek: int = None) -> str:
        self.logger.debug("Generating H2H report for league_id=%s gameweek=%s", league_id, gameweek)
        if gameweek is None:
            gw = await self._h2h_repo.get_last_n_gameweeks(league_id, 1)
            if gw:
                gw = gw[0]
        else:
            gw = await self._h2h_repo.get_by_gameweek(league_id, gameweek)
        if not gw:
            raise DatabaseException(f"H2H Gameweek not found league_id={league_id} gameweek={gameweek}")
        parts = [await h2h_text_gen.form_matches_info(gw)]
        parts.extend(await h2h_text_gen.form_top_info(gw))
        parts.append(await h2h_text_gen.form_top_diff(gw))
        parts.append(await h2h_text_gen.form_top_pts(gw))
        parts.append(await h2h_text_gen.form_leaderboard(gw))
        return "\n\n\n".join(parts)

    async def generate_h2h_json(self, league_id: int, gameweek: int = None) -> Dict:
        self.logger.debug("Generating H2H JSON for league_id=%s gameweek=%s", league_id, gameweek)
        if gameweek is None:
            gw = await self._h2h_repo.get_last_n_gameweeks(league_id, 1)
            if gw:
                gw = gw[0]
        else:
            gw = await self._h2h_repo.get_by_gameweek(league_id, gameweek)
        if not gw:
            raise DatabaseException(f"H2H Gameweek not found league_id={league_id} gameweek={gameweek}")
        parts: Dict[str, str] = {"gw": str(gw.gameweek), "matches_info": await h2h_text_gen.form_matches_info(gw)}
        top_info = await h2h_text_gen.form_top_info(gw)
        parts["top_performance"] = top_info[0]
        parts["top_ownership"] = top_info[1]
        parts["top_captains"] = top_info[2]
        parts["top_differential"] = await h2h_text_gen.form_top_diff(gw)
        parts["top_points"] = await h2h_text_gen.form_top_pts(gw)
        parts["leaderboard"] = await h2h_text_gen.form_leaderboard(gw)
        return parts

    async def generate_classic_report(self, league_id: int, gameweek: int = None) -> str:
        self.logger.debug("Generating Classic report for league_id=%s gameweek=%s", league_id, gameweek)
        if gameweek is None:
            gw = await self._classic_repo.get_last_n(league_id, 1)
            if gw:
                gw = gw[0]
        else:
            gw = await self._classic_repo.get_by_gameweek(league_id, gameweek)
        if not gw:
            raise DatabaseException(f"Classic Gameweek not found league_id={league_id} gameweek={gameweek}")
        parts = [await classic_text_gen.form_matches_info(gw)]
        parts.extend(await classic_text_gen.form_top_info(gw))
        return "\n\n\n".join(parts)

    async def generate_classic_json(self, league_id: int, gameweek: int = None) -> Dict:
        self.logger.debug("Generating Classic JSON for league_id=%s gameweek=%s", league_id, gameweek)
        if gameweek is None:
            gw = await self._classic_repo.get_last_n(league_id, 1)
            if gw:
                gw = gw[0]
        else:
            gw = await self._classic_repo.get_by_gameweek(league_id, gameweek)
        if not gw:
            raise DatabaseException(f"Classic Gameweek not found league_id={league_id} gameweek={gameweek}")
        parts: Dict[str, str] = {"gw": str(gw.gameweek), "matches_info": await classic_text_gen.form_matches_info(gw)}
        top_info = await classic_text_gen.form_top_info(gw)
        parts["top_performance"] = top_info[0]
        parts["top_ownership"] = top_info[1]
        parts["top_captains"] = top_info[2]
        return parts

    async def send_webhook(self, league_id: int, league_type: str, gameweek: int = None) -> None:
        if league_type == "h2h":
            data = await self.generate_h2h_json(league_id, gameweek)
        elif league_type == "classic":
            data = await self.generate_classic_json(league_id, gameweek)
        else:
            return
        data["type"] = league_type
        data["league_id"] = league_id
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ballista-rss-webhook-test/1.0"
        }
        try:
            self.logger.info("Sending payload to %s", WEBHOOK_URL)
            self.logger.debug("Payload data: %s", json_data)
            resp = requests.request("POST", WEBHOOK_URL, json=json_data, headers=headers, timeout=15)
        except requests.RequestException as e:
            raise ExternalAPIException(e)
        self.logger.info(f"Response webhook status: {resp.status_code}")
        ctype = resp.headers.get("Content-Type", "")
        if "json" in ctype.lower():
            try:
                self.logger.info(json.dumps(resp.json(), indent=2, ensure_ascii=False))
                return
            except Exception:
                pass
        self.logger.info(resp.text)
