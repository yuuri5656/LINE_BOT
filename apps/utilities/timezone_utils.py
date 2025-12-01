"""
タイムゾーンユーティリティ

すべての時刻処理を日本時間（JST）に統一
"""
from datetime import datetime, timezone, timedelta

# 日本時間のタイムゾーン（UTC+9）
JST = timezone(timedelta(hours=9))


def now_jst() -> datetime:
    """
    現在の日本時間を取得

    Returns:
        datetime: タイムゾーン情報付きの現在日時（JST）
    """
    return datetime.now(JST)


def utc_to_jst(dt: datetime) -> datetime:
    """
    UTC時刻を日本時間に変換

    Args:
        dt: UTC時刻のdatetimeオブジェクト

    Returns:
        datetime: 日本時間に変換されたdatetime
    """
    if dt.tzinfo is None:
        # タイムゾーン情報がない場合はUTCとして扱う
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST)


def format_jst(dt: datetime, fmt: str = '%Y/%m/%d %H:%M:%S') -> str:
    """
    日本時間でフォーマット

    Args:
        dt: datetimeオブジェクト
        fmt: フォーマット文字列

    Returns:
        str: フォーマットされた日時文字列
    """
    if dt is None:
        return '-'

    # タイムゾーン情報がない場合はUTCとして扱う
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    jst_dt = dt.astimezone(JST)
    return jst_dt.strftime(fmt)
