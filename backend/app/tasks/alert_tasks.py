"""
Celery tasks for retest and expiry alerts.
Uses synchronous DB access since Celery workers run synchronously.
"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.grn import GRN, GRNStatus
from app.models.notification import Notification, NotificationType
from app.models.user import User, Role
from app.tasks.celery_app import celery_app

_sync_engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)


def _get_target_user_ids(session: Session, department_keywords: list[str]) -> list:
    """Return user IDs belonging to given departments."""
    result = session.execute(
        select(User.id).where(
            User.is_active == True,
            User.deleted_at == None,
            User.department.in_(department_keywords),
        )
    )
    return [row[0] for row in result.all()]


@celery_app.task(name="app.tasks.alert_tasks.send_retest_alerts")
def send_retest_alerts():
    """Daily: notify when retesting_date is within 15 days."""
    threshold = date.today() + timedelta(days=15)

    with Session(_sync_engine) as session:
        grns = session.execute(
            select(GRN).where(
                GRN.status == GRNStatus.APPROVED,
                GRN.retesting_date != None,
                GRN.retesting_date <= threshold,
                GRN.retest_alert_sent == False,
                GRN.is_active == True,
            )
        ).scalars().all()

        if not grns:
            return {"sent": 0}

        target_users = _get_target_user_ids(session, ["QC", "Warehouse"])
        count = 0

        for grn in grns:
            for uid in target_users:
                session.add(Notification(
                    user_id=uid,
                    type=NotificationType.RETEST_ALERT,
                    title=f"Retest due: {grn.grn_number}",
                    body=(
                        f"Material {grn.item_code} batch {grn.batch_no} "
                        f"retesting date is {grn.retesting_date}."
                    ),
                    ref_type="grn",
                    ref_id=grn.id,
                ))
                count += 1

            grn.retest_alert_sent = True
            grn.retest_alert_sent_at = datetime.now(timezone.utc)

        session.commit()
        return {"sent": count}


@celery_app.task(name="app.tasks.alert_tasks.send_expiry_alerts")
def send_expiry_alerts():
    """Daily: notify when exp_date is within 30 days."""
    threshold = date.today() + timedelta(days=30)

    with Session(_sync_engine) as session:
        grns = session.execute(
            select(GRN).where(
                GRN.exp_date <= threshold,
                GRN.balance_qty > 0,
                GRN.is_active == True,
                GRN.deleted_at == None,
            )
        ).scalars().all()

        if not grns:
            return {"sent": 0}

        target_users = _get_target_user_ids(session, ["QC", "Warehouse"])
        count = 0

        for grn in grns:
            existing = session.execute(
                select(Notification.id).where(
                    Notification.ref_type == "grn",
                    Notification.ref_id == grn.id,
                    Notification.type == NotificationType.EXPIRY_ALERT,
                ).limit(1)
            ).scalar_one_or_none()

            if existing:
                continue

            for uid in target_users:
                session.add(Notification(
                    user_id=uid,
                    type=NotificationType.EXPIRY_ALERT,
                    title=f"Expiry alert: {grn.grn_number}",
                    body=(
                        f"Material {grn.item_code} batch {grn.batch_no} "
                        f"expires on {grn.exp_date}."
                    ),
                    ref_type="grn",
                    ref_id=grn.id,
                ))
                count += 1

        session.commit()
        return {"sent": count}
