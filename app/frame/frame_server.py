import zmq
from frame import Frame # 複数関節をまとめて制御するクラス
from frame_common import * # コマンド定義などの共通モジュール
import sys

# ZeroMQの初期化（REP: 応答型ソケット）
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://*:{PORT}")     # 指定ポートで待ち受け開始

# 引数に 'dryrun' があれば、実際のハードウェアには接続しない
frame = None
if len(sys.argv) > 1 and sys.argv[1] == 'dryrun':
    print("Dry run mode")
    # ドライランモード：frame を生成しない（ハード未接続）
else:
    # 実機接続モード（使用するポートを指定）
    frame = Frame(ports=['/dev/ttyUSB0','/dev/ttyUSB2','/dev/ttyUSB3'])

# 引数に 'fix' があれば、角度を固定してコマンドを無視する
fix_mode = False
if len(sys.argv) > 1 and sys.argv[1] == 'fix':
    print("Fix mode")
    fix_mode = True

# 角度指定コマンドを処理
def process_set_positions(command):
    # frame が存在し、fixモードでなければ関節角を設定
    if frame is not None and not fix_mode:
        frame.set_positions([command.j1, command.j2, command.j3])

# メインループ（コマンド受信 → 処理）
while True:
    # クライアントからオブジェクトを受信して応答を返す
    command = socket.recv_pyobj()
    socket.send(b"OK")

    if isinstance(command, SetPositions):
        # 角度指定コマンド
        process_set_positions(command)
    elif isinstance(command, Shutdown):
        # 終了コマンド
        print("Shutting down")
        break
    else:
        # 未知のコマンド
        print("Unknown command")

# 終了時、frameが存在すればゼロ度に戻す
if frame is not None:
    print("Going to the home position")
    frame.go_to_zero()
    print("Done")