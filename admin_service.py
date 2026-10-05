"""Журнал действий администраторов (аудит)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin, AdminLog


async def log_action(
    db: AsyncSession,
    admin: Optional[Admin],
    action: str,
    *,
    target_type: Optional[str] = None,
    target_id: Optional[str | int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    commit: bool = True,
) -> AdminLog:
    entry = AdminLog(
        admin_id=admin.id if admin else None,
        admin_username=admin.username if admin else "system",
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    if commit:
        await db.commit()
    else:
        await db.flush()
    return entry


async def list_logs(
    db: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    admin_id: Optional[int] = None,
    action: Optional[str] = None,
) -> list[AdminLog]:
    stmt = select(AdminLog)
    if admin_id is not None:
        stmt = stmt.where(AdminLog.admin_id == admin_id)
    if action:
        stmt = stmt.where(AdminLog.action == action)
    stmt = stmt.order_by(AdminLog.created_at.desc()).limit(limit).offset(offset)
    return list((await db.execute(stmt)).scalars().all())
