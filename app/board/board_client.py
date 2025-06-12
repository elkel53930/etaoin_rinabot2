import zmq
import os, sys

# カレントディレクトリをモジュール検索パスに追加（board_common のため）
sys.path.append(os.path.dirname(__file__))

from board_common import *  # SetExp などのコマンド定義をインポート

class BoardClient:
    def __init__(self):
        # ZeroMQの初期化
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.REQ)  # 要求（request）ソケット
        self.sock.connect(f"tcp://localhost:{PORT}")  # サーバに接続（PORT は board_common で定義）

    def __del__(self):
        # 終了処理は特になし（必要があればソケットクローズなどを追加）
        pass

    def set_expression(self, exp):
        # Expression オブジェクトから文字列表現を取得し、SetExp コマンドを作成
        command = SetExp(exp.get_expression())
        # サーバに送信（Pythonオブジェクトとして送る）
        self.sock.send_pyobj(command)
        # サーバからの応答を待つ（"OK"）
        self.sock.recv()