# if text == "?じゃんけん":
#     messages = []
#     sessions[user_id] = "waiting_for_hand"
#     messages.append(TextSendMessage(text="最初はグー！じゃんけん……"))
#     line_bot_api.reply_message(
#         event.reply_token,
#         messages
#     )
#     return

# elif state == "waiting_for_hand":
#     messages = []
#     if text in ["グー", "ぐー", "チョキ", "ちょき", "パー", "ぱー"]:
#         # 入力を標準形に変換
#         hand = {"ぐー": "グー", "ちょき": "チョキ", "ぱー": "パー"}.get(text, text)
#         # 必ず勝つ手を選ぶ
#         win_hand = {"グー": "パー", "チョキ": "グー", "パー": "チョキ"}[hand]
#         messages.append(TextSendMessage(text=f"ﾎﾟﾝｯｯ!{win_hand}\n俺の勝ち!俺の勝ち!"))
#         messages.append(TextSendMessage(text="何で負けたか明日までに考えといてください。\nそしたら何かが見えてくるはずです。"))
#         messages.append(TextSendMessage(text="ほな、いただきます。"))
#         messages.append(ImageSendMessage(
#             original_content_url='https://i.imgur.com/HV1x5vV.png',
#             preview_image_url='https://i.imgur.com/HV1x5vV.png'
#         ))
#     else:
#         messages.append(TextSendMessage(text="逃げるな卑怯者！！！じゃんけんから逃げるなーーー！！！"))

#     # セッション状態をクリア
#     sessions.pop(user_id, None)

#     # 応答を送信
#     line_bot_api.reply_message(event.reply_token, messages)
#     return