import serial
from time import sleep

class Drive:
    def __init__(self, port='/dev/ttyACM0'):
        # シリアル通信を初期化（ポートとボーレート指定）
        self.ser = serial.Serial(port, 115200, timeout=1)
        
        self.ser.reset_input_buffer()   # 受信バッファをクリア
        self.ser.reset_output_buffer()  # 送信バッファをクリア

        # センサやアクチュエータの状態変数
        self.input_shaft_angle = 0       # 入力側シャフトの角度
        self.output_shaft_angle = 0      # 出力側シャフトの角度
        self.abs_sensor_value = 0        # 絶対値センサの値
        self.offset = 0                  # ゼロ点補正用のオフセット

    def __del__(self):
        # インスタンス終了時にアクチュエータを無効化してシリアルポートを閉じる
        self.disable()
        self.ser.close()

    def _send(self, data):
        # シリアルにバイト列を送信
        self.ser.write(bytes(data))

    def _read_ushort(self):
        # 2バイト（unsigned short）をビッグエンディアンで受信して整数化
        return int.from_bytes(self.ser.read(2), 'big')

    def _to_rad(self, digit):
        # デジタル値をラジアンに変換（中心2000で1.0rad = 1000）
        return (digit - 2000) / 1000.0

    def _to_digit(self, rad):
        # ラジアン値をデジタル値に変換（中心2000で1.0rad = 1000）
        return int(rad * 1000 + 2000)

    def init_actuator(self, p=10, i=0, d=0, tf=0.01):
        # アクチュエータのPID制御パラメータを設定して初期化
        # p, i, dは100倍、tf（フィルタ時定数）は10000倍して整数に変換
        p = int(p * 100)
        i = int(i * 100)
        d = int(d * 100)
        tf = int(tf * 10000)
        self._send([0x80, p >> 8, p & 0xFF, i >> 8, i & 0xFF, d >> 8, d & 0xFF, tf >> 8, tf & 0xFF])
        print("Result", self.ser.readline())  # 応答読み取り
        self.get_position()                   # 現在位置を取得
        sleep(0.1)

        # ホーム（ゼロ）位置に出力シャフトを移動する（センサ値100を基準に）
        pos = self.output_shaft_angle
        if self.abs_sensor_value < 100:
            while self.abs_sensor_value < 100:
                self.set_position(pos)
                pos += 0.003
                sleep(0.01)
            pos -= 0.03
            self.set_position(pos)
        else:
            while self.abs_sensor_value >= 100:
                self.set_position(pos)
                pos -= 0.003
                sleep(0.01)
            pos += 0.03
            self.set_position(pos)

        # 現在位置をオフセットとして保存（以後の動作基準に）
        self.offset = self.output_shaft_angle
        sleep(0.1)

    def go_to_zero(self):
        # 出力シャフトをゼロ位置（オフセット補正後）に戻す
        if self.output_shaft_angle > 0:
            while self.output_shaft_angle > 0:
                self.set_position(self.output_shaft_angle - 0.0015)
                sleep(0.01)
        else:
            while self.output_shaft_angle < 0:
                self.set_position(self.output_shaft_angle + 0.0015)
                sleep(0.01)

    def stop_actuator(self):
        # アクチュエータを停止させるコマンドを送信
        self._send([0x81])
        self.ser.readline()  # 応答読み取り（破棄）

    def set_position(self, rad):
        # 指定されたラジアン位置にアクチュエータを動かす
        rad += self.offset  # オフセットを加算
        digit = self._to_digit(rad)  # デジタル値に変換
        if digit < 0:
            digit = 0  # 負値は0にクリップ
        upper = digit >> 8
        lower = digit & 0xFF
        self._send([0x91, upper, lower])  # 位置設定コマンド送信

        # 結果として得られた現在位置・入力角・センサ値を取得
        self.output_shaft_angle = self._to_rad(self._read_ushort()) - self.offset
        self.input_shaft_angle = self._to_rad(self._read_ushort())
        self.abs_sensor_value = self._read_ushort()

    def get_position(self):
        # 現在の位置とセンサ値を取得する
        self._send([0x94])  # 位置取得コマンド
        self.output_shaft_angle = self._to_rad(self._read_ushort()) - self.offset
        self.input_shaft_angle = self._to_rad(self._read_ushort())
        self.abs_sensor_value = self._read_ushort()

    def disable(self):
        # アクチュエータを無効化（停止）
        self._send([0x81])

    def reset(self):
        # システムをリセット（初期化）
        self._send([0x89])
