from uuid import uuid4, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import TIMESTAMP, ForeignKey, Table, Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from . import Base
from typing import List


class TeamGameweek(Base):
    __tablename__ = "team_gameweek_table"
    __table_args__ = (UniqueConstraint('name', 'gameweek'),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    gameweek: Mapped[int] = mapped_column(nullable=False)
    points: Mapped[int] = mapped_column(nullable=False)
    composition: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    def __repr__(self):
        return f"<TeamGameweek(team_id={self.id}, gameweek_number={self.gameweek})>"

class H2HMatch(Base):
    __tablename__ = "h2hmatch_table"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    h2h_gameweek_id: Mapped[UUID] = mapped_column(ForeignKey("h2h_gameweek_table.id"), nullable=False)
    h2h_gameweek: Mapped["H2HGameweek"] = relationship(
        back_populates="matches",
        lazy="selectin",
    )

    first_contender_id: Mapped[UUID] = mapped_column(ForeignKey("team_gameweek_table.id"))
    second_contender_id: Mapped[UUID] = mapped_column(ForeignKey("team_gameweek_table.id"))

    first_contender: Mapped["TeamGameweek"] = relationship(
        foreign_keys=[first_contender_id]
    )
    second_contender: Mapped["TeamGameweek"] = relationship(
        foreign_keys=[second_contender_id]
    )

    def __repr__(self):
        return f"<H2HMatch({self.first_contender_id} vs {self.second_contender_id})>"

class H2HStandings(Base):
    __tablename__ = "h2hstandings_table"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    h2h_gameweek_id: Mapped[UUID] = mapped_column(ForeignKey("h2h_gameweek_table.id"), nullable=False)
    h2h_gameweek: Mapped["H2HGameweek"] = relationship(
        back_populates="standings",
        lazy="selectin",
    )

    team_id: Mapped[UUID] = mapped_column(ForeignKey("team_gameweek_table.id"))
    team: Mapped["TeamGameweek"] = relationship()
    points: Mapped[int] = mapped_column(nullable=False)

    def __repr__(self):
        return f"<H2HStandings(team_id={self.team_id}, points={self.points})>"

classic_gameweek_teams = Table(
    "classic_gameweek_teams",
    Base.metadata,
    Column("classic_gameweek_id", ForeignKey("classic_gameweek_table.id"), primary_key=True),
    Column("team_id", ForeignKey("team_gameweek_table.id"), primary_key=True)
)

class ClassicGameweek(Base):
    __tablename__ = "classic_gameweek_table"
    __table_args__ = (UniqueConstraint('league_id', 'gameweek'),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    league_id: Mapped[int] = mapped_column(nullable=False)
    gameweek: Mapped[int] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    standings: Mapped[List["TeamGameweek"]] = relationship(
        "TeamGameweek",
        secondary=classic_gameweek_teams,
        lazy="selectin"
    )

    def __repr__(self):
        return f"<ClassicGameweek(gameweek_number={self.gameweek})>"

class H2HGameweek(Base):
    __tablename__ = "h2h_gameweek_table"
    __table_args__ = (UniqueConstraint('league_id', 'gameweek'),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    league_id: Mapped[int] = mapped_column(nullable=False)
    gameweek: Mapped[int] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    matches: Mapped[List["H2HMatch"]] = relationship(back_populates="h2h_gameweek")
    standings: Mapped[List["H2HStandings"]] = relationship(back_populates="h2h_gameweek")

    def __repr__(self):
        return f"<H2HGameweek(gameweek_number={self.gameweek})>"
