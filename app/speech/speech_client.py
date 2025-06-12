import requests
import urllib.parse
import hashlib
import os, sys

# 自分のディレクトリをモジュール検索パスに追加
sys.path.append(os.path.dirname(__file__))

from pydub import AudioSegment
from pydub.playback import play

# キャッシュディレクトリのパス（合成された音声を保存）
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache_audio")

# 音声合成に失敗した場合に再生される代替音声ファイル
ERROR_VOICE = "silence.wav"

# キャッシュディレクトリが存在しない場合は作成
os.makedirs(CACHE_DIR, exist_ok=True)

# 音声合成APIにリクエストを送り、音声を保存・再生する関数
def send_voice_request(text, play_audio=False, force_generate=False):
    base_url = "http://127.0.0.1:5000/voice"  # ローカルの音声サーバ

    # 音声合成APIに渡すパラメータ
    params = {
        "text": text,
        "encoding": "utf-8",
        "model_name": "rina1",
        "model_id": 0,
        "speaker_id": 0,
        "sdp_ratio": 0.2,
        "noise": 0.6,
        "noisew": 0.8,
        "length": 1,
        "language": "JP",
        "auto_split": "true",
        "split_interval": 0.5,
        "assist_text_weight": 1,
        "style": "Neutral",
        "style_weight": 1
    }

    # テキスト内容をSHA-256でハッシュ化し、キャッシュファイル名として使用
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    filename = os.path.join(CACHE_DIR, f"audio_{text_hash}.wav")

    # 音声キャッシュが存在し、force_generate が False なら再利用
    if not force_generate and os.path.exists(filename):
        print(f"Using existing audio file: '{filename}'")

        if play_audio:
            # 音声を再生
            audio = AudioSegment.from_file(filename, format="wav")
            play(audio)
        
        return filename  # 再利用されたファイル名を返す

    # GETリクエスト用URLを構築（パラメータをクエリ文字列化）
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        # サーバへリクエストを送信
        response = requests.get(url)
        response.raise_for_status()  # エラーがあれば例外を投げる

        # 音声バイナリデータを取得
        audio_data = response.content

        # 音声ファイルとして保存
        with open(filename, "wb") as f:
            f.write(audio_data)
        print(f"Saved new audio file: '{filename}'")

        if play_audio:
            # 音声を再生
            audio = AudioSegment.from_file(filename, format="wav")
            play(audio)

        return filename  # 新しく保存したファイル名を返す

    except requests.RequestException as e:
        # エラー処理：接続や取得失敗時
        print(f"Error: {e}")
        print(f"Failed to get audio data from '{base_url}'")

        if play_audio:
            # エラー時には静音ファイルを再生
            audio = AudioSegment.from_file(ERROR_VOICE, format="wav")
            play(audio)

        return (ERROR_VOICE, "")  # エラー音声を返す

if __name__ == "__main__":
    fg = False
    if len(sys.argv) < 2:
        print("Usage: python speech.py <text> [-g]")
        sys.exit(1)
    if sys.argv[-1] == "-g":
        fg = True
    text_input = sys.argv[1]
    send_voice_request(text_input, play_audio=True, force_generate=fg)
