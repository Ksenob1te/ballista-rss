from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class PlayerModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    player_id: int
    team: str
    points: int
    factor: int
    gameweek: Optional[int] = None


class ContendersModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    leader: str
    team_id: int
    score: int
    gameweek: Optional[int]
    composition: List[PlayerModel]

class MatchesModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_contender_id: int
    second_contender_id: int
