import zmq
import os, sys

# 自身のディレクトリをモジュール検索パスに追加
sys.path.append(os.path.dirname(__file__))

from frame_common import *  # SetPositions などのコマンド定義をインポート

class FrameClient:
    def __init__(self):
        # REQソケットを作成してサーバに接続
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://localhost:{PORT}")

    def set_positions(self, positions):
        # 3関節分の目標角度から SetPositions コマンドを作成
        command = SetPositions(positions[0], positions[1], positions[2])
        # コマンドをサーバに送信
        self.socket.send_pyobj(command)
        # サーバからの応答を待機
        self.socket.recv()