#include <DHTesp.h>

#define PIN_N    4
#define PIN_P    18
#define PIN_K    19
#define PIN_LDR  34
#define PIN_DHT  15
#define PIN_RELE 5

const int   PH_MIN          = 5;
const int   PH_MAX          = 7;
const float UMID_SECA       = 60.0;
const float UMID_ENCHARCADO = 75.0;

DHTesp dht;

void setup() {
  Serial.begin(115200);
  delay(300);
  pinMode(PIN_N, INPUT_PULLUP);
  pinMode(PIN_P, INPUT_PULLUP);
  pinMode(PIN_K, INPUT_PULLUP);
  pinMode(PIN_RELE, OUTPUT);
  digitalWrite(PIN_RELE, LOW);
  dht.setup(PIN_DHT, DHTesp::DHT22);
}

void loop() {
  bool n = !digitalRead(PIN_N);
  bool p = !digitalRead(PIN_P);
  bool k = !digitalRead(PIN_K);
  int ph = map(analogRead(PIN_LDR), 0, 4095, 0, 14);
  TempAndHumidity data = dht.getTempAndHumidity();
  float umid = data.humidity;
  float temp = data.temperature;

  bool phOk         = (ph >= PH_MIN && ph <= PH_MAX);
  bool encharcado   = (umid > UMID_ENCHARCADO);
  bool soloSeco     = (umid < UMID_SECA);
  bool nutrientesOk = p && (n || k);
  bool irrigar = soloSeco && phOk && !encharcado && nutrientesOk;

  digitalWrite(PIN_RELE, irrigar ? HIGH : LOW);

  Serial.printf(
    "N:%d P:%d K:%d | pH:%2d | umid:%5.1f%% temp:%5.1fC | bomba:%s\n",
    n, p, k, ph, umid, temp, irrigar ? "ON " : "OFF"
  );

  if (!phOk)      Serial.println("  [ALERTA] pH fora da faixa ideal (5-7)");
  if (encharcado) Serial.println("  [ALERTA] Solo encharcado - risco de podridao radicular");
  if (!p)         Serial.println("  [ALERTA] Fosforo ausente - critico para enraizamento");
  if (!soloSeco && !encharcado)
    Serial.println("  [INFO]   Umidade adequada - irrigacao desnecessaria");

  delay(2000);
}
