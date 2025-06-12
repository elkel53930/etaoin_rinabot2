import socket
import sys
import tkinter as tk
from PIL import Image, ImageTk
from screeninfo import get_monitors
import zmq
from slide_common import *

def show_display_info(monitors):
    for i, monitor in enumerate(monitors):
        print(f"Display {i}: {monitor.name} {monitor.width}x{monitor.height}")

def show_fullscreen_image(display_index, image_path, canvas, screen_width, screen_height):
    # 画像読み込み
    try:
        img = Image.open(image_path)
        img = img.resize((screen_width, screen_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

    # 画像をキャンバスに表示
    canvas.delete("all")  # 既存の画像を削除
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.image = photo  # 画像の参照を保持し、ガーベジコレクションを防止

    return photo  # 画像の参照を返す


def start_server():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{PORT}")

    # ディスプレイ情報取得
    monitors = get_monitors()
    if len(monitors) == 0:
        print("No monitors found")
        sys.exit(1)

    if len(sys.argv) == 1:
        show_display_info(monitors)
        while True:
            command = socket.recv_pyobj()
            socket.send(b"OK")
            print(f"Received command: {command}")
        exit(0)
    monitor_index = int(sys.argv[1])

    print(monitors)

    monitor = monitors[monitor_index]
    screen_width, screen_height = monitor.width, monitor.height
    screen_x, screen_y = monitor.x, monitor.y

    # Tkinter ウィンドウ作成
    root = tk.Tk()
    root.geometry(f"{screen_width}x{screen_height}+{screen_x}+{screen_y}")
    root.attributes("-fullscreen", True)

    # キャンバス作成
    canvas = tk.Canvas(root, width=screen_width, height=screen_height)
    canvas.pack()

    # クライアントからの接続を待機
    while True:
        try:
            # クライアントから画像ファイル名を受け取る
            command = socket.recv_pyobj()
            socket.send(b"OK")
            if isinstance(command, SetImage):
                image_filename = command.filename
                print(f"Received image filename: {image_filename}")
                # 画像をフルスクリーン表示
                show_fullscreen_image(0, image_filename, canvas, screen_width, screen_height)

            # ESCキーで終了
            root.bind("<Escape>", lambda e: root.destroy())

            # Tkinter ループを続ける
            root.update()

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    start_server()
