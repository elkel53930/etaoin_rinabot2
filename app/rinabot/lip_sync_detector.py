import numpy as np
import librosa

# 音声信号からRMS（Root Mean Square: 実効音量）を計算する関数
def compute_rms(audio, frame_size, hop_size):
    # RMS値を時間ごとに計算し、1次元配列として返す
    return librosa.feature.rms(y=audio, frame_length=frame_size, hop_length=hop_size)[0]

# 音声ファイルからリップシンク（口の開閉）タイミングを検出する関数
def detect_lip_sync_timing(wav_file, frame_size=1024, hop_size=512):
    # 音声ファイルを読み込み（サンプリングレートも取得）
    audio, sr = librosa.load(wav_file, sr=None)

    # 音量（RMS）を計算
    rms = compute_rms(audio, frame_size, hop_size)

    # 各RMS値の時間（秒）を取得
    times = librosa.times_like(rms, sr=sr, hop_length=hop_size)

    # 平均音量の1.2倍以上なら「口が開いている」とみなす（ブール配列）
    mouth_open = (rms > np.mean(rms) * 1.2)

    # 時間軸、RMS配列、口の開閉状態（True/False）を返す
    return times, rms, mouth_open

# 口が開いている時間の区間（インターバル）を抽出する関数
def get_mouth_open_intervals(times, mouth_open):
    open_intervals = []  # 口が開いている区間のリスト
    start = None         # 現在の開口開始時刻

    for i in range(len(times)):
        if mouth_open[i]:
            if start is None:
                start = times[i]  # 新しく口が開き始めた
        else:
            if start is not None:
                # 口が閉じたので、開いていた区間を保存
                open_intervals.append((start, times[i]))
                start = None

    # 最後まで口が開いていた場合、終端を補う
    if start is not None:
        open_intervals.append((start, times[-1]))

    return open_intervals  # 開口時間のリスト [(start1, end1), (start2, end2), ...]


import matplotlib.pyplot as plt


def plot_lip_sync_timing(wav_file):
    times, rms, mouth_open = detect_lip_sync_timing(wav_file)
    open_intervals = get_mouth_open_intervals(times, mouth_open)

    # 口が開いている時間を出力
    print("Mouth Open Time Intervals:")
    for interval in open_intervals:
        print(f"Start: {interval[0]:.2f}s, End: {interval[1]:.2f}s")

    plt.rcParams.update({
        'font.size': 20,
        'axes.labelsize': 20,
        'axes.titlesize': 22,
        'xtick.labelsize': 18,
        'ytick.labelsize': 18,
        'legend.fontsize': 18
    })

    plt.figure(figsize=(12, 5))

    # 音量のプロット
    plt.subplot(3, 1, 1)
    plt.plot(times, rms, label="RMS (Volume)")
    plt.fill_between(times, 0, np.max(rms), where=mouth_open, color='red', alpha=0.3, label="Mouth Open")
    plt.legend()
    plt.ylabel("Volume")
    plt.xlabel("Time (s)")

    plt.suptitle("Lip Sync Timing Detection", fontsize=24)
    plt.show()

# 使用例
if __name__ == "__main__":
    wav_path = "wav/okaiage.wav"  # WAVファイルのパス
    plot_lip_sync_timing(wav_path)