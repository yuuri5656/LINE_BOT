from linebot.models import MessageEvent, TextMessage
from .api import handler, line_bot_api
from apps.auto_reply import auto_reply
from apps.recording_logs import recording_logs

@handler.add(MessageEvent, message=TextMessage)
def on_message(event):
    text = event.message.text # メッセージのテキストを取得
    user_id = event.source.user_id  # ユーザーIDを取得
    group_id = None

    if event.source.type == 'group':
        group_id = event.source.group_id # グループの場合のみグループidを取得
        profile = line_bot_api.get_group_member_profile(group_id, user_id) # グループの場合のみメンバーのプロフィールを取得
    elif event.source.type == 'user':
        profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name

    recording_logs(event, user_id, text, display_name)
    auto_reply(event, text, user_id, group_id, display_name)
