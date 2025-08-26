from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Dict, Tuple


class MatchesModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_contender: str
    second_contender: str
    first_score: Optional[int] = 0
    second_score: Optional[int] = 0

    first_standings: List[str]
    second_standings: List[str]

    # noinspection PyNestedDecorators
    @field_validator("first_standings", mode="before")
    @classmethod
    def validate_first_standings(cls, v):
        if isinstance(v, dict):
            return [f"{name} - {pts}" for name, pts in v.items()]
        return v

    # noinspection PyNestedDecorators
    @field_validator("second_standings", mode="before")
    @classmethod
    def validate_second_standings(cls, v):
        if isinstance(v, dict):
            return [f"{name} - {pts}" for name, pts in v.items()]
        return v

class H2HGameweekModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    league_id: int
    gameweek: int
    matches: List[MatchesModel]
    standings: List[Tuple[str, int]]

class ClassicContendersModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    score: int
    standings: List[str]

    # noinspection PyNestedDecorators
    @field_validator("standings", mode="before")
    @classmethod
    def validate_standings(cls, v):
        if isinstance(v, dict):
            return [f"{name} - {pts}" for name, pts in v.items()]
        return v

class ClassicGameweekModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    league_id: int
    gameweek: int
    contenders: List[ClassicContendersModel]