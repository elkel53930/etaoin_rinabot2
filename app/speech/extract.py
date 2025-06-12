import os
import sys
import shutil
import subprocess
import numpy as np
import soundfile as sf
from PIL import Image
import pyocr

# 出力先ディレクトリの定数定義
OUTPUT_DIR = "output/"
TEMP_DIR = "/dev/shm/rinabot_temp/"  # 一時作業用のRAMディスクパス（高速）

# 出力ファイルパスのラムダ関数
AUDIO_FILE = lambda prefix: os.path.join(TEMP_DIR, f"{prefix}audio.wav")            # 抽出された音声ファイル
PNG_FILE = lambda prefix: os.path.join(TEMP_DIR, f"{prefix}output%04d.png")         # フレーム画像
WAV_OUT = lambda prefix, i: os.path.join(OUTPUT_DIR, f"{prefix}{i:04d}.wav")        # 切り出し結果のWAVファイル

# OCR（光学文字認識）ツールの初期化
tool = pyocr.get_available_tools()[0]
builder = pyocr.builders.TextBuilder(tesseract_layout=6)  # 読み取り設定（レイアウト6）

# シェルコマンド実行関数（簡略化）
def run(cmd):
    subprocess.run(cmd.split())

# フレーム画像から名前領域を切り出してOCRで名前を読み取る
def read_name(img_path):
    img = Image.open(img_path).crop((447, 594, 519, 631))  # 名前表示部分を切り出し
    return tool.image_to_string(img, lang="jpn", builder=builder)

# 音声信号中の無音区間を検出し、喋っている（キープすべき）区間を返す
def detect_keep_blocks(data, samplerate, silence_threshold=0.05, min_duration=1.4):
    amp = np.abs(data)                    # 振幅を取得
    voice_flags = amp > silence_threshold  # 閾値より大きければ音声とみなす

    silence_blocks, keep_blocks = [], []
    entered = 0       # 無音が始まったインデックス
    prev = True       # 前サンプルの状態（音声 or 無音）

    # 音声と無音の区間を検出
    for i, v in enumerate(voice_flags):
        if prev and not v:
            entered = i
        elif not prev and v:
            dur = (i - entered) / samplerate
            if dur > min_duration:
                silence_blocks.append((entered, i))
        prev = v

    # 終端の無音処理
    if not prev and entered < len(data):
        silence_blocks.append((entered, len(data)))

    # 無音区間以外を抽出（キープ区間）
    last = 0
    for s, e in silence_blocks:
        if last < s:
            keep_blocks.append((last, s))
        last = e
    if last < len(data):
        keep_blocks.append((last, len(data)))
    return keep_blocks

# メイン処理
def main(src_file):
    # 入力ファイル名からプレフィックスを生成（拡張子を除いて"_を追加）
    prefix = os.path.splitext(os.path.basename(src_file))[0] + "_"

    # 一時ディレクトリと出力ディレクトリを作成
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 映像からモノラル音声を抽出（22050Hz）→ RAMディスクに保存
    run(f"ffmpeg -n -i {src_file} -ac 1 -ar 22050 -b:a 128K {AUDIO_FILE(prefix)}")

    # 映像から1秒ごとのフレーム画像を抽出 → RAMディスクに保存
    run(f"ffmpeg -n -i {src_file} -r 1 {PNG_FILE(prefix)}")

    # 音声ファイルを読み込み
    data, sr = sf.read(AUDIO_FILE(prefix))

    # 無音検出によって喋っている区間を検出
    keep_blocks = detect_keep_blocks(data, sr)

    i = 1
    for fr, to in keep_blocks:
        # 無音検出区間の前後0.3秒を拡張して抽出範囲とする
        fr_s = max(fr / sr - 0.3, 0)
        to_s = min(to / sr + 0.3, len(data) / sr)

        # 対応するフレーム画像から名前をOCRで読み取る（2秒後のフレームを参照）
        name = read_name(PNG_FILE(prefix) % int(to_s + 2))

        # 名前に「璃」または「奈」が含まれる場合、その区間を音声として切り出す
        if "璃" in name or "奈" in name:
            run(f"ffmpeg -n -i {AUDIO_FILE(prefix)} -ss {fr_s} -t {to_s - fr_s} {WAV_OUT(prefix, i)}")
            i += 1

    # RAMディスクの一時ファイルをすべて削除
    shutil.rmtree(TEMP_DIR)

# コマンドライン実行時の入口
if __name__ == "__main__":
    main(sys.argv[1])
