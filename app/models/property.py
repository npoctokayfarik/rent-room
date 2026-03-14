from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_tg_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    district: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(64), default="apartment")
    status: Mapped[str] = mapped_column(String(64), default="active")
    price: Mapped[int] = mapped_column(Integer)
    rooms: Mapped[int] = mapped_column(Integer)
    floor: Mapped[int] = mapped_column(Integer)
    floors_total: Mapped[int] = mapped_column(Integer)
    contact_info: Mapped[str] = mapped_column(String(255), default="")
    amenities: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    images: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
