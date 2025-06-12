import os, sys
import zmq
from board import Board, Expression
from board_common import *
from datetime import datetime
from time import sleep

tenji = "⠀⠁⠂⠃⠄⠅⠆⠇⡀⡁⡂⡃⡄⡅⡆⡇⠈⠉⠊⠋⠌⠍⠎⠏⡈⡉⡊⡋⡌⡍⡎⡏⠐⠑⠒⠓⠔⠕⠖⠗⡐⡑⡒⡓⡔⡕⡖⡗⠘⠙⠚⠛⠜⠝⠞⠟⡘⡙⡚⡛⡜⡝⡞⡟" + \
        "⠠⠡⠢⠣⠤⠥⠦⠧⡠⡡⡢⡣⡤⡥⡦⡧⠨⠩⠪⠫⠬⠭⠮⠯⡨⡩⡪⡫⡬⡭⡮⡯⠰⠱⠲⠳⠴⠵⠶⠷⡰⡱⡲⡳⡴⡵⡶⡷⠸⠹⠺⠻⠼⠽⠾⠿⡸⡹⡺⡻⡼⡽⡾⡿" + \
        "⢀⢁⢂⢃⢄⢅⢆⢇⣀⣁⣂⣃⣄⣅⣆⣇⢈⢉⢊⢋⢌⢍⢎⢏⣈⣉⣊⣋⣌⣍⣎⣏⢐⢑⢒⢓⢔⢕⢖⢗⣐⣑⣒⣓⣔⣕⣖⣗⢘⢙⢚⢛⢜⢝⢞⢟⣘⣙⣚⣛⣜⣝⣞⣟" + \
        "⢠⢡⢢⢣⢤⢥⢦⢧⣠⣡⣢⣣⣤⣥⣦⣧⢨⢩⢪⢫⢬⢭⢮⢯⣨⣩⣪⣫⣬⣭⣮⣯⢰⢱⢲⢳⢴⢵⢶⢷⣰⣱⣲⣳⣴⣵⣶⣷⢸⢹⢺⢻⢼⢽⢾⢿⣸⣹⣺⣻⣼⣽⣾⣿"

def show_exp(exp_str): # 文字列は20x15 = 300文字
    s = []
    for i in range(0, 300, 20):
        s.append(exp_str[i:i+20])
    s.append("0"*20)

    result = "------------\n"
    for j in range(4):
        result += "|"
        for i in range(10):
            index  = int(s[j*4  ][i*2]) * 1
            index += int(s[j*4+1][i*2]) * 2
            index += int(s[j*4+2][i*2]) * 4
            index += int(s[j*4+3][i*2]) * 8
            index += int(s[j*4  ][i*2+1]) * 16
            index += int(s[j*4+1][i*2+1]) * 32
            index += int(s[j*4+2][i*2+1]) * 64
            index += int(s[j*4+3][i*2+1]) * 128
            result += tenji[index]
        result += "|\n"
    result += "------------\n"
    return result

# ZMQサーバを初期化（REP: 応答型）
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(f"tcp://*:{PORT}")

# dryrunであれば実機には接続しない
board = None
if len(sys.argv) > 1 and sys.argv[1] == 'dryrun':
    print("Dry run mode")
else:
    board = Board(port='/dev/ttyUSB1')  # 実際のLEDボードに接続

# 表情オブジェクトを初期化（すべて消灯）
exp = Expression()

# メインループ：コマンド待機
while True:
    command = socket.recv_pyobj() # クライアントからコマンドを受信（Pythonオブジェクト）
    exp_str = command.exp # 表情データ文字列を取得
    socket.send(b"OK") # クライアントに応答

    if isinstance(command, SetExp): # 表情更新コマンド
        log = show_exp(exp_str) # 点字表示用のログ生成
        now = datetime.now()
        print(now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}")  # タイムスタンプ
        print(log)  # ターミナルに表情を表示

        exp.set_from_string(exp_str)  # 文字列から Expression オブジェクトを更新

        if board is not None:
            board.set_expression(exp)  # 実機に表示を反映

        sleep(0.01)  # 少し待機（連続更新対策）

    elif isinstance(command, Shutdown):  # 終了コマンド
        print("Shutting down")
        break  # ループを抜けて終了