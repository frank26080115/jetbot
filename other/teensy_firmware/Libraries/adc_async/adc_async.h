#ifndef _ADC_ASYNC_H_
#define _ADC_ASYNC_H_

/*
this library is a constantly running ADC

ADC will always be converting, one channel after the next, with results stored in a buffer

this avoids the need for the main code to call "analogRead"
*/

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void adc_init(void);
uint16_t adc_read_10_wait(uint8_t);
uint8_t adc_read_8_wait(uint8_t);
uint16_t adc_read_10_last(uint8_t);
uint8_t adc_read_8_last(uint8_t);
uint16_t adc_read_10_unsafe(uint8_t);
uint8_t adc_read_8_unsafe(uint8_t);

#ifdef __cplusplus
}
#endif

#endif
