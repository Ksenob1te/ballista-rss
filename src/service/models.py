from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Dict, Tuple

class PlayerModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    player_id: int
    factor: int
    team: str
    points: int

class ContendersModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    leader: str
    team_id: int
    score: int
    composition: List[PlayerModel]

class ClassicGameweekModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    league_id: int
    gameweek: int
    contenders: List[ContendersModel]


class MatchesModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_contender_id: int
    second_contender_id: int

class H2HGameweekModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    league_id: int
    gameweek: int
    matches: List[MatchesModel]
    contenders: List[ContendersModel]

# class MatchesModel(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#
#     first_contender: str
#     second_contender: str
#     first_score: Optional[int] = 0
#     second_score: Optional[int] = 0
#
#     first_standings: List[str]
#     second_standings: List[str]
#
#     # noinspection PyNestedDecorators
#     @field_validator("first_standings", mode="before")
#     @classmethod
#     def validate_first_standings(cls, v):
#         if isinstance(v, dict):
#             return [f"{name} - {pts}" for name, pts in v.items()]
#         return v
#
#     # noinspection PyNestedDecorators
#     @field_validator("second_standings", mode="before")
#     @classmethod
#     def validate_second_standings(cls, v):
#         if isinstance(v, dict):
#             return [f"{name} - {pts}" for name, pts in v.items()]
#         return v
#
#
# class ClassicContendersModel(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#
#     name: str
#     score: int
#     standings: List[str]
#
#     # noinspection PyNestedDecorators
#     @field_validator("standings", mode="before")
#     @classmethod
#     def validate_standings(cls, v):
#         if isinstance(v, dict):
#             return [f"{name} - {pts}" for name, pts in v.items()]
#         return v
#
# class ClassicGameweekModel(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#
#     league_id: int
#     gameweek: int
#     contenders: List[ClassicContendersModel]
#     standings: List[H2HStandingModel]
