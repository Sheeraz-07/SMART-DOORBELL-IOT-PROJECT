#include "esp_camera.h"
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ESPmDNS.h>

// === Wi-Fi Credentials ===
const char* ssid = "sherry";
const char* password = "connected";

// === Flask Server Hostname & Port ===
const char* serverHostname = "mythbuster.local";
const int serverPort = 5000;
String serverURL = ""; // will be dynamically built using mDNS

// === AI Thinker ESP32-CAM Pin Mapping ===
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define FLASH_GPIO_NUM     4

framesize_t frameSizes[] = {
  FRAMESIZE_UXGA, FRAMESIZE_SXGA, FRAMESIZE_XGA,
  FRAMESIZE_SVGA, FRAMESIZE_VGA, FRAMESIZE_CIF,
  FRAMESIZE_QVGA, FRAMESIZE_HQVGA
};

framesize_t workingSize = FRAMESIZE_QVGA;

bool tryCameraInit(framesize_t size) {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = size;
  config.jpeg_quality = 10;
  config.fb_count     = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("⚠ Failed with resolution %d. Error: 0x%x\n", size, err);
    return false;
  }
  return true;
}

void connectToWiFi() {
  Serial.print("📡 Connecting to WiFi");
  WiFi.begin(ssid, password);
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (++retries > 20) {
      Serial.println("\n❌ WiFi Failed. Restarting...");
      ESP.restart();
    }
  }
  Serial.println("\n✅ WiFi Connected!");
  Serial.print("🌐 IP Address: ");
  Serial.println(WiFi.localIP());
}

void resolveMDNS() {
  IPAddress serverIP;
  if (WiFi.hostByName(serverHostname, serverIP)) {
    Serial.print("🎯 Resolved mythbuster.local to: ");
    Serial.println(serverIP);
    serverURL = "http://" + serverIP.toString() + ":" + String(serverPort) + "/upload";
    Serial.print("🔗 Full server URL: ");
    Serial.println(serverURL);
  } else {
    Serial.println("❌ Failed to resolve mythbuster.local. Restarting...");
    delay(2000);
    ESP.restart();
  }
}

void initCameraWithBestResolution() {
  Serial.println("📷 Trying highest resolution possible...");
  for (int i = 0; i < sizeof(frameSizes) / sizeof(frameSizes[0]); i++) {
    if (tryCameraInit(frameSizes[i])) {
      workingSize = frameSizes[i];
      Serial.printf("✅ Using resolution code: %d\n", workingSize);
      return;
    }
  }
  Serial.println("❌ Couldn't initialize camera with any resolution");
  ESP.restart();
}

void sendImage() {
  Serial.println("📸 Capturing image...");
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Capture failed");
    return;
  }

  Serial.println("📤 Sending image to server...");
  WiFiClient client;
  HTTPClient http;

  http.begin(client, serverURL);
  http.addHeader("Content-Type", "application/octet-stream");

  int httpResponseCode = http.POST(fb->buf, fb->len);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("✅ Server responded [%d]: %s\n", httpResponseCode, response.c_str());
  } else {
    Serial.printf("❌ POST failed: %s\n", http.errorToString(httpResponseCode).c_str());
  }

  esp_camera_fb_return(fb);
  http.end();
}

unsigned long previousMillis = 0;
const long interval = 5000; // 5 seconds interval

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n🚀 ESP32-CAM Booting...");
  connectToWiFi();

  if (!MDNS.begin("esp32cam")) {
    Serial.println("❌ Error starting mDNS");
  } else {
    Serial.println("📣 mDNS started: esp32cam.local");
  }

  resolveMDNS();  // 💥 NEW LINE — builds serverURL using mythbuster.local

  initCameraWithBestResolution();

  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(FLASH_GPIO_NUM, HIGH);  // Flash ON forever
  Serial.println("🔦 Flashlight ON permanently");
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    Serial.println("\n🎯 Aim your face at the camera...");
    sendImage();
    Serial.println("🕒 Waiting 5 seconds...");
  }
}