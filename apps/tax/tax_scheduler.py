"""税/回収/ローンの定期実行スケジューラ。

- 週次: 日曜15:00 JST 課税確定 + 自動納付
- 日次: 回収処理、ローン利息、ローン自動引落

既存の `apps/prison/rehabilitation_scheduler.py` と同じパターン。
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from apps.tax.tax_service import assess_weekly_taxes_and_autopay
from apps.collections.collections_service import process_collections_daily
from apps.loans.loan_service import accrue_daily_interest, attempt_autopay_daily

logger = logging.getLogger(__name__)
_scheduler = None


def _run_weekly_tax():
    try:
        result = assess_weekly_taxes_and_autopay()
        logger.info(f"[TaxScheduler] weekly tax done: {result}")
    except Exception as e:
        logger.error(f"[TaxScheduler] weekly tax error: {e}", exc_info=True)


def _run_daily_collections():
    try:
        result = process_collections_daily()
        logger.info(f"[TaxScheduler] daily collections done: {result}")
    except Exception as e:
        logger.error(f"[TaxScheduler] daily collections error: {e}", exc_info=True)


def _run_daily_loans():
    try:
        r1 = accrue_daily_interest()
        r2 = attempt_autopay_daily()
        logger.info(f"[TaxScheduler] daily loans done: interest={r1} autopay={r2}")
    except Exception as e:
        logger.error(f"[TaxScheduler] daily loans error: {e}", exc_info=True)


def start_tax_collections_loan_scheduler():
    global _scheduler

    if _scheduler is not None:
        logger.info("[TaxScheduler] already running")
        return

    _scheduler = BackgroundScheduler(timezone='Asia/Tokyo')

    # 週次課税: 日曜15:00
    _scheduler.add_job(
        _run_weekly_tax,
        CronTrigger(day_of_week='sun', hour=15, minute=0, timezone='Asia/Tokyo'),
        id='weekly_tax_assessment',
        name='週次課税+自動納付',
        replace_existing=True,
    )

    # ローン: 毎日10:00（push督促が夜中にならないように）
    _scheduler.add_job(
        _run_daily_loans,
        CronTrigger(hour=10, minute=0, timezone='Asia/Tokyo'),
        id='daily_loan_jobs',
        name='ローン利息+自動引落',
        replace_existing=True,
    )

    # 回収: 毎日10:10（ローン自動引落後に延滞/差押え判定）
    _scheduler.add_job(
        _run_daily_collections,
        CronTrigger(hour=10, minute=10, timezone='Asia/Tokyo'),
        id='daily_collections',
        name='回収（日次）',
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("[TaxScheduler] started")


def stop_tax_collections_loan_scheduler():
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown()
    _scheduler = None
    logger.info("[TaxScheduler] stopped")
