/*
this library is a constantly running ADC

ADC will always be converting, one channel after the next, with results stored in a buffer

this avoids the need for the main code to call "analogRead"
*/

#include "adc_async.h"

#include <stdint.h>
#include <avr/io.h>
#include <avr/interrupt.h>

#ifdef HAS_IDLE_TASKS
extern void idle_tasks(void);
#else
#define idle_tasks()
#endif

//#define ADC_ENABLE_FILTERING

#define ADC_CHANNEL_CNT 7
#define ADMUX_DEFAULT		( _BV(REFS0) )
#define ADCSRA_DEFAULT		( _BV(ADEN) | 0x07 )

uint8_t adc_chanMap[] = { 0, 1, 4, 5, 6, 7, 0b100011, };

volatile char adc_hasNew[ADC_CHANNEL_CNT];
volatile uint16_t adc_result[ADC_CHANNEL_CNT];
volatile static uint8_t adc_curChanIdx = 0;

#ifdef ADC_ENABLE_FILTERING
#define ADC_DEFAULT_FILTER_CONST 0.9
volatile double adc_filteredResult[ADC_CHANNEL_CNT];
#endif

void adc_init(void)
{
	uint8_t mux;

	// advanced start only for processors that supports it
	#if defined(ADCSRC)
	ADCSRC = 0xDF; // slowest start and slowest track-and-hold
	#endif
	ADCSRA = _BV(ADEN) | 0x07; // enable with clk/128
	#if defined(AVDDOK) && defined(REFOK)
	while ((ADCSRB & (_BV(AVDDOK) | _BV(REFOK))) == 0); // wait for analog supply and ref to ready
	#elif defined(AVDDOK) && !defined(REFOK)
	while ((ADCSRB & (_BV(AVDDOK))) == 0);
	#elif !defined(AVDDOK) && defined(REFOK)
	while ((ADCSRB & (_BV(REFOK))) == 0);
	#endif

	for (uint8_t i = 0; i < ADC_CHANNEL_CNT; i++)
	{
		adc_hasNew[i] = 0;
		adc_result[i] = 0;
		#ifdef ADC_ENABLE_FILTERING
		adc_filteredResult[i] = -1.0d;
		#endif
	}

	// trigger the first conversion, the ISR will fire off more conversions
	mux = adc_chanMap[adc_curChanIdx];
	ADMUX  = ADMUX_DEFAULT | (mux & 0x1F);
	#ifdef MUX5
	if ((mux & 0x20) != 0) {
		ADCSRB |= _BV(MUX5);
	}
	else {
		ADCSRB &= ~_BV(MUX5);
	}
	#endif
	ADCSRA = ADCSRA_DEFAULT | _BV(ADSC) | _BV(ADIE);
}

uint16_t adc_read_10_wait(uint8_t chan)
{
	#if defined(ADC_ENABLE_FILTERING)
	while (adc_hasNew[chan] == 0) { idle_tasks(); }
	uint16_t r = lround(adc_filteredResult[chan]);
	adc_hasNew[chan] = 0;
	return r;
	#else
	while (adc_hasNew[chan] == 0) { idle_tasks(); }
	uint16_t r = adc_result[chan];
	adc_hasNew[chan] = 0;
	return r;
	#endif
}

uint8_t adc_read_8_wait(uint8_t chan)
{
	return (uint8_t)(adc_read_10_wait(chan) >> 2);
}

uint16_t adc_read_10_last(uint8_t chan)
{
	#if defined(ADC_ENABLE_FILTERING)
	cli();
	uint16_t r = lround(adc_filteredResult[chan]);
	adc_hasNew[chan] = 0;
	sei();
	return r;
	#else
	cli();
	uint16_t r = adc_result[chan];
	adc_hasNew[chan] = 0;
	sei();
	return r;
	#endif
}

uint8_t adc_read_8_last(uint8_t chan)
{
	return (uint8_t)(adc_read_10_last(chan) >> 2);
}

uint16_t adc_read_10_unsafe(uint8_t chan)
{
	#if defined(ADC_ENABLE_FILTERING)
	uint16_t r = lround(adc_filteredResult[chan]);
	adc_hasNew[chan] = 0;
	return r;
	#else
	uint16_t r = adc_result[chan];
	adc_hasNew[chan] = 0;
	return r;
	#endif
}

uint8_t adc_read_8_unsafe(uint8_t chan)
{
	#if defined(ADC_ENABLE_FILTERING)
	uint16_t r = lround(adc_filteredResult[chan]);
	adc_hasNew[chan] = 0;
	return r >> 2;
	#else
	uint16_t r = adc_result[chan];
	adc_hasNew[chan] = 0;
	return r >> 2;
	#endif
}

ISR(ADC_vect)
{
	uint16_t res = ADC;
	uint8_t curChan = adc_curChanIdx;
	uint8_t mux;
	adc_result[curChan] = res;
	#ifdef ADC_ENABLE_FILTERING
	if (adc_filteredResult[curChan] < 0.0d) {
		adc_filteredResult[curChan] = res;
	}
	else {
		adc_filteredResult[curChan] = (adc_filteredResult[curChan] * ADC_DEFAULT_FILTER_CONST) + (res * (1.0d - ADC_DEFAULT_FILTER_CONST));
	}
	#endif
	adc_hasNew[curChan] = 1;
	curChan = (curChan + 1) % ADC_CHANNEL_CNT;
	adc_curChanIdx = curChan;

	mux = adc_chanMap[curChan];
	ADMUX  = ADMUX_DEFAULT | (mux & 0x1F);
	#ifdef MUX5
	if ((mux & 0x20) != 0) {
		ADCSRB |= _BV(MUX5);
	}
	else {
		ADCSRB &= ~_BV(MUX5);
	}
	#endif
	ADCSRA = ADCSRA_DEFAULT | _BV(ADSC) | _BV(ADIE);
}
