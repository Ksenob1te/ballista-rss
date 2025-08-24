from uuid import uuid4, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from . import Base


class H2HGameweek(Base):
    __tablename__ = "h2h_gameweek_table"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    league_id: Mapped[str] = mapped_column(nullable=False)
    gameweek: Mapped[int] = mapped_column(nullable=False, unique=True)
    date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    matches: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    standings: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)

    def __repr__(self):
        return f"<H2HGameweek(gameweek_number={self.gameweek})>"