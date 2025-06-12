import serial
from time import sleep
import os, sys

# 相対パスで 'drive' モジュールをインポートできるようにパスを追加
sys.path.append(os.path.dirname(__file__) + '/../drive')

from drive import Drive  # 各関節を制御するクラス

class Frame:
    def __init__(self, ports=['/dev/ttyUSB0','/dev/ttyUSB2','/dev/ttyUSB3'],
        p=10, i=0, d=0, tf=0.01):
        # 3つのDriveインスタンスを保持するリスト
        self.joints = []

        # 指定されたポートを用いて各関節のDriveインスタンスを初期化
        for i in range(3):
            print("Open", ports[i])
            self.joints.append(Drive(ports[i]))

        print("Wait for the actuator to be ready")
        sleep(3)  # ハードウェアの起動を待つ
        print("Init actuator")

        # 各関節を順に初期化（PID値とフィルタ係数を設定）
        for i in [2, 1, 0]:
            print("Initialize J"+str(i+1)+"...")
            self.joints[i].init_actuator(p, i, d, tf)

        print("done")
        sleep(1)

    def __del__(self):
        # オブジェクト破棄時にすべての関節をゼロ位置に戻す
        for i in range(3):
            self.joints[i].go_to_zero()

    def set_positions(self, positions):
        positions[2] += 0.1
        # 指定した各関節の角度（ラジアン）に移動させる
        # `positions` は長さ3のリスト [rad1, rad2, rad3]
        for i in range(3):
            self.joints[i].set_position(positions[i])

    def go_to_zero(self):
        # 各関節をゼロ位置に戻す
        for i in range(3):
            self.joints[i].go_to_zero()

    def get_positions(self):
        # 各関節の現在角度を取得してリストで返す
        positions = []
        for i in range(3):
            self.joints[i].get_position()
            positions.append(self.joints[i].output_shaft_angle)
        return positions