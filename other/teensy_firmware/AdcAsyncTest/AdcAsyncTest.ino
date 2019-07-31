#include "adc_async.h"

void setup() {
  adc_init();
  Serial.begin(115200);
}

void loop() {
  uint8_t i;
  Serial.printf("%u, ", millis());
  for (i = 0; i < 7; i++)
  {
    Serial.printf("%u, ", adc_read_10_last(i));
  }
  Serial.printf("\r\n");
}
