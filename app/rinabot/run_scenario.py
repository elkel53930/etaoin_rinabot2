#!/usr/bin/env python3

import yaml
import argparse
from pprint import pprint

from rinabot import *
from time import sleep
from pydub import AudioSegment
from pydub.playback import play
from threading import Thread, Lock
from lip_sync_detector import detect_lip_sync_timing, get_mouth_open_intervals
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from slide.slide_client import SlideClient

# 表情の変更と口パクの制御がコンフリクトしないように排他制御するためのロック
lock = Lock()
# スライド表示用のクライアント(本書では説明を割愛、app/slide/ディレクトリ下を参照)
slide = SlideClient()
base_path = os.path.join(os.path.dirname(__file__), os.pardir)

# コマンドライン引数の取得
def get_args():
    parser = argparse.ArgumentParser(description='Run a scenario')
    # シナリオファイルの指定
    parser.add_argument('scenario', type=str, help='Scenario file')
    # 指定のタグまでスキップするオプション
    parser.add_argument('--tag_from', help='Start from the specified tag')
    return parser.parse_args()

# 非同期再生のための関数
def play_audio(audio):
    play(audio)

# 口パクをしながら音声を再生する
def run_scene(command):
    base_exp = None
    lip_set = "normal"
    lip_sync_index = 0

    # ---- ① ---- 音声ファイルを取得
    filename = generate_voice(command['text'])

    # ---- ② ---- 表情の初期設定
    if 'base_exp' in command:
        base_exp = exp_dict[command['base_exp']]
    else:
        base_exp = exp_dict['eyes_normal']
    # 口パクの内容が手動で指定されていれば、それを使用
    if 'base_lip_set' in command:
        lip_set = command['base_lip_set']

    # 時間経過とともに表情を変更するためのスレッド
    def change_exp(exp_timeline):
        nonlocal base_exp
        nonlocal lip_set
        nonlocal lip_sync_index
        exp_wait = Await()
        for exp in exp_timeline:
            exp_wait.wait(exp['sec']) # 指定された時間まで待機
            with lock: # 排他制御のためにロックを取得
                if 'lip_set' in exp:
                    lip_set = exp['lip_set']
                if 'exp' in exp:
                    base_exp = exp_dict[exp['exp']]
                set_exp(base_exp + lip_set_dict[lip_set][lip_sync_index])

    # ---- ③ ---- 音声ファイルを読み込んで別スレッドで非同期再生
    audio = AudioSegment.from_wav(filename)
    thread = Thread(target=play_audio, args=(audio,))
    thread.start()

    s(0.05)

    # ---- ④ ---- 音声ファイルの口パクタイミングを検出
    (times, _, mouth_open) = detect_lip_sync_timing(filename)
    open_intervals = get_mouth_open_intervals(times, mouth_open)

    # ---- ⑤ ---- 途中で表情を変更する場合、別スレッドで実行
    if 'exp_timeline' in command:
        exp_thread = Thread(target=change_exp, args=(command['exp_timeline'],))
        exp_thread.start()

    # ---- ⑥ ---- 音声の口パクタイミングに合わせて表情を変更
    last_time = 0
    for mouth_interval in open_intervals:
        for i in range(2):
            s(mouth_interval[i] - last_time)
            with lock:
                lip_sync_index = i
                last_time = mouth_interval[lip_sync_index]
                set_exp(base_exp + lip_set_dict[lip_set][lip_sync_index])
    s(0.1)
    set_exp(base_exp + lip_set_dict[lip_set][1])

def replace_base_path(path_template, base_path):
    return path_template.replace("{BASE_PATH}", base_path)

def main():
    args = get_args() # コマンドライン引数を取得
    scenario = None
    base_path = os.path.dirname(os.path.abspath(args.scenario))
    with open(args.scenario, 'r') as f:
        scenario = yaml.safe_load(f) # YAMLファイル(シナリオファイル)を読み込む
    print(args.tag_from)
    if args.tag_from: # 特定のタグまでスキップする場合
        skip = True
    else:
        skip = False

    # ---- ⑦ ---- あらかじめ音声を生成しておく(キャッシュしておく)
    for command in scenario:
        if 'scene' in command:
            generate_voice(command['text'])

    prev_joints = [0, 0, 0]

    print("Skip:", skip)

    wait_init()
    for command in scenario:
        if 'tag' in command:
            print("Tag:", command['tag'])
            if args.tag_from == command['tag']:
                skip = False # タグが一致したらスキップを解除
            continue

        if skip: # 特定のタグまではコマンドを実行せずスキップ
            continue
        
        if 'scene' in command: # セリフを実行するコマンド
            run_scene(command)
        elif 'wait' in command: # 指定された時間だけ待機するコマンド
            sleep(command['wait'])
        elif 'await' in command: # 指定された時間だけ待機するコマンド
            s(command['await'])
        elif 'move' in command: # 指定角度に移動するコマンド
            prev_joints = [command['j1'], command['j2'], command['j3']]
            move(command['time'], prev_joints)
        elif 'move_add' in command: # 現在の移動に追加で移動するコマンド
            prev_joints = [command['j1'], command['j2'], command['j3']]
            move_add(command['time'], prev_joints)
        elif 'move_add_wait' in command: # 現在の移動に停止時間を追加するコマンド
            move_add(command['time'], prev_joints)
        elif 'set_exp' in command: # 表情を設定するコマンド
            e = exp_dict['face_non']
            for exp in command['exps']:
                e = e + exp_dict[exp]
            set_exp(e)
        elif 'image' in command: # 画像を表示するコマンド
            filename = replace_base_path(command['image'], base_path)
            print("Image:", filename)
            slide.set_image(filename)
        else:
            print("Unknown command")
            pprint(command)
            break
    
    end_script()

if __name__ == '__main__':
    main()
