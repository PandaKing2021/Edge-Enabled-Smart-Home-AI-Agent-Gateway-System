#include <string.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>
#include <Ticker.h>

// Include required card reader libraries
#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>

// Include required OLED libraries
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// Initialize OLED display
#define OLED_X 128
#define OLED_Y 64
Adafruit_SSD1306 oled(OLED_X, OLED_Y, &Wire, -1);

// Initialize card reader pins
#define RST_PIN   D1
#define SS_PIN    D2

// Initialize buzzer pin
#define buzzerPin D0

// Create new RFID instance
MFRC522 mfrc522(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key key;

// Initialize card UID string
String permittedUid = "4341e313";
String cardUid = "";
int permitStatus = 0;

const char* ssid     = "3-205/E404";
const char* password = "ieqyydxq2021";
const char* host     = "192.168.1.107";  // Python server IP address
const uint16_t port  = 9300;

WiFiClient client;

const char* device_id = "A1_door_security";   // Sensor ID, used for unique identification
// Note: Door security device ID must contain "security" text

void setup() {
  SPI.begin();        // Start SPI
  Wire.begin(D3,D4);  // Start I2C
  Serial.begin(115200);

   // Initialize WiFi
  wifiInit(ssid, password);

  // Initialize OLED display
  oled.begin(SSD1306_SWITCHCAPVCC,0x3C);
  oled.setTextColor(WHITE);  // Turn on pixel illumination
  oled.clearDisplay();  // Clear screen
  oled_string_display(2,16,30,"S: ",0); // Seconds since boot

  pinMode(buzzerPin, OUTPUT); // Set buzzer pin to output mode

  mfrc522.PCD_Init();

  client.write(device_id);  // Send this device's device_id to Python server
}

void loop() {
  cardLogic();

  delay(1000);
}

// Card recognition main function
void cardLogic(){
    if ( ! mfrc522.PICC_IsNewCardPresent()) {
    //Serial.println("No card found");
    return;
  }

   // Select a card
  if ( ! mfrc522.PICC_ReadCardSerial()) {
    Serial.println("No card available");
    return;
  }

  // Display card details
  Serial.print(F("Card UID:"));
  dump_byte_array(mfrc522.uid.uidByte, mfrc522.uid.size);
  Serial.println();
  Serial.print(F("Card Type: "));
  MFRC522::PICC_Type piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
  Serial.println(mfrc522.PICC_GetTypeName(piccType));

  // Card validation
  if(cardUid == permittedUid){
    permitStatus = 1;
    buzzerStart(100);
    oled_string_display(2,42,30,"Allowed",1); // Seconds since boot
  }else{
    permitStatus = 0;
    buzzerStart(100);
    delay(100);
    buzzerStart(100);
    oled_string_display(2,42,30,"Denied ",1); // Seconds since boot
  }

  sendMsgToGate();

  // Check compatibility
  if (piccType != MFRC522::PICC_TYPE_MIFARE_MINI
          &&  piccType != MFRC522::PICC_TYPE_MIFARE_1K
          &&  piccType != MFRC522::PICC_TYPE_MIFARE_4K) {
    Serial.println(F("Only suitable for Mifare Classic card read/write"));
    return;
  }

  // Stop PICC
  mfrc522.PICC_HaltA();
  // Stop encryption PCD
  mfrc522.PCD_StopCrypto1();

  return;
}

// Send message to gateway
void sendMsgToGate(){
  StaticJsonDocument<200> msg;
  msg["device_id"] = device_id;
  msg["Door_Security_Status"] = permitStatus;
  msg["Door_Secur_Card_id"] = cardUid;

  // Serialize JSON object to string and send to Python client
  String jsonStr;
  serializeJson(msg, jsonStr);
  client.println(jsonStr);  // println automatically appends \n at the end
  Serial.println("SEND:"+jsonStr);
}

// Initialize WiFi connection
void wifiInit(const char *ssid, const char *password){
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(1000);
        Serial.println("WiFi not Connect");
    }

    if (!client.connect(host, port)) {
    Serial.println("Connection failed");
    return;
    }

    Serial.println("Connected to AP");
    Serial.print("Connecting to ");
    Serial.println(host);
}

// Dump byte array to serial hexadecimal values
void dump_byte_array(byte *buffer, byte bufferSize) {
  cardUid = "";
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], HEX);
    cardUid = cardUid + String(buffer[i], HEX);
  }
}

void buzzerStart(int micro_second){
  digitalWrite(buzzerPin, HIGH); 
  delay(micro_second);
  digitalWrite(buzzerPin, LOW);
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
  oled.setTextSize(textsize);// Set text size
  oled.setCursor(oled_x,oled_y);// Set display position
  oled.println(str);
  oled.display();
}
