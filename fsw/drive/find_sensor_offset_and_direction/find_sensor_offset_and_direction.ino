/**
 * Simple example intended to help users find the zero offset and natural direction of the sensor. 
 * 
 * These values can further be used to avoid motor and sensor alignment procedure. 
 * To use these values add them to the code:");
 *    motor.sensor_direction=Direction::CW; // or Direction::CCW
 *    motor.zero_electric_angle=1.2345;     // use the real value!
 * 
 * This will only work for abosolute value sensors - magnetic sensors. 
 * Bypassing the alignment procedure is not possible for the encoders and for the current implementation of the Hall sensors. 
 * library version 1.4.2.
 * 
 */
#include <SimpleFOC.h>
#include "SimpleFOCDrivers.h"
#include "encoders/as5048a/MagneticSensorAS5048A.h"

// magnetic sensor instance - SPI
//MagneticSensorSPI sensor = MagneticSensorSPI(10, 14, 0x3FFF);
// magnetic sensor instance - I2C
//MagneticSensorI2C sensor = MagneticSensorI2C(0x36, 12, 0X0C, 4);
// magnetic sensor instance - analog output
MagneticSensorAS5048A sensor(10);

// BLDC motor instance
const int VOLTAGE = 9;
BLDCMotor motor = BLDCMotor(11);
BLDCDriver3PWM driver = BLDCDriver3PWM(9, 5, 6, 8);
// Stepper motor instance
//StepperMotor motor = StepperMotor(50);
//StepperDriver4PWM driver = StepperDriver4PWM(9, 5, 10, 6,  8);

void setup() {

  // use monitoring with serial 
  Serial.begin(115200);
  // enable more verbose output for debugging
  // comment out if not needed
  SimpleFOCDebug::enable(&Serial);
#if 0
  // power supply voltage
  driver.voltage_power_supply = 9;
  driver.init();
  motor.linkDriver(&driver);

  // initialise magnetic sensor hardware
  sensor.init();
  // link the motor to the sensor
  motor.linkSensor(&sensor);

  // aligning voltage 
  motor.voltage_sensor_align = 9;
  
  // set motion control loop to be used
  motor.controller = MotionControlType::angle;

  // force direction search - because default is CW
  motor.sensor_direction = Direction::UNKNOWN;

#endif


  // init sensor
  sensor.init();
  motor.linkSensor(&sensor);
  // init driver
  driver.voltage_power_supply = VOLTAGE;
  driver.voltage_limit = VOLTAGE;
  driver.init();
  motor.linkDriver(&driver);

  // init motor
  motor.controller = MotionControlType::angle;
  motor.voltage_limit = VOLTAGE;
  motor.current_limit = 1.0;
  motor.velocity_limit = 8;

  motor.LPF_velocity.Tf = 0.01f;
  // initialize motor
  motor.init();
  // align sensor and start FOC
  motor.initFOC();

  
  Serial.println("Sensor zero offset is:");
  Serial.println(motor.zero_electric_angle, 4);
  Serial.println("Sensor natural direction is: ");
  Serial.println(motor.sensor_direction == Direction::CW ? "Direction::CW" : "Direction::CCW");

  Serial.println("To use these values add them to the code:");
  Serial.print("   motor.sensor_direction=");
  Serial.print(motor.sensor_direction == Direction::CW ? "Direction::CW" : "Direction::CCW");
  Serial.println(";");
  Serial.print("   motor.zero_electric_angle=");
  Serial.print(motor.zero_electric_angle, 4);
  Serial.println(";");

  _delay(1000);
  Serial.println("If motor is not moving the alignment procedure was not successfull!!");
}


void loop() {
    
  // main FOC algorithm function
  motor.loopFOC();

  // Motion control function
  motor.move(2);
}
