from linebot.models import MessageEvent, TextMessage, PostbackEvent
from .api import handler, line_bot_api
from apps.auto_reply import auto_reply
from apps.recording_logs import recording_logs
from core.sessions import sessions

@handler.add(MessageEvent, message=TextMessage)
def on_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    group_id = None

    if event.source.type == 'group':
        group_id = event.source.group_id
        profile = line_bot_api.get_group_member_profile(group_id, user_id)
    elif event.source.type == 'user':
        profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name

    recording_logs(event, user_id, text, display_name)
    auto_reply(event, text, user_id, group_id, display_name, sessions)

# Postbackイベント用ハンドラ
@handler.add(PostbackEvent)
def on_postback(event):
    user_id = event.source.user_id
    group_id = None
    if event.source.type == 'group':
        group_id = event.source.group_id
        profile = line_bot_api.get_group_member_profile(group_id, user_id)
    elif event.source.type == 'user':
        profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name

    # postbackイベントはtextがないので空文字を渡す
    recording_logs(event, user_id, event.postback.data, display_name, group_id)
    auto_reply(event, '', user_id, group_id, display_name, sessions)
