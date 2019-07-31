#include <twi.h>
#include <adc_async.h>

#define PWM_SLAVE_ADDR 0x60 // must match Adafruit's address, and match the address used in the code

#define REGS_MAX 76

#define PIN_MOTOR_LEFT_PWM  15
#define PIN_MOTOR_LEFT_IN1  9
#define PIN_MOTOR_LEFT_IN2  7
#define PIN_MOTOR_RIGHT_PWM   14
#define PIN_MOTOR_RIGHT_IN1   8
#define PIN_MOTOR_RIGHT_IN2   10

#define ADCIDX_BATTERY 6

volatile bool trigger = false;    // indicates if any I2C activity happened from the ISR
volatile uint8_t regs[REGS_MAX];
bool started = false;             // this "started" flag shows if any I2C activity happened at all, it is set by "trigger"
volatile bool autoInc = true;
volatile uint8_t lastReqReg; // caches the last requested register
volatile uint8_t lastReqLen; // caches the last transaction length

uint32_t serialTime = 0; // used for timeout exiting serial port mode
#define SERIAL_TIMEOUT 1000
#define SERIAL_SPEED_HIGH 255
#define SERIAL_SPEED_LOW  0

bool i2cDebug = false; // enable/disable verbose debug output to serial port

bool battlog = false; // enable/disable battery ADC logging, requires serial port and logging application
uint32_t battlogTime = 0;
uint32_t battlogSec = 0;

#define SAFETY_MAGIC 0x55
volatile uint8_t safety = SAFETY_MAGIC; // motors will not move if safety is off, note: default is ON

volatile uint8_t cameraled = 0; // enable/disable camera LED indicator
uint32_t cameratime = 0; // used to timeout the camera LED indicator

void receiveEvent(uint8_t i2cAdr, uint8_t* data, int cnt);
void requestEvent(uint8_t i2cAdr);

void setup()
{
  initRegs();

  pinMode(LED_BUILTIN, OUTPUT);

  initPins();

  adc_init();

  twi_init();
  twi_setAddress(PWM_SLAVE_ADDR);
  twi_attachSlaveRxEvent(receiveEvent);
  twi_attachSlaveTxEvent(requestEvent);

  Serial.begin(115200);
}

void initPins()
{
  pinMode(PIN_MOTOR_LEFT_PWM, OUTPUT);
  digitalWrite(PIN_MOTOR_LEFT_PWM, LOW);
  pinMode(PIN_MOTOR_RIGHT_PWM, OUTPUT);
  digitalWrite(PIN_MOTOR_RIGHT_PWM, LOW);

  // Drok H-bridge expects logic high on the input pins for floating output pins

  pinMode(PIN_MOTOR_LEFT_IN1, OUTPUT);
  digitalWrite(PIN_MOTOR_LEFT_IN1, HIGH);
  pinMode(PIN_MOTOR_LEFT_IN2, OUTPUT);
  digitalWrite(PIN_MOTOR_LEFT_IN2, HIGH);
  pinMode(PIN_MOTOR_RIGHT_IN1, OUTPUT);
  digitalWrite(PIN_MOTOR_RIGHT_IN1, HIGH);
  pinMode(PIN_MOTOR_RIGHT_IN2, OUTPUT);
  digitalWrite(PIN_MOTOR_RIGHT_IN2, HIGH);
}

void initRegs()
{
  memset((void*)regs, 0, (size_t)REGS_MAX);
  regs[0] = 0x20;
}

void loop()
{
  volatile uint32_t timestamp = 0;

  uint32_t now = millis();

  // timeout check for the "started" flag
  if (timestamp != 0 && started != false) {
    if ((now - timestamp) > 30000) {
      started = false;
      timestamp = 0;
    }
  }

  uint32_t n2 = now % 1600;
  char cameraindicate = false;


  // camera LED blinking
  if (cameraled != 0) {
    cameratime = now;
    cameraled = 0;
  }
  if (cameratime > 0 && (now - cameratime) < 800) {
    cameraindicate = true;
  }
  else {
    cameratime = 0;
  }

  // standard heartbeat blinking
  if (cameraindicate != false) {
    digitalWrite(LED_BUILTIN, (now % 200) < 100);
  }
  else if ((n2 < 200) || (started != false && n2 > 400 && n2 < 600)) {
    digitalWrite(LED_BUILTIN, HIGH);
  }
  else {
    digitalWrite(LED_BUILTIN, LOW);
  }

  if (trigger != false) // I2C transaction happened
  {
    timestamp = now;
    trigger = false;

    // verbose output debug if required
    if (Serial)
    {
      if (i2cDebug != false)
      {
        Serial.printf("I2C 0x%02X ", lastReqReg);
        if (lastReqLen > 0)
        {
          uint8_t i;
          for (i = 0; i < lastReqLen - 1; i++)
          {
            Serial.printf("0x%02X ", regs[lastReqReg + i]);
          }
        }
        Serial.println();
      }
    }
  }

  if (safety != SAFETY_MAGIC) {
    handleChange(); // if safety is off, this function will stop the motors
  }

  // this block handles incoming serial port commands
  // some of these trigger additional debugging output
  // some of these overrides the motors for testing
  char c;
  while (Serial.available() > 0)
  {
    c = Serial.read();
    Serial.printf("%c\r\n", c);
    serialTime = now;
    switch (c)
    {
      case 'a':
      case 'A': // ADC dump
        {
          uint8_t i;
          Serial.printf("%u, ", now);
          for (i = 0; i < 7; i++) {
            Serial.printf("%u, ", adc_read_10_last(i));
          }
          Serial.printf("\r\n");
        }
        break;
      case 'm':
      case 'M': // motor values dump
        {
          Serial.printf("L_PWM %u\r\n",  readPwmValue(8));
          Serial.printf("R_PWM %u\r\n",  readPwmValue(13));
          Serial.printf("L_IN_1 %u\r\n", readPwmValue(10));
          Serial.printf("L_IN_2 %u\r\n", readPwmValue(9));
          Serial.printf("R_IN_1 %u\r\n", readPwmValue(11));
          Serial.printf("R_IN_2 %u\r\n", readPwmValue(12));
        }
        break;
      case 'r':
      case 'R': // register dump
        {
          uint8_t i;
          for (i = 0; i < REGS_MAX; i++) {
            Serial.printf("[0x%02X]: 0x%02X \r\n", i, regs[i]);
          }
          Serial.printf("\r\n");
        }
        break;
      case 'b':
      case 'B': // enables battery logging
        battlog = true;
        break;
      case 'q':
      case 'Q': // toggles I2C debug output
        i2cDebug = !i2cDebug;
        if (Serial)
        {
          if (i2cDebug != false) {
            Serial.println("I2C debug enabled");
          }
          else {
            Serial.println("I2C debug disabled");
          }
        }
        break;
      case '0': // stops the robot
        initPins();
        safety = SAFETY_MAGIC;
        break;
      case '5':
        writePin(PIN_MOTOR_LEFT_PWM,  SERIAL_SPEED_LOW, true, false);
        writePin(PIN_MOTOR_RIGHT_PWM, SERIAL_SPEED_LOW, true, false);
        writePin(PIN_MOTOR_LEFT_IN1, 0, false, false);
        writePin(PIN_MOTOR_LEFT_IN2, 0, false, false);
        writePin(PIN_MOTOR_RIGHT_IN1, 0, false, false);
        writePin(PIN_MOTOR_RIGHT_IN2, 0, false, false);
        safety = SAFETY_MAGIC;
        break;

      /* use the number pad of a full sized keyboard to drive the robot around
         so you can test the motors
      */

      case '8': 
        writePin(PIN_MOTOR_LEFT_PWM,  SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_RIGHT_PWM, SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_LEFT_IN1, 1, false, false);
        writePin(PIN_MOTOR_LEFT_IN2, 0, false, false);
        writePin(PIN_MOTOR_RIGHT_IN1, 1, false, false);
        writePin(PIN_MOTOR_RIGHT_IN2, 0, false, false);
        break;
      case '2':
        writePin(PIN_MOTOR_LEFT_PWM,  SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_RIGHT_PWM, SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_LEFT_IN1, 0, false, false);
        writePin(PIN_MOTOR_LEFT_IN2, 1, false, false);
        writePin(PIN_MOTOR_RIGHT_IN1, 0, false, false);
        writePin(PIN_MOTOR_RIGHT_IN2, 1, false, false);
        break;
      case '4':
        writePin(PIN_MOTOR_LEFT_PWM,  SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_RIGHT_PWM, SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_LEFT_IN1, 0, false, false);
        writePin(PIN_MOTOR_LEFT_IN2, 1, false, false);
        writePin(PIN_MOTOR_RIGHT_IN1, 1, false, false);
        writePin(PIN_MOTOR_RIGHT_IN2, 0, false, false);
        break;
      case '6':
        writePin(PIN_MOTOR_LEFT_PWM,  SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_RIGHT_PWM, SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_LEFT_IN1, 1, false, false);
        writePin(PIN_MOTOR_LEFT_IN2, 0, false, false);
        writePin(PIN_MOTOR_RIGHT_IN1, 0, false, false);
        writePin(PIN_MOTOR_RIGHT_IN2, 1, false, false);
        break;
      case '9':
        writePin(PIN_MOTOR_LEFT_PWM,  SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_RIGHT_PWM, SERIAL_SPEED_LOW, true, false);
        writePin(PIN_MOTOR_LEFT_IN1, 1, false, false);
        writePin(PIN_MOTOR_LEFT_IN2, 0, false, false);
        break;
      case '3':
        writePin(PIN_MOTOR_LEFT_PWM,  SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_RIGHT_PWM, SERIAL_SPEED_LOW, true, false);
        writePin(PIN_MOTOR_LEFT_IN1, 0, false, false);
        writePin(PIN_MOTOR_LEFT_IN2, 1, false, false);
        break;
      case '7':
        writePin(PIN_MOTOR_LEFT_PWM,  SERIAL_SPEED_LOW, true, false);
        writePin(PIN_MOTOR_RIGHT_PWM, SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_RIGHT_IN1, 1, false, false);
        writePin(PIN_MOTOR_RIGHT_IN2, 0, false, false);
        break;
      case '1':
        writePin(PIN_MOTOR_LEFT_PWM,  SERIAL_SPEED_LOW, true, false);
        writePin(PIN_MOTOR_RIGHT_PWM, SERIAL_SPEED_HIGH, true, false);
        writePin(PIN_MOTOR_RIGHT_IN1, 0, false, false);
        writePin(PIN_MOTOR_RIGHT_IN2, 1, false, false);
        break;
      default: // not understood, full reset, stops the motors
        initRegs();
        initPins();
        break;
    }
  }

  // time out of serial port more
  if (serialTime != 0 && ((now - serialTime) > SERIAL_TIMEOUT)) {
    initPins();
    serialTime = 0;
  }

  // battery log output if required, done once per second
  if (battlog != false && Serial && (now - battlogTime) >= 1000) {
    battlogSec++;
    uint16_t batt = adc_read_10_last(6);
    Serial.printf("batt, %u, ", battlogSec);
    Serial.printf("%u, \r\n", batt);
    battlogTime = now;
  }
}

void handleChange()
{
  uint16_t motor_left_pwm, motor_right_pwm;
  uint8_t motor_left_in_1, motor_left_in_2, motor_right_in_1, motor_right_in_2;
  uint8_t mode1, mode2;
  bool invert, invl, invr;

  // emulate some of the weirder behaviours of the PWM driver
  mode1 = regs[0];
  autoInc = (mode1 & 0x20) != 0;
  if ((mode1 & 0x80) != 0 || safety != SAFETY_MAGIC) {
    initRegs();
    initPins();
    return;
  }
  else if ((mode1 & 0x10) != 0) {
    initPins();
    return;
  }

  if (serialTime != 0) {
    return;
  }

  mode2 = regs[1];

  // these PWM channel mappings are from Adafruit's schematic
  motor_left_pwm   = readPwmValue(8);
  motor_right_pwm  = readPwmValue(13);

  motor_left_in_1  = readPwmValue(10);
  motor_left_in_2  = readPwmValue(9);

  motor_right_in_1 = readPwmValue(11);
  motor_right_in_2 = readPwmValue(12);

  invert = (mode2 & 0x10) != 0;
  invl = invr = invert;
  writePin(PIN_MOTOR_LEFT_PWM, motor_left_pwm, true, invert);
  writePin(PIN_MOTOR_RIGHT_PWM, motor_right_pwm, true, invert);

  /*
  The Drok H-bridge has different logic than the TB6612 with regards to braking/floating
  */
#if 0
  if ((motor_left_in_1 == 0 && motor_left_in_2 == 0) || (motor_left_in_1 != 0 && motor_left_in_2 != 0)) {
    invl = !invert;
  }
  if ((motor_right_in_1 == 0 && motor_right_in_2 == 0) || (motor_right_in_1 != 0 && motor_right_in_2 != 0)) {
    invr = !invert;
  }
#endif

  writePin(PIN_MOTOR_LEFT_IN1, motor_left_in_1, false, invl);
  writePin(PIN_MOTOR_LEFT_IN2, motor_left_in_2, false, invl);

  writePin(PIN_MOTOR_RIGHT_IN1, motor_right_in_1, false, invr);
  writePin(PIN_MOTOR_RIGHT_IN2, motor_right_in_2, false, invr);
}

// this function intelligently decides how to physically output the signal
void writePin(uint8_t pin, uint8_t val, bool pwm, bool inv)
{
  if (val <= 0) {
    digitalWrite(pin, inv == false ? LOW : HIGH);
  }
  else if (val >= 255 || pwm == false) {
    digitalWrite(pin, inv == false ? HIGH : LOW);
  }
  else {
    analogWrite(pin, inv == false ? val : (255 - val));
  }
}

// I2C master to slave event handler
void receiveEvent(uint8_t i2cAdr, uint8_t* data, int cnt)
{
  uint8_t i, j, adr;
  lastReqLen = cnt;
  if (cnt > 0)
  {
    adr = data[0];
    lastReqReg = adr;
    for (i = 1; i < cnt; i++)
    {
      uint8_t d = data[i];
      if (adr >= 0xFA && adr <= 0xFD)
      {
        uint8_t offset = adr - 0xFA;
        uint8_t limit = 0x42 + offset;
        for (j = (0x06 + offset); j <= limit; j += 4) {
          regs[j] = d;
        }
      }
      else if (adr <= 0x45)
      {
        regs[adr] = d;
      }
      else if (adr == 0xFF)
      {
        safety = d;
      }
      else if (adr == 0xFE)
      {
        cameraled = d;
      }
      if (autoInc != false) {
        adr++;
      }
      trigger = true;
      started = true;
    }
  }
  handleChange();
}

// I2C slave to master event handler
void requestEvent(uint8_t i2cAdr)
{
  if (lastReqReg <= 0x45) // emulate PWM driver
  {
    twi_transmit((const uint8_t*)&(regs[lastReqReg]), TWI_BUFFER_LENGTH);
  }
  else if (lastReqReg == 0xD0) // ADC read in 10 bit mode
  {
    uint16_t* ptr16 = (uint16_t*)twi_txBuffer;
    uint8_t i;
    for (i = 0; i < 7; i++) {
      ptr16[i] = adc_read_10_unsafe(i);
    }
    twi_txBufferLength = i * 2;
  }
  else if (lastReqReg == 0xE0) // ADC read in 8 bit mode
  {
    uint8_t* ptr8 = (uint8_t*)twi_txBuffer;
    uint8_t i;
    for (i = 0; i < 7; i++) {
      ptr8[i] = adc_read_8_unsafe(i);
    }
    twi_txBufferLength = i;
  }
}

// this is used to skip some unused registers, so we can save some RAM
uint8_t writeAddrXlate(uint8_t x)
{
  if (x <= 0x45) {
    return x;
  }
  return x - (0xFA - 0x46);
}

// this translates the very flexible PWM settings of the PCA9685 to something easy to use (ie, 0 to 255)
uint8_t readPwmValue(uint8_t c)
{
  uint8_t r = c * 4;
  int32_t tOn, tOff, total;
  r += 0x06; // base address
  tOn = regs[r + 1];
  tOn <<= 8;
  tOn += regs[r];
  tOff = regs[r + 3];
  tOff <<= 8;
  tOff += regs[r + 2];
  
  if (tOn > 0 && tOff <= 0) {
    return 0xFF;
  }
  else if (tOff >= 0x1000 && tOn <= 0) {
    return 0;
  }
  else if (tOn <= 0 && tOff <= 0x0FF0)
  {
    return (uint8_t)(tOff >> 4);
  }
  total = tOn + tOff;
  tOn *= 255;
  tOn /= total;
  tOn = tOn > 255 ? 255 : tOn;
  tOn = tOn < 0 ? 0 : tOn;
  return (uint8_t)tOn;
}
