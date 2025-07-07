# application/view/recruit_views.py
import discord

class JoinLeaveButtons(discord.ui.View):
    """
    各募集メッセージに付与される「参加予定に追加」「参加予定を削除」ボタンのビュー。
    """
    def __init__(self, recruit_id: int):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(label="参加予定に追加",
                              style=discord.ButtonStyle.success,
                              custom_id=f"join:{recruit_id}"))
        self.add_item(
            discord.ui.Button(label="参加予定を削除",
                              style=discord.ButtonStyle.secondary,
                              custom_id=f"leave:{recruit_id}"))
        # NOTE: スレッドへボタンと「新たな募集を追加」ボタンは
        #       Controller (_send_or_update_recruit_message) で動的に追加されるため、ここには含めない。

class MakeButton(discord.ui.Button):
    """ヘッダービュー用の「募集を作成」ボタン。"""
    def __init__(self):
        super().__init__(label="募集を作成",
                         style=discord.ButtonStyle.primary,
                         custom_id="make")

    # callback は GDBotController の on_interaction で処理されるため、ここには記述しない。
    # Modalを表示する処理はController側で行う。


class RefreshButton(discord.ui.Button):
    """ヘッダービュー用の「最新状況を反映」ボタン。"""
    def __init__(self):
        super().__init__(label="最新状況を反映",
                         style=discord.ButtonStyle.secondary,
                         custom_id="refresh")

    async def callback(self, it: discord.Interaction):
        # このボタンは主にデバッグ/表示確認用で、Controllerのロジックを呼び出す必要はない
        # 現状はrecruit_dataがController/Modelにあるため、ここから直接アクセスできない
        # 簡易的な表示であればここで完結させるか、Controllerに処理を委譲する
        # ここではController経由で全募集データを取得して表示する例（Ephemeralメッセージ）
        # ※ このViewクラスはGDBotControllerに依存しないように注意
        # 実際にはControllerのメソッドを呼び出す形になる
        # 例: await self.controller.show_all_recruits_ephemeral(it)

        # 簡略化のため、ここではDBから直接データを取得し表示します (本来はController経由)
        from application.model.recruit_model import RecruitModel, Recruit
        recruit_model = RecruitModel()
        all_recruits_data = await recruit_model.get_all_recruits()

        blocks = []
        for r_data in all_recruits_data:
            # 参加者情報を表示用に変換 (Discord.Memberオブジェクトではない点に注意)
            # これはDBに保存されているユーザーIDのリスト
            participants_display = [f"<@{uid}>" for uid in r_data['participants']] if r_data['participants'] else []

            # Recruitクラスのblock()メソッドを呼び出すために一時的にRecruitオブジェクトを生成
            # 本来はrecruit_modelから整形済みテキストを取得するか、別途Formatterクラスを用意
            temp_recruit_obj = Recruit(
                rid=r_data['id'],
                date_s=r_data['date_s'],
                place=r_data['place'],
                cap=r_data['max_people'],
                note=r_data['note'],
                thread_id=r_data['thread_id'],
                msg_id=r_data['msg_id'],
                # participantsはMemberオブジェクトである必要があるため、ここでは表示しない
                # または、display_nameではなくユーザーIDで表示するなどの工夫が必要
                participants=[] # ここでは空にしておくか、user_idから名前を取得するロジックを別途用意
            )
            
            l1 = f"\U0001F4C5 {temp_recruit_obj.date}   \U0001F9D1 {len(r_data['participants'])}/{temp_recruit_obj.max_people}名"
            l2 = f"{temp_recruit_obj.place}"
            l3 = f"{temp_recruit_obj.note}" if temp_recruit_obj.note else ""
            l4 = "\U0001F7E8 満員" if temp_recruit_obj.is_full() else "⬜ 募集中" # is_fullはparticipantsがMemberオブジェクトでないと正しく判定できない
            l5 = "👥 参加者: " + (", ".join(participants_display) if participants_display else "なし")
            blocks.append(f"```\n{l1}\n{l2}\n{l3}\n{l4}\n{l5}\n```")


        content = "\n".join(blocks) if blocks else "現在募集はありません。"
        await it.response.send_message(content, ephemeral=True)


class HeaderView(discord.ui.View):
    """
    チャンネルのヘッダーに表示される「募集を作成」と「最新状況を反映」ボタンのビュー。
    """
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MakeButton())
        self.add_item(RefreshButton())