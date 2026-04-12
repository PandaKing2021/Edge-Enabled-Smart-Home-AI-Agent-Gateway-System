#include <string.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>
#include <Ticker.h>

// Include configuration file (please copy config_template.h as config.h and modify configuration first)
#include "config.h"

// Include required OLED libraries
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// Include required temperature and humidity sensor (DHT11) libraries
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>

// Initialize OLED display
#define OLED_X 128
#define OLED_Y 64
Adafruit_SSD1306 oled(OLED_X, OLED_Y, &Wire, OLED_RESET_PIN);

// Set temperature and humidity communication port data
#define LEDPIN D6
DHT_Unified dht(DHT_PIN, DHT_TYPE);

int cur_light = 0; // LED status
float cur_temperature = 0.0; // Temperature
float cur_humidity = 0.0; // Humidity

int access_status = 0; // Monitor door access approval status

int recv_light = 0; // Control LED data

Ticker SendTicker;
Ticker GetTicker;
Ticker TimeTicker;
WiFiClient client;

const char* device_id = DEVICE_ID;   // Read sensor ID from configuration file

int seconds = 0;
 
void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(LEDPIN,OUTPUT);
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  Serial.begin(115200);

  // Initialize WiFi
  wifiInit(WIFI_SSID, WIFI_PASSWORD);

  // Initialize OLED display
  oled.begin(SSD1306_SWITCHCAPVCC,0x3C);
  oled.setTextColor(WHITE);  // Turn on pixel illumination
  oled.clearDisplay();  // Clear screen
  oled_string_display(2,16,10,"T: ",0); // Temperature value status
  oled_string_display(2,16,30,"H: ",0); // Humidity value status
  oled_string_display(2,16,50,"S: ",0); // Seconds since boot

  // Initialize temperature and humidity sensor
  dht.begin();
  sensor_t sensor;
  dht.temperature().getSensor(&sensor);

  // Initialize onboard LED
  digitalWrite(LED_PIN, HIGH);

  // Send this device's device_id to Python server
  client.write(device_id);

  // Listen for door access approval
  listen_door_secur_access();

  // Initialize periodic execution functions
  SendTicker.attach(SEND_INTERVAL, sendMsgToGate);
  GetTicker.attach(RECV_INTERVAL, getMsgFromGate);
}

void loop() {
  // Get sensor data
  getTemperature_Humidity();
  getLightStatus();

  // Timer
  showCurrSeconds(seconds++);

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
  }
}


// Get temperature and humidity sensor data
void getTemperature_Humidity(){
    sensors_event_t event;
    dht.temperature().getEvent(&event);
    int tem_t = event.temperature;
    dht.humidity().getEvent(&event);
    int hum_t = event.relative_humidity;

    if (isnan(tem_t) && isnan(hum_t)) {
     Serial.println("Error reading temperature or humidty!");
     cur_temperature = 0.0;
     cur_humidity = 0.0;
    } else {
    cur_temperature = tem_t;
    cur_humidity = hum_t;
   }

   oled_float_display(2,42,10,cur_temperature,1);
   oled_float_display(2,42,30,cur_humidity,1);
}

// Get LED light data
void getLightStatus(){
    cur_light = digitalRead(LEDPIN);
}

void sendMsgToGate(){
  // Create JSON object for message msg
  StaticJsonDocument<200> msg;
  msg["device_id"] = device_id;
  msg["Light_TH"] = cur_light;
  msg["Temperature"] = cur_temperature;
  msg["Humidity"] = cur_humidity;

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
    recv_light = msg["Light_TH"];
    Serial.println("RECV:"+ jsonStr);
  }

    // Control device
  controlDevice();
}

// Control air conditioner light on/off status
void controlDevice(){
   if(recv_light == 0)
    digitalWrite(LEDPIN, LOW);
  else if(recv_light == 1)
    digitalWrite(LEDPIN, HIGH);
}

void showCurrSeconds(int seconds){
  oled_int_display(2,42,50,seconds,1);
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
