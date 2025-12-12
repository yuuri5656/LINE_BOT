"""
犯罪者更生給付金の配布スケジューラー
毎日午前9時に実行
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apps.prison.prison_service import distribute_rehabilitation_fund
from apps.utilities.timezone_utils import now_jst

logger = logging.getLogger(__name__)
scheduler = None


def run_daily_distribution():
    """
    1日1回実行：犯罪者更生給付金を配布
    """
    try:
        result = distribute_rehabilitation_fund()
        if result['success']:
            logger.info(f"[給付金配布] 成功: {result['message']}")
        else:
            logger.info(f"[給付金配布] スキップ: {result['message']}")
    except Exception as e:
        logger.error(f"[給付金配布] エラー: {str(e)}", exc_info=True)


def start_rehabilitation_distribution_scheduler():
    """
    スケジューラーを開始
    毎日午前9時（日本時間）に給付金配布を実行
    """
    global scheduler
    
    if scheduler is not None:
        logger.info("[スケジューラー] 既に起動しています")
        return
    
    try:
        scheduler = BackgroundScheduler(timezone='Asia/Tokyo')
        
        # 毎日午前9時に実行
        scheduler.add_job(
            run_daily_distribution,
            CronTrigger(hour=9, minute=0, timezone='Asia/Tokyo'),
            id='prison_rehabilitation_distribution',
            name='犯罪者更生給付金配布',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("[スケジューラー] 犯罪者更生給付金配布スケジューラーを開始しました (毎日午前9時)")
    except Exception as e:
        logger.error(f"[スケジューラー] 起動エラー: {str(e)}", exc_info=True)


def stop_rehabilitation_distribution_scheduler():
    """
    スケジューラーを停止
    """
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("[スケジューラー] 犯罪者更生給付金配布スケジューラーを停止しました")
