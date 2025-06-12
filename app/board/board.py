import serial
import csv
from time import sleep
import os, sys

# カレントディレクトリをモジュール検索パスに追加
sys.path.append(os.path.dirname(__file__))

from exp import _EXP

# ボードのサイズ（横20×縦15）
BOARD_WIDTH = 20
BOARD_HEIGHT = 15

class Expression:
    def __init__(self, exp=None):
        self.clear()  # 初期化して全消灯状態に
        if exp is not None:
            self.set_from_string(exp)  # 文字列から表情を設定

    def clear(self):
        # 全LEDをFalse（消灯）で初期化
        self.graphic = [[False] * BOARD_WIDTH for i in range(BOARD_HEIGHT)]

    def load(self, filename):
        self.clear()
        with open(filename, 'r') as f:
            r = csv.reader(f)
            l = [row for row in r]

        for x in range(BOARD_HEIGHT):
            for y in range(BOARD_WIDTH):
                if l[x][y] == '1':
                    self.graphic[x][y] = True

    def set_from_string(self, str):
        # 文字列（'1'と'スペース' '）から表情データを構築
        self.clear()
        i = 0
        exp_data = list(str.replace('\n', '').replace(',', ''))  # 改行やカンマを削除
        for x in range(BOARD_HEIGHT):
            for y in range(BOARD_WIDTH):
                if exp_data[i] == '1': # '1'は点灯、それ以外は消灯
                    self.graphic[x][y] = True
                i += 1

    def get_graphic(self):
        # 現在のグラフィックデータを返す
        return self.graphic
    
    def __add__(self, other):
        # 2つの表情を論理和で合成して新しいExpressionを返す
        e = Expression()
        for i in range(BOARD_HEIGHT):
            for j in range(BOARD_WIDTH):
                e.graphic[i][j] = self.graphic[i][j] or other.graphic[i][j]
        return e

    def get_expression(self):
        # 表情データを1次元文字列（'1'/'0'）として取得
        flatten = [item for sublist in self.graphic for item in sublist]
        result = ''.join(['1' if b else '0' for b in flatten])
        return result


class Board:
    NUM_OF_LED = 200  # LEDの総数

    WIDTH = BOARD_WIDTH
    HEIGHT = BOARD_HEIGHT

    # 実際のLEDの物理的な配置を論理座標にマッピングする配列
    _LED_ALLOCATION = [
        [  0, 21, 16, 11,  6,  1,  0,  0,  0,  0,  0,  0,  0,  0, 96, 91, 86, 81, 76,  0],
        [  0, 22, 17, 12,  7,  2,  0,  0,  0,  0,  0,  0,  0,  0, 97, 92, 87, 82, 77,  0],
        [  0, 23, 18, 13,  8,  3,  0,  0,  0,  0,  0,  0,  0,  0, 98, 93, 88, 83, 78,  0],
        [  0, 24, 19, 14,  9,  4,  0,  0,  0,  0,  0,  0,  0,  0, 99, 94, 89, 84, 79,  0],
        [  0, 25, 20, 15, 10,  5,  0,  0,  0,  0,  0,  0,  0,  0,100, 95, 90, 85, 80,  0],
        [180,185,190,195,200, 46, 41, 36, 31, 26, 71, 66, 61, 56, 51,105,110,115,120,125],
        [179,184,189,194,199, 47, 42, 37, 32, 27, 72, 67, 62, 57, 52,104,109,114,119,124],
        [178,183,188,193,198, 48, 43, 38, 33, 28, 73, 68, 63, 58, 53,103,108,113,118,123],
        [177,182,187,192,197, 49, 44, 39, 34, 29, 74, 69, 64, 59, 54,102,107,112,117,122],
        [176,181,186,191,196, 50, 45, 40, 35, 30, 75, 70, 65, 60, 55,101,106,111,116,121],
        [  0,  0,  0,  0,  0,155,160,165,170,175,130,135,140,145,150,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,154,159,164,169,174,129,134,139,144,149,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,153,158,163,168,173,128,133,138,143,148,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,152,157,162,167,172,127,132,137,142,147,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,151,156,161,166,171,126,131,136,141,146,  0,  0,  0,  0,  0]]

    def __init__(self, port='/dev/ttyUSB0'):
        # シリアルポートを初期化（ボーレート115200）
        self.ser = serial.Serial(port, 115200, timeout=None)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.graphic = None
        print(self.ser.readline())  # 初期応答の読み取り

    def __del__(self):
        # インスタンス破棄時にLED消灯＆シリアルポートを閉じる
        self.clear()
        self.ser.close()

    def clear(self):
        # LED消灯コマンド（0x83）を送信
        self.ser.write(b'\x83')

    def set_expression(self, expression):
        # Expressionインスタンスの内容をボードに反映する
        # LED状態のビット配列を構築（1bit = 1LED）
        code = [0x80] + [0x00] * 29
        e = expression.get_graphic()
        for x in range(self.WIDTH):
            for y in range(self.HEIGHT):
                if e[y][x]:  # 点灯すべきLEDか？
                    led_index = self._LED_ALLOCATION[y][x]
                    if led_index == 0:
                        print("LEDs are not located at [%d, %d]" % (x, y))
                    else:
                        led_index -= 1  # インデックスを0始まりに
                        code[led_index // 7 + 1] |= 1 << (led_index % 7)  # 対応するビットを立てる
        self.graphic = bytes(code)
        self.ser.write(self.graphic)  # コマンド送信
    
    def set_fullcolor(self, image):
        # フルカラー画像（RGB）をLEDに反映する
        # 各LEDにRGBの3バイトを送信する（コマンド0x82）
        code = [0] * (1 + (self.NUM_OF_LED + 1) * 3)
        code[0] = 0x82
        for x in range(self.WIDTH):
            for y in range(self.HEIGHT):
                led_index = self._LED_ALLOCATION[y][x]
                if led_index != 0:
                    led_index -= 1
                    code[led_index * 3 + 1] = image[y][x][0]  # R
                    code[led_index * 3 + 2] = image[y][x][1]  # G
                    code[led_index * 3 + 3] = image[y][x][2]  # B

        self.ser.write(bytes(code))  # コマンド送信
    
    def set_color(self, r, g, b):
        # 表情の色を設定
        code = [0x81, r, g, b]
        self.ser.write(bytes(code))  # コマンド送信
		

exp_dict = {}
for key in _EXP:
    e = Expression()
    e.set_from_string(_EXP[key])
    exp_dict[key] = e

lip_set_dict = {}
lip_set_dict['normal'] = [Expression(_EXP['mouth_a']), Expression(_EXP['mouth_t'])]
lip_set_dict['waan'] = [Expression(_EXP['mouth_waan1']), Expression(_EXP['mouth_uruuru'])]
lip_set_dict['loud'] = [Expression(_EXP['mouth_a']), Expression(_EXP['mouth_t'])]
lip_set_dict['whisper'] = [Expression(_EXP['mouth_u']), Expression(_EXP['mouth_t'])]
lip_set_dict['hmm'] = [Expression(_EXP['mouth_hmm1']), Expression(_EXP['mouth_hmm2'])]
lip_set_dict['yahoo'] = [Expression(_EXP['mouth_yahoo']), Expression(_EXP['mouth_t'])]

import colorsys
import math
def hsv_gradation(t, max_value=100, speed = 0.1):
    frame = [[[0, 0, 0] for i in range(20)] for j in range(15)]
    for x in range(20):
        for y in range(15):
            hue = ((x + math.sin(y + t * speed + x) * 360) % 360) / 360.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            frame[y][x] = [int(r * max_value), int(g * max_value), int(b * max_value)]
    return frame

if __name__ == '__main__':
    i = 0
    board = Board('/dev/ttyUSB1')
    sleep(2)

    i = 0
    while True:
        for i in range(0, 100):
            board.set_fullcolor(hsv_gradation(i, speed=0.1))
            sleep(0.03)

        for i in range(0, 100):
            color = hsv_gradation(i, speed=0.01)[0][0]
            board.set_color(color[0], color[1], color[2])
            board.set_expression(face['normal'])
            sleep(0.03)
