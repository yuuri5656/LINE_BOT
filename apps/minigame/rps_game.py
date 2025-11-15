"""
1.グループチャット内で"?じゃんけん"と入力する。 ←達成
2.送信者に有効な銀行口座が存在し、最低参加費用（例:110JPY）を満たしているか確認。 ←達成
3.存在しない場合、口座開設を促すメッセージを送信。 ←達成
4.存在する場合、参加者の募集を開始し、参加希望者を募る。
5.参加希望者は"?参加"と入力して参加表明を行う。
6.送信者に有効な銀行口座が存在し、最低参加費用（例:110JPY）を満たしているか確認し、満たしていない場合は参加を拒否する。
7.開始までなら"?キャンセル"で参加を取り消し可能とする。ホストがキャンセルした場合、全員の参加を取り消す。
8.一定時間（例:1分）後、または"?開始"または参加人数5人で募集を締め切る。
9.参加者全員からベッド各110JPY(手数料約10%)を徴収(引き落とし)する。
10.参加者に対して、グループラインで「個別チャットでじゃんけんの手（グー、チョキ、パー）を選択して送信するよう」促す。
11.各参加者が手を選択し送信する。
12.20秒の猶予を与え、全員の手が揃うかタイムアウトを待つ。
13.タイムアウトしたユーザーはその時点で負けとする。
14.全員の手が揃ったら、じゃんけんの勝敗を判定する。
15.順位によってそれぞれの賞金を計算する。
16.3人以上の参加者がいる場合、同時に多人数じゃんけんを処理する。
17.順位に応じて賞金を分配する（例:1位200JPY、2位100JPY、3位40JPY）。
18.各順位の収支を含めた結果をグループチャットに表示する。
19.賞金を各参加者の銀行口座に送金する。
20.次のゲームの開催を促すメッセージを送信する。
注意点:
- 送金処理は銀行システムのAPIを使用して行う。
- 参加者が最低2人以上必要。
"""
import psycopg2
import config
from core.api import handler, line_bot_api
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

# 口座が存在し、かつアクティブ状態であり、残金がmin_balanceを満たしているかどうかを確認。
def check_account_existence_and_balance(conn, user_id, min_balance):
    cur = conn.cursor()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT balance
            FROM accounts
            WHERE user_id = %s AND status = 'active'
        """, (user_id,))
        result = cur.fetchone()
        if result is None:
            return False  # 口座が存在しない
        balance = result[0]
        return balance >= min_balance  # 最低残高を満たしているか確認

def play_rps_game(event, user_id, text, display_name, sessions):
    conn = psycopg2.connect(config.DATABASE_URL)
    min_balance = 110  # 最低参加費用
    if not check_account_existence_and_balance(conn, user_id, min_balance):
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text=f"{display_name} 様、申し訳ございませんが、じゃんけんゲームを開始するためには有効な銀行口座と最低残高 {min_balance} JPY が必要です。"),
            TextSendMessage(text="口座をお持ちでない場合は、塩爺との個別チャットにて'?口座開設' と入力して口座を開設してください。")]
        )
        conn.close()
        return
    # ここにじゃんけんゲームのロジックを実装する
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"{display_name}が参加者を募集しています。参加希望の方は'?参加'と入力してください。")
    )
