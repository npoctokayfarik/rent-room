#токенизация делает вещи
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_admin
from app.models.property import Property
from app.schemas.property import PropertyCreate, PropertyListOut, PropertyOut, PropertyUpdate

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("", response_model=PropertyListOut)
async def list_properties(
    q: str | None = Query(default=None),
    district: str | None = Query(default=None),
    type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    min_price: int | None = Query(default=None, alias="minPrice"),
    max_price: int | None = Query(default=None, alias="maxPrice"),
    rooms: int | None = Query(default=None),
    sort: str | None = Query(default="newest"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PropertyListOut:
    stmt = select(Property)

    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Property.title.ilike(like),
                Property.description.ilike(like),
                Property.address.ilike(like),
            )
        )
    if district:
        stmt = stmt.where(Property.district == district)
    if type:
        stmt = stmt.where(Property.type == type)
    if status_filter:
        stmt = stmt.where(Property.status == status_filter)
    if min_price is not None:
        stmt = stmt.where(Property.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Property.price <= max_price)
    if rooms is not None:
        stmt = stmt.where(Property.rooms == rooms)

    if sort == "price_asc":
        stmt = stmt.order_by(Property.price.asc())
    elif sort == "price_desc":
        stmt = stmt.order_by(Property.price.desc())
    else:
        stmt = stmt.order_by(Property.created_at.desc())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()
    items = (await session.execute(stmt.offset(offset).limit(limit))).scalars().all()
    return PropertyListOut(items=items, total=total)


@router.get("/{property_id}", response_model=dict[str, PropertyOut])
async def get_property(property_id: int, session: AsyncSession = Depends(get_session)) -> dict[str, PropertyOut]:
    item = await session.get(Property, property_id)
    if not item:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"item": item}


@router.post("", response_model=dict[str, PropertyOut], dependencies=[Depends(require_admin)])
async def create_property(data: PropertyCreate, session: AsyncSession = Depends(get_session)) -> dict[str, PropertyOut]:
    item = Property(**data.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return {"item": item}


@router.patch("/{property_id}", response_model=dict[str, PropertyOut], dependencies=[Depends(require_admin)])
async def update_property(
    property_id: int,
    data: PropertyUpdate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, PropertyOut]:
    item = await session.get(Property, property_id)
    if not item:
        raise HTTPException(status_code=404, detail="Property not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    await session.commit()
    await session.refresh(item)
    return {"item": item}


@router.delete("/{property_id}", dependencies=[Depends(require_admin)])
async def delete_property(property_id: int, session: AsyncSession = Depends(get_session)) -> dict[str, bool]:
    item = await session.get(Property, property_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    await session.delete(item)
    await session.commit()
    return {"ok": True}
