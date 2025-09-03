from uuid import uuid4, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import TIMESTAMP, ForeignKey, Table, Column, UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from datetime import datetime, timezone
from . import Base
from typing import List

# team_gameweek_players = Table(
#     "team_gameweek_players",
#     Base.metadata,
#     Column("team_gameweek_id", ForeignKey("team_gameweek_table.id"), primary_key=True),
#     Column("player_gameweek_id", ForeignKey("player_gameweek_table.id"), primary_key=True)
# )

class TeamGameweekPlayer(Base):

    __tablename__ = "team_gameweek_players"

    team_gameweek_id: Mapped[UUID] = mapped_column(ForeignKey("team_gameweek_table.id"), primary_key=True)
    player_gameweek_id: Mapped[UUID] = mapped_column(ForeignKey("player_gameweek_table.id"), primary_key=True)
    factor: Mapped[int] = mapped_column(default=1, nullable=False)

    team_gameweek: Mapped["TeamGameweek"] = relationship(back_populates="composition_links", lazy="selectin")
    player_gameweek: Mapped["PlayerGameweek"] = relationship(lazy="selectin")

    def __repr__(self):
        return f"<TeamGameweekPlayer(team={self.team_gameweek_id}, player={self.player_gameweek_id}, factor={self.factor})>"



class PlayerGameweek(Base):
    __tablename__ = 'player_gameweek_table'
    __table_args__ = (UniqueConstraint('player_id', 'team', 'gameweek'),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    player_id: Mapped[int] = mapped_column(nullable=False)
    gameweek: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    team: Mapped[str] = mapped_column(nullable=False)
    points: Mapped[int] = mapped_column(nullable=False)

    def __repr__(self):
        return f"<PlayerGameweek(name={self.name}, team={self.team}, gameweek={self.gameweek})>"


class TeamGameweek(Base):
    __tablename__ = "team_gameweek_table"
    __table_args__ = (UniqueConstraint('team_id', 'gameweek'),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    team_id: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    leader: Mapped[str] = mapped_column(nullable=True)
    gameweek: Mapped[int] = mapped_column(nullable=False)
    points: Mapped[int] = mapped_column(nullable=False)

    composition_links: Mapped[List["TeamGameweekPlayer"]] = relationship(
        back_populates="team_gameweek",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    composition: List[PlayerGameweek] = association_proxy(
        "composition_links", "player_gameweek"
    )


    def __repr__(self):
        return f"<TeamGameweek(team_id={self.id}, gameweek_number={self.gameweek})>"


class H2HMatch(Base):
    __tablename__ = "h2h_match_table"

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


class H2HContenders(Base):
    __tablename__ = "h2h_contenders_table"
    __table_args__ = (UniqueConstraint('h2h_gameweek_id', 'team_id'),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    h2h_gameweek_id: Mapped[UUID] = mapped_column(ForeignKey("h2h_gameweek_table.id"), nullable=False)
    h2h_gameweek: Mapped["H2HGameweek"] = relationship(
        back_populates="contenders",
        lazy="selectin",
    )

    team_id: Mapped[UUID] = mapped_column(ForeignKey("team_gameweek_table.id"))
    team: Mapped["TeamGameweek"] = relationship()
    points: Mapped[int] = mapped_column(nullable=False)

    def __repr__(self):
        return f"<H2HContenders(team_id={self.team_id}, points={self.points})>"


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

    contenders: Mapped[List["TeamGameweek"]] = relationship(
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
    contenders: Mapped[List["H2HContenders"]] = relationship(back_populates="h2h_gameweek")

    def __repr__(self):
        return f"<H2HGameweek(gameweek_number={self.gameweek})>"
