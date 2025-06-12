#include <Adafruit_NeoPixel.h>

#define INDICATOR (13)
#define PIN (6)
#define NUM_OF_LED (200)
#define DATA_LEN (29)
#define BUF_SIZE (NUM_OF_LED*3+1)

#define DEFAULT_R (240)
#define DEFAULT_G (0)
#define DEFAULT_B (96)

unsigned char led_r = DEFAULT_R;
unsigned char led_g = DEFAULT_G;
unsigned char led_b = DEFAULT_B;

Adafruit_NeoPixel pixels(NUM_OF_LED, PIN, NEO_GRB + NEO_KHZ800);

/*
  0x80 : 先頭ビットが1のデータはコマンド。0x80は0/1データ送信。
  0x00~0x7F : 0のビットは消灯、1のビットは点灯。1byteあたり7個分の情報量で、LED200個分のデータを送るので合計29byte
*/

#define CMD_DISPLAY (0x80)
#define CMD_SET_COLOR (0x81)
#define CMD_FULL_COLOR (0x82)
#define CMD_CLEAR (0x83)

unsigned char rgb_buf[BUF_SIZE] = {0};
int index = 0;

void set_color(int index, unsigned char r, unsigned char g, unsigned char b) {
  rgb_buf[index*3] = r;
  rgb_buf[index*3+1] = g;
  rgb_buf[index*3+2] = b;
}

void fill_with(unsigned char r, unsigned char g, unsigned char b)
{
  for(int i = 0 ; i != NUM_OF_LED ; i++)
  {
    set_color(i, r, g, b);
  }
}

void show() {
  pixels.clear();

  digitalWrite(INDICATOR, HIGH);

  for(int i = 0 ; i != NUM_OF_LED ; i++){
    pixels.setPixelColor(i, pixels.Color(
      rgb_buf[i*3],
      rgb_buf[i*3+1],
      rgb_buf[i*3+2]
    ));
  }
  pixels.show();
  
  digitalWrite(INDICATOR, LOW);
}

/**** COMMANDS ****/

void process_display() {
  for(int i = 0; i != DATA_LEN; i++)
  {
    while(Serial.available() == 0);
    unsigned char c = Serial.read();
    for(int j = 0; j != 7; j++)
    {
      if (c & (1 << j)) {
        set_color(i*7+j, led_r, led_g, led_b);
      }
      else{
        set_color(i*7+j, 0, 0, 0);
      }
    }
  }
  show();
}

void process_set_color(){
  while(Serial.available() == 0);
  led_r = Serial.read();
  while(Serial.available() == 0);
  led_g = Serial.read();
  while(Serial.available() == 0);
  led_b = Serial.read();
}

void process_full_color() {
  for(int i = 0; i != NUM_OF_LED; i++)
  {
    while(Serial.available() == 0);
    unsigned char set_r = Serial.read();
    while(Serial.available() == 0);
    unsigned char set_g = Serial.read();
    while(Serial.available() == 0);
    unsigned char set_b = Serial.read();
    set_color(i, set_r, set_g, set_b);
  }
  show();
}

void process_clear() {
  fill_with(0, 0, 0);
  show();
}

/**** SETUP ***/

void setup() {
    int i;
    fill_with(0, 0, 0);
    pixels.begin();
    for(i = 0 ; i != NUM_OF_LED ; i++){
      fill_with(0, 0, 0);
      set_color(i, led_r, led_g, led_b);
      show();
      delay(10);
    }
    fill_with(0, 0, 0);
    show();

    pinMode(PIN, OUTPUT);
  
    pinMode(INDICATOR, OUTPUT);

    Serial.begin(115200);
    Serial.println("Start Rina-chan board");
}

/**** LOOP ***/

void loop() {
  char buf[4] = {0};
  int i = 0;
  bool flag = true;

  while(flag)
  {
    if(Serial.available() > 0)
    {
      unsigned char c = Serial.read();
      switch(c)
      {
      case CMD_DISPLAY:
        process_display();
        break;
      case CMD_SET_COLOR:
        process_set_color();
        break;
      case CMD_FULL_COLOR:
        process_full_color();
        break;
      case CMD_CLEAR:
        process_clear();
        break;
      default:
        break;
      }
    }
  }
}
