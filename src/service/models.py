from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Tuple


class MatchesModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_contender: str
    second_contender: str
    first_score: Optional[int] = 0
    second_score: Optional[int] = 0

    first_standings: Dict[str, int]
    second_standings: Dict[str, int]

class H2HGameweekModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    league_id: int
    gameweek: int
    matches: List[MatchesModel]
    standings: List[Tuple[str, int]]