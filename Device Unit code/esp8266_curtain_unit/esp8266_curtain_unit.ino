#include <string.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>
#include <Ticker.h>

// Include configuration file (please copy config_template.h as config.h and modify configuration first)
#include "config.h"

// Include required OLED libraries
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// Include required brightness sensor (BH1750) libraries based on I2C communication
#include <Wire.h>
#include <BH1750.h>

// Initialize OLED display
#define OLED_X 128
#define OLED_Y 64
Adafruit_SSD1306 oled(OLED_X, OLED_Y, &Wire, OLED_RESET_PIN);

// Define buzzer
#define buzzerPin BUZZER_PIN
#define LEDPIN D6

// Initialize brightness sensor object
BH1750 lightMeter(BH1750_ADDR);

// Sensor data initialization
int cur_light = 0; // LED status
int curtain_status = 0;  // Curtain open/close status
float cur_brightness = 0.0;  // Brightness

int access_status = 0; // Monitor door access approval status

int recv_light = 0; // Control LED data
int recv_curtain_status = 0;

int per_curtain_status = 0; // Used to indicate previous curtain status

Ticker SendTicker;
Ticker GetTicker;
WiFiClient client;

const char* device_id = DEVICE_ID;   // Read sensor ID from configuration file

int seconds = 0;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(LEDPIN,OUTPUT);
  pinMode(buzzerPin, OUTPUT); // Set buzzer pin to output mode
  Serial.begin(115200);

  // Initialize WiFi
  wifiInit(WIFI_SSID, WIFI_PASSWORD);

  // Initialize OLED display
  oled.begin(SSD1306_SWITCHCAPVCC,0x3C);
  oled.setTextColor(WHITE);  // Turn on pixel illumination
  oled.clearDisplay();  // Clear screen
  oled_string_display(2,16,10,"B: ",0); // Brightness status
  oled_string_display(2,16,30,"C: ",0); // Curtain open/close status
  oled_string_display(2,16,50,"S: ",0); // Seconds since boot

  // Curtain motor port settings
  pinMode(CURTAIN_PIN1, OUTPUT);
  pinMode(CURTAIN_PIN2, OUTPUT);

  // Brightness sensor port settings
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  lightMeter.begin();

  // Initialize onboard LED
  digitalWrite(LED_PIN, HIGH);

  client.write(device_id); // Send this device's device_id to Python server for verification

  // Listen for door access approval
  listen_door_secur_access();

  // Initialize periodic execution functions
  SendTicker.attach(SEND_INTERVAL, sendMsgToGate);
  GetTicker.attach(RECV_INTERVAL, getMsgFromGate);
}

void loop() {
  // Get brightness sensor data
  getBrightness();

  // Control device
  controlDevice();

  delay(1000);
}

// Initialize WiFi connection
void wifiInit(const char *ssid, const char *password){
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi: ");
    Serial.println(ssid);

    int retry_count = 0;
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(1000);
        Serial.print(".");
        retry_count++;
        if(retry_count > 30) {  // 30 second timeout
            Serial.println("\nWiFi connection timeout!");
            return;
        }
    }

    Serial.println("\nWiFi connected");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    Serial.print("Connecting to gateway ");
    Serial.print(GATEWAY_IP);
    Serial.print(":");
    Serial.println(GATEWAY_PORT);

    if (!client.connect(GATEWAY_IP, GATEWAY_PORT)) {
     Serial.println("Gateway connection failed");
     return;
    }

    Serial.println("Gateway connected");
}

// Listen for door access approval to start communication
void listen_door_secur_access(){
  Serial.println("Start to listen user accessment...");
  while(1){
     if(client.available()){
      String jsonStr = client.readStringUntil('\n'); // Get data, remove trailing newline

      // When gateway sends start signal, update status
      if(jsonStr == "start")
        Serial.println("User access successfully! Start to communication.");
        access_status = 1;
        break;
    }
    digitalWrite(CURTAIN_PIN1,LOW);
    digitalWrite(CURTAIN_PIN2,LOW);
  }
}

void getBrightness(){
  float lux = lightMeter.readLightLevel();

  if (isnan(lux)) {
     Serial.println("Error reading brightness value!");
     cur_brightness = 0.0;
    } else {
    cur_brightness = lux;
   }

   oled_float_display(2,42,10,cur_brightness,1);
}

// Gateway send/receive processing part
void sendMsgToGate(){
  // Create JSON object for message msg
  StaticJsonDocument<200> msg;
  msg["device_id"] = device_id;
  msg["Light_CU"] = cur_light;
  msg["Brightness"] = cur_brightness;
  msg["Curtain_status"] = curtain_status;

  // Serialize JSON object to string and send to Python client
  String jsonStr;
  serializeJson(msg, jsonStr);
  client.println(jsonStr);  // println automatically appends \n at the end
  Serial.println("SEND:"+jsonStr);
}

void getMsgFromGate(){
  if(client.available()){
    StaticJsonDocument<200> msg;
    String jsonStr = client.readStringUntil('\n'); // Get data, newline as delimiter


    // Convert message string to JSON object
    deserializeJson(msg,jsonStr);

    // Update data
    recv_curtain_status = msg["Curtain_status"];
    recv_light = msg["Light_CU"];
    Serial.println("RECV:"+ jsonStr);
  }
  Serial.println(recv_curtain_status);
}

// Device control function
void controlDevice(){
  if(recv_curtain_status == 1 && per_curtain_status != 1){ // 1 is open command
    Serial.println("Open.");

    buzzerStart(100);
    controlLight(1);

    // Drive motor
    digitalWrite(CURTAIN_PIN1,LOW);
    digitalWrite(CURTAIN_PIN2,HIGH);
    delay(500);

    curtain_status = 1;
    per_curtain_status = 1;

    oled_float_display(2,42,30,curtain_status,1);

    digitalWrite(CURTAIN_PIN1,LOW);
    digitalWrite(CURTAIN_PIN2,LOW);
  }else if(recv_curtain_status == 0 && per_curtain_status != 0){ // 0 is close command
    Serial.println("Closed");

    buzzerStart(100);
    controlLight(0);

    digitalWrite(CURTAIN_PIN1,HIGH);
    digitalWrite(CURTAIN_PIN2,LOW);
    delay(500);

    curtain_status = 0;
    per_curtain_status = 0;

    oled_float_display(2,42,30,curtain_status,1);

    digitalWrite(CURTAIN_PIN1,LOW);
    digitalWrite(CURTAIN_PIN2,LOW);
  }

  showCurrSeconds();
}

void showCurrSeconds(){
  seconds += 1;
  oled_int_display(2,42,50,seconds,1);
}

// Trigger buzzer function
void buzzerStart(int micro_second){
  digitalWrite(buzzerPin, HIGH);
  delay(micro_second);
  digitalWrite(buzzerPin, LOW);
}

// Control indoor light
void controlLight(int ifOpen){
  if(ifOpen == 1 && recv_light == 0){
    digitalWrite(LEDPIN, LOW);
  }else if(ifOpen == 0 && recv_light == 1){
    digitalWrite(LEDPIN, HIGH);
  }
}

// oled 显示函数
void oled_int_display(int textsize,int oled_x,int oled_y,int integer_num,int if_clear){
  if(if_clear == 1)
  oled.setTextColor(WHITE, BLACK);
  oled.setTextSize(textsize);
  oled.setCursor(oled_x,oled_y);
  oled.println(integer_num);
  oled.display(); 
}

void oled_float_display(int textsize,int oled_x,int oled_y,float float_num,int if_clear){
  if(if_clear == 1)
    oled.setTextColor(WHITE, BLACK);
  oled.setTextSize(textsize);
  oled.setCursor(oled_x,oled_y);
  oled.println(float_num);
  oled.display(); 
}

void oled_string_display(int textsize,int oled_x,int oled_y,char* str,int if_clear){
  if(if_clear == 1)
  oled.setTextColor(WHITE, BLACK);
  oled.setTextSize(textsize);//设置字体大小  
  oled.setCursor(oled_x,oled_y);//设置显示位置
  oled.println(str);
  oled.display(); 
}

/*
else if(recv_curtain_status == 0 && per_curtain_status != 0){ // 0 为待机指令
    Serial.println("Paused");

    digitalWrite(D3,LOW); 
    digitalWrite(D4,LOW);

    curtain_status = 0;
    per_curtain_status = 0;

    oled_float_display(2,42,30,curtain_status,1);
    delay(500);
  }
*/
