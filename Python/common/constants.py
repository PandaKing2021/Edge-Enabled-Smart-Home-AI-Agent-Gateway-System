"""IoT gateway system common constants definition."""

# TCP communication ports
PORT_SENSOR = 9300          # Device node communication port (originally 3000)
PORT_ANDROID = 9301         # Mobile application communication port (originally 3001)
PORT_DB_SERVER = 9302       # Database server communication port (originally 5000)

# Message terminator (all TCP messages separated by \\n)
MSG_TERMINATOR = "\n"

# Buffer sizes
BUFFER_SIZE_SMALL = 1024
BUFFER_SIZE_MEDIUM = 10240
BUFFER_SIZE_LARGE = 4096

# Gateway listening queue length
LISTEN_BACKLOG = 128

# Database related constants
DB_HOST = "localhost"
DB_PORT = 3306

# Communication intervals (seconds)
SENSOR_SEND_INTERVAL = 3
SENSOR_RECV_INTERVAL = 3
ANDROID_SEND_INTERVAL = 3
ANDROID_RECV_INTERVAL = 3
ALIYUN_UPLOAD_INTERVAL = 5

# Aliyun IoT MQTT port
ALIYUN_MQTT_PORT = 1883

# Door access status
DOOR_DENIED = 0
DOOR_GRANTED = 1

# Device data field names
FIELD_DOOR_CARD_ID = "Door_Secur_Card_id"
FIELD_DOOR_STATUS = "Door_Security_Status"
FIELD_LIGHT_TH = "Light_TH"
FIELD_TEMPERATURE = "Temperature"
FIELD_HUMIDITY = "Humidity"
FIELD_LIGHT_CU = "Light_CU"
FIELD_BRIGHTNESS = "Brightness"
FIELD_CURTAIN_STATUS = "Curtain_status"
FIELD_DEVICE_KEY = "device_key"

# Device data default values
DEFAULT_SENSOR_DATA = {
    FIELD_DOOR_CARD_ID: "",
    FIELD_DOOR_STATUS: 0,
    FIELD_LIGHT_TH: 0,
    FIELD_TEMPERATURE: 0,
    FIELD_HUMIDITY: 0,
    FIELD_LIGHT_CU: 0,
    FIELD_BRIGHTNESS: 0,
    FIELD_CURTAIN_STATUS: 1,
}

DEFAULT_THRESHOLD_DATA = {
    FIELD_LIGHT_TH: 0,
    FIELD_TEMPERATURE: 0,
    FIELD_HUMIDITY: 0,
    FIELD_BRIGHTNESS: 0,
}
