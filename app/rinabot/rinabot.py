import os, sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))  # 上位ディレクトリもモジュール検索対象に

# rina lib（自作モジュール群）
from frame.frame_client import FrameClient               # ロボットの関節制御クライアント
from board.board import exp_dict, lip_set_dict           # 表情プリセット辞書
from board.board_client import BoardClient               # 表情表示用クライアント
from speech.speech_client import send_voice_request      # 音声合成クライアント
from active_wait import Await                            # 時間待機（非同期向け）

# マルチスレッド制御
import threading
import queue

# トラジェクトリ生成（関節の補間移動）
from trajgen import t_sin, t_linear

from time import sleep
import random

# 表情表示用のクライアントと待機制御インスタンスを生成
board = BoardClient()
wait = Await()

# s(t): 時間tだけ待つ（ラップ関数）
def s(t):
    wait.wait(t)

# waitオブジェクトの初期化
def wait_init():
    wait.init()

# トラジェクトリ生成方式
TRAJ_SIN = 0
TRAJ_LINEAR = 1
traj_generator = t_sin  # デフォルトはサイン補間

# トラジェクトリの生成器を切り替える
def change_traj_generator(gen_id):
    global traj_generator
    if gen_id == TRAJ_SIN:
        traj_generator = t_sin
    elif gen_id == TRAJ_LINEAR:
        traj_generator = t_linear
    else:
        traj_generator = t_sin

# トラジェクトリ種別
FRESH = 0  # 新しい移動
ADD = 1    # 既存の動きに追加

# 関節制御スレッド関数：コマンドキューから目標姿勢を受け取り、関節角度を補間しながら送信
def frame_traj_thread(cmdq):
    DT = 0.02  # フレーム周期（秒）
    print("start frame_traj_thread")
    frame = FrameClient()  # 関節制御インスタンス
    current_j = [0, 0, 0]  # 現在の関節角度
    traj = [[0], [0], [0]] # 各軸のトラジェクトリ
    index = 0
    w = Await()
    while True:
        if not cmdq.empty():
            cmd = cmdq.get()
            if cmd is None:
                break  # None を受け取ったらスレッド終了
            if cmd['type'] is FRESH:
                # 新しいトラジェクトリを生成
                traj[0] = traj_generator(current_j[0], cmd['target'][0], cmd['time'], DT)
                traj[1] = traj_generator(current_j[1], cmd['target'][1], cmd['time'], DT)
                traj[2] = traj_generator(current_j[2], cmd['target'][2], cmd['time'], DT)
                index = 0
            elif cmd['type'] is ADD:
                # 現在の終点から次の目標へ続ける形で追加
                traj[0] += traj_generator(traj[0][-1], cmd['target'][0], cmd['time'], DT)
                traj[1] += traj_generator(traj[1][-1], cmd['target'][1], cmd['time'], DT)
                traj[2] += traj_generator(traj[2][-1], cmd['target'][2], cmd['time'], DT)

        # 次の関節角度を送信
        if index != len(traj[0]) - 1:
            index += 1
        current_j = [traj[0][index], traj[1][index], traj[2][index]]

        w.wait(DT)
        frame.set_positions(current_j)

# コマンドキューとスレッド起動
rc_frame_queue = queue.Queue()
t1 = threading.Thread(target=frame_traj_thread, args=(rc_frame_queue,))
t1.start()

# 移動
def move(time, target):
    cmd = {
        'type': FRESH,
        'time': time,
        'target': target,
    }
    rc_frame_queue.put(cmd)

# 移動追加（現在の移動に連続追加）
def move_add(time, target):
    cmd = {
        'type': ADD,
        'time': time,
        'target': target,
    }
    rc_frame_queue.put(cmd)

# 終了処理：目と口を「通常」表情に戻して、原点へ移動
def end_script():
    set_exp(exp_dict['eyes_normal'] + exp_dict['mouth_normal'])
    move(1, [0, 0, 0])
    s(1.2)
    rc_frame_queue.put(None)  # スレッド終了信号

# 表情を設定
def set_exp(exp):
    board.set_expression(exp)

# リップシンク処理：母音の変化に応じて口の形を切り替える
def lip_sync(base_exp, vow, interval):
    prev = ''
    for v in vow:
        if v == prev:
            set_exp(base_exp)
            s(interval / 4)
            set_exp(base_exp + exp_dict[f"mouth_{v}"])
            s(interval / 4 * 3)
        else:
            set_exp(base_exp + exp_dict[f"mouth_{v}"])
            s(interval)
        prev = v

# 音声を生成（ファイル保存のみ、再生なし）
def generate_voice(text, force_generate=False):
    return send_voice_request(text, play_audio=False, force_generate=force_generate)
