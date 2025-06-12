#include <SimpleFOC.h>
#include "SimpleFOCDrivers.h"
#include "encoders/as5048a/MagneticSensorAS5048A.h"

// magnetic sensor instance - SPI
MagneticSensorAS5048A sensor(10);

// BLDC motor & driver instance
BLDCMotor motor = BLDCMotor(11);

BLDCDriver3PWM driver = BLDCDriver3PWM(9, 5, 6, 8);
const int absSensorPin = A5;
const int vmonPin = A1;

const int INPUT_GEAR = 12;
const int OUTPUT_GEAR = 93;
const double GEAR_RATIO = (double)OUTPUT_GEAR / (double)INPUT_GEAR;

#define J3

// 以下のパラメータは個体依存
// J1
#ifdef J1
const int absThreshold = 100;
#define SENSOR_DIRECTION Direction::CW
#define ZERO_ELECTRIC_ANGLE (2.6852)
#endif

// J2
#ifdef J2
const int absThreshold = 100;
#define SENSOR_DIRECTION Direction::CW
#define ZERO_ELECTRIC_ANGLE (5.3076)
#endif

// J3
#ifdef J3
const int absThreshold = 100;
#define SENSOR_DIRECTION Direction::CW
#define ZERO_ELECTRIC_ANGLE (1.5357)
#endif

struct CTX {
  bool is_initialized;
  float target_angle;
} ctx;

unsigned char read() {
  while (Serial.available() == 0) {
    // do nothing
  }
  return Serial.read();
}

unsigned short read2() {
  unsigned char upper = read();
  unsigned char lower = read();
  return (unsigned short)upper * 256 + (unsigned short)lower;
}

void (*resetFunc)(void) = 0;

void init_actuator(float p, float i, float d, float tf) {
  if (ctx.is_initialized) {
    return;
  }
  // init sensor
  sensor.init();
  motor.linkSensor(&sensor);
  // init driver
  float motor_voltage = getMotorVoltage();
  driver.voltage_power_supply = motor_voltage;
  driver.voltage_limit = motor_voltage;
  driver.init();
  motor.linkDriver(&driver);

  // init motor
  motor.controller = MotionControlType::angle;
  motor.voltage_limit = motor_voltage;
  motor.current_limit = 0.5;
  motor.velocity_limit = 20;

  motor.P_angle.P = p;
  motor.P_angle.I = i;
  motor.P_angle.D = d;

  motor.PID_velocity.P = 0.2f;
  motor.PID_velocity.I = 11.0f;

  motor.LPF_velocity.Tf = tf;

  motor.sensor_direction = SENSOR_DIRECTION;
  motor.zero_electric_angle = ZERO_ELECTRIC_ANGLE;

  motor.init();
  motor.initFOC();

  ctx.is_initialized = true;
}

void disable_actuator() {
  motor.disable();
  ctx.is_initialized = false;
}

double getOutputShaftAngle() {
  return motor.shaftAngle() / GEAR_RATIO;
}

double getInputShaftAngle() {
  return sensor.getSensorAngle();
}

float getMotorVoltage() {
  int adc_value = analogRead(vmonPin);
  float measured_voltage = ((float)adc_value / 1023.0) * 5.0;
  return measured_voltage * 11.0;
}

int getAbsSensorValue() {
  return analogRead(absSensorPin);
}

double toRad(unsigned int digit) {
  return (double)((int)digit - 2000) / 1000.0;
}

unsigned int toDigit(double rad) {
  return (unsigned int)(rad * 1000.0) + 2000;
}

// Serial.write()で2byteのデータ(unsigned short)を送信する
void write(unsigned short data) {
  Serial.write((unsigned char)(data >> 8));
  Serial.write((unsigned char)(data & 0xff));
}

void process_init_command() {
  float p = ((float)read2()) / 100.0;
  float i = ((float)read2()) / 100.0;
  float d = ((float)read2()) / 100.0;
  float tf = ((float)read2()) / 10000.0;

  init_actuator((float)p, (float)i, (float)d, tf);
  ctx.target_angle = motor.shaftAngle();
}

void process_command(unsigned char cmd) {
  int raw_digit;
  float diff;
  switch (cmd) {
    case 0x80:  // init
      process_init_command();
      break;

    case 0x81:  // disable
      disable_actuator();
      break;

    case 0x89:  // reset
      resetFunc();
      break;

    case 0x91:  // Set target position
      // 出力軸の角度[rad]*1000 + 2000の値を受け取る
      // e.g.
      //  30度の場合 : 30度 = 0.5235987755982988rad -> 2523
      //  -5度の場合 : -5度 = -0.08726646259971647rad -> 1912
      ctx.target_angle = toRad(read2()) * GEAR_RATIO;
      // 出力軸の角度を送信
      write(toDigit(getOutputShaftAngle()));
      // 入力軸の角度を送信
      write(toDigit(getInputShaftAngle()));
      // 絶対センサの値を送信
      write(getAbsSensorValue());

      break;
  
    case 0x94:  // Get angle
      // 出力軸の角度を送信
      write(toDigit(getOutputShaftAngle()));
      // 入力軸の角度を送信
      write(toDigit(getInputShaftAngle()));
      // 絶対センサの値を送信
      write(getAbsSensorValue());
      break;
  }
}

void setup() {
  Serial.begin(115200);

  ctx.is_initialized = false;
  ctx.target_angle = 0.0;
}

void loop() {
  if (Serial.available()) {
    unsigned char data = Serial.read();
    if (data & 0x80) {
      // if head bit is 1, it is a command
      process_command(data);
    }
  }

  if (ctx.is_initialized) {
    // Motion control function
    motor.move(ctx.target_angle);
    // main FOC algorithm function
    motor.loopFOC();
  }
}
