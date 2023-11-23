///
/// @mainpage  Python_Teensy_CV_v1
///
/// @details  Description of the project
/// @n
/// @n
///
/// @author   Elie CAMPAGNOLO
/// @date     28/04/2023 17:10
/// @version  <#version#>
///
/// @copyright  (c) Elie Campagnolo, 2023
/// @copyright  Licence
///
/// @see    ReadMe.txt for references
///


///
/// @file   Python_Teensy_CV_v1.ino
/// @brief    Main sketch
///
/// @author   Elie CAMPAGNOLO
/// @date     28/04/2023 17:10
/// @version  <v1>
///
/// @copyright  (c) Elie Campagnolo, 2023
/// @copyright  Licence
///
/// @see    ReadMe.txt for references
/// @n
///

#include <SPI.h> 

#define MKR0_BOARD  "Arduino MKR0"
#define BAUD_RATE          115200
#define NB_PARAM                4
#define COMMA                 ','
#define EQUAL                 '='

#define PIN_MARK                5 // To synchronise the oscilloscope
#define DIV_16                 16 // To set clock frequency of 1 MHz
#define IDLE_STATE          false
#define ACTIVE_STATE         true
#define CODE_STEP               1
#define MAX_DAC              1023         // Maximum code for DAC
#define DAC_VZERO               0
#define DAC_V1V65             512
#define V5V                     5.00
#define ADC_RESOLUTION_BITS    12 // This library supports a maximum of 12 bit resolution
#define ADC_IN                 A1
#define DAC_RESOLUTION_BITS    10    
#define DAC_OUT                A0
#define PIN_CTRL                6

#define DELAY_1s             1000
#define DELAY_1ms            1000
#define DELAY_BLK             200
#define PER_BLK               512

#define MIN_CYCLE               1
#define MAX_CYCLE               3
#define SIZE_MAX_CYCLE       2048 // Limited by the size of the memory

#define ERROR_INDEX     -1   // Indicateur d'erreur si l'entrée de la chaîne de caractères n'est pas une de celles qui est attendue
#define OK              true // Simple transposition du booléen true
#define ERROR_INPUT     false// Idem pour false

unsigned long time_init, time_final ;
int cur[MAX_CYCLE * SIZE_MAX_CYCLE] ; // Buffer for CV
int i, index_acq, index_acq_up[MAX_CYCLE], index_acq_down[MAX_CYCLE] ;
int nb_cycle, i_cycle ;
int code_DAC, code_DAC_vstart , code_DAC_vstop ;
int code_DAC_end[MAX_CYCLE] ;
int i_blk, code_step ;

volatile boolean state = IDLE_STATE; // for the ISR subroutine

int received_length, received_pos_comma, received_pos_equal ;
unsigned int param[NB_PARAM] ;
unsigned int period ;
String received, received_param ;
boolean status_input ; 
boolean status_input_param ;
boolean status_input_acq ;
boolean blk, ox ;

/****************************************************************************/
/*              Setup pins                                                  */
/****************************************************************************/
void setup(void) {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PIN_CTRL, OUTPUT) ; // To switch on/off the cell
  digitalWrite(PIN_CTRL, LOW) ;
  pinMode(PIN_MARK, OUTPUT);
  digitalWrite(PIN_MARK, LOW);
  Serial.begin(BAUD_RATE);
  while (!Serial) ;               // Wait for serial port to connect. Needed for native USB
  
  /****************************************************************************/
  /*              Setup ADC and DACparameters                                 */
  /****************************************************************************/
  state = IDLE_STATE ;
  analogReadResolution(ADC_RESOLUTION_BITS);
  analogWriteResolution(DAC_RESOLUTION_BITS);
  status_input        = ERROR_INPUT ;
  status_input_param  = ERROR_INPUT ;
  status_input_acq    = ERROR_INPUT ;
  delay(DELAY_1s);              // Wait for 1 second
}

/****************************************************************************/
/*    The main program will print the data to the Arduino Serial Monitor    */
/****************************************************************************/

void loop(void) {

  time_init = micros();
  /****************************************************************************/
  /*              Test input character                                        */
  /****************************************************************************/
  if (Serial.available() > 0) { // If serial data available
    received = Serial.readString() ;       // Get serial string
    
    /********************************************************************/
    /*            SET parameters command                                */
    /********************************************************************/
    if ( received != "ACQ" && received != "BOARD" ) {
      for ( i = 0 ; i < NB_PARAM ; i++) {     
        received_length = received.length() ;
        received_pos_comma  = received.indexOf(COMMA) ;
        received_param = received.substring(0, received_pos_comma) ;
        param[i] = received_param.toInt() ;
        received = received.substring(received_pos_comma + 1, received_length);
      } 
      if ( param[1] > param[2]) { // We start with Oxidation
        code_step = CODE_STEP ;
        ox = true ;    
      }
      else {
        code_step = - CODE_STEP ;
        ox = false ;
      }
    }

    /********************************************************************/
    /*            BOARD command                                         */
    /********************************************************************/
    else if(received == "BOARD") {
      Serial.println(MKR0_BOARD) ;     // send the board type to the Pyhon script
   }   
     
    /********************************************************************/
    /*            ACQ command                                           */
    /********************************************************************/
    else if(received == "ACQ") {  
      period = param[3] ;
      TC_Configure(period);                     // Configure the timer to run at samplePeriod µs
      TC_Startcounter();                        // Starts the timer

      digitalWrite(LED_BUILTIN, HIGH) ;
      //time_final = micros();
      delayMicroseconds(DELAY_1ms);
      
      code_DAC_vstart = param[1] ;
      code_DAC_vstop  = param[2]  ;
      analogWrite(DAC_OUT, code_DAC_vstart) ;
      digitalWrite(PIN_CTRL, HIGH) ;
      delay(2*DELAY_1s) ;
      //Serial.print("code_DAC_vstart = ") ;Serial.println(code_DAC_vstart) ;
      //Serial.print("code_DAC_vstop  = ") ;Serial.println(code_DAC_vstop) ;
      
      /********************************************************************/
      /*            Loop for firt part of the cycle                       */
      /********************************************************************/
      nb_cycle = param[0] ;
      if( nb_cycle > 3) nb_cycle = 3 ;
      switch (nb_cycle) {
        case 1:
          code_DAC_end[0] = code_DAC_vstart ;
          break;
        case 2:
          code_DAC_end[0] = code_DAC_vstart - code_step ;
          code_DAC_end[1] = code_DAC_vstart ;
          break;
        case 3:
          code_DAC_end[0] = code_DAC_vstart - code_step ;
          code_DAC_end[1] = code_DAC_vstart - code_step ;
          code_DAC_end[2] = code_DAC_vstart ;
          break;
      }

/********************************************************************/
/*           Cycle starts in Oxydation                              */
/********************************************************************/ 
      if (ox == true) {
        for (i_cycle = 0 ; i_cycle < nb_cycle ; i_cycle++) {
          index_acq = 0 ;   
          for ( code_DAC = code_DAC_vstart; code_DAC > code_DAC_vstop ; code_DAC -= CODE_STEP ) {
            while (state == IDLE_STATE) ;
            state = IDLE_STATE ;
            analogWrite(DAC_OUT, code_DAC); // DAC pin = A14
            cur[index_acq + i_cycle * SIZE_MAX_CYCLE] = analogRead(ADC_IN); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
            index_acq +=1 ;
          }
          index_acq_down[i_cycle] = index_acq - 1;
      
      /********************************************************************/
      /*            Loop for second part of the cycle                     */
      /********************************************************************/     
          for ( code_DAC = code_DAC_vstop ; code_DAC <= code_DAC_end[i_cycle] ; code_DAC += CODE_STEP ){
            while (state == IDLE_STATE) ;
            state = IDLE_STATE ;
            analogWrite(DAC_OUT, code_DAC);
            cur[index_acq + i_cycle * SIZE_MAX_CYCLE] = analogRead(ADC_IN); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
            index_acq +=1 ;
          }
          index_acq_up[i_cycle] = index_acq - 1 ;
        }
      /********************************************************************/
      /*           Loop for printing Data on serial link                  */
      /********************************************************************/
        //Serial.println(index_acq_down[0]);
        //Serial.println(index_acq_up[0]);
        blk = true ; 
        for ( i_cycle = 0 ; i_cycle < nb_cycle ; i_cycle++ ) {                 
          for ( i = 0 ; i <= index_acq_up[i_cycle] ; i += CODE_STEP ) {
            if ( i <= index_acq_down[i_cycle] ) {
              code_DAC = code_DAC_vstart - i ;
            }
            else {
              code_DAC = code_DAC_vstop + (i - index_acq_down[i_cycle] - 1) ;
            }
            i_blk = i % PER_BLK ;
            if (i_blk == 0) {
              digitalWrite(LED_BUILTIN, blk); // To show serial link transfert
              delay(DELAY_BLK);
              blk = !blk ;
            }
            Serial.print(code_DAC);Serial.print(", ");Serial.println(cur[i + i_cycle * SIZE_MAX_CYCLE]);
          }
        }
      }

/********************************************************************/
/*           Cycle starts in Reduction                              */
/********************************************************************/      
      else {
        for (i_cycle = 0 ; i_cycle < nb_cycle ; i_cycle++) {
          index_acq = 0 ;   
          for ( code_DAC = code_DAC_vstart; code_DAC < code_DAC_vstop ; code_DAC += CODE_STEP ) {
            while (state == IDLE_STATE) ;
            state = IDLE_STATE ;
            analogWrite(DAC_OUT, code_DAC); // DAC pin = A14
            cur[index_acq + i_cycle * SIZE_MAX_CYCLE] = analogRead(ADC_IN); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
            index_acq +=1 ;
          }
          index_acq_up[i_cycle] = index_acq  - 1;
      
      /********************************************************************/
      /*            Loop for second part of the cycle                     */
      /********************************************************************/     
          for ( code_DAC = code_DAC_vstop ; code_DAC >= code_DAC_end[i_cycle] ; code_DAC -= CODE_STEP ){
            while (state == IDLE_STATE) ;
            state = IDLE_STATE ;
            analogWrite(DAC_OUT, code_DAC);
            cur[index_acq + i_cycle * SIZE_MAX_CYCLE] = analogRead(ADC_IN); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
            index_acq +=1 ;
          }
          index_acq_down[i_cycle] = index_acq - 1 ;
        }
      /********************************************************************/
      /*           Loop for printing Data on serial link                  */
      /********************************************************************/
        blk = true ; 
        for ( i_cycle = 0 ; i_cycle < nb_cycle ; i_cycle++ ) {                 
          for ( i = 0 ; i <= index_acq_down[i_cycle] ; i += CODE_STEP ) {
            if ( i <= index_acq_up[i_cycle] ) {
              code_DAC = code_DAC_vstart + i*CODE_STEP ;
            }
            else {
              code_DAC = code_DAC_vstop + (-i*CODE_STEP + index_acq_up[i_cycle] + 1) ;
            }
            i_blk = i % PER_BLK ;
            if (i_blk == 0) {
              digitalWrite(LED_BUILTIN, blk); // To show serial link transfert
              delay(DELAY_BLK);
              blk = !blk ;
            }
            Serial.print(code_DAC);Serial.print(", ");Serial.println(cur[i + i_cycle * SIZE_MAX_CYCLE]);
          }
         }
      }
      digitalWrite(PIN_CTRL, LOW) ;  
      digitalWrite(LED_BUILTIN, LOW );
      analogWrite(DAC_OUT, code_DAC_vstart); // DAC pin = A14
    }
  }
}

/****************************************************************************/
/*  TIMER SPECIFIC FUNCTIONS FOLLOW                                         */
/*  you shouldn't change these unless you know what you're doing            */
/****************************************************************************/
// Configures the TC to generate output events at the sample period
// Configures the TC in Frequency Generation mode, with an event output once
void TC_Configure(uint16_t samplePeriod) {
  REG_GCLK_GENDIV = GCLK_GENDIV_DIV(3) | GCLK_GENDIV_ID(4);        // Divide the 48MHz clock source by divisor 3: 48MHz/3 = 16MHz
                                                  // Select Generic Clock (GCLK) 4
  while (GCLK->STATUS.bit.SYNCBUSY);              // Wait for synchronization

  REG_GCLK_GENCTRL = GCLK_GENCTRL_IDC |           // Set the duty cycle to 50/50 HIGH/LOW
                     GCLK_GENCTRL_GENEN |         // Enable GCLK4
                     GCLK_GENCTRL_SRC_DFLL48M |   // Set the 48MHz clock source
                     GCLK_GENCTRL_ID(4);          // Select GCLK4
  while (GCLK->STATUS.bit.SYNCBUSY);              // Wait for synchronization
                                                  // Feed GCLK4 to TC_4 and TC_5
  REG_GCLK_CLKCTRL = GCLK_CLKCTRL_CLKEN |         // Enable GCLK4 to TC_4 and TC_5
                     GCLK_CLKCTRL_GEN_GCLK4 |     // Select GCLK4
                     GCLK_CLKCTRL_ID_TC4_TC5;     // Feed the GCLK4 to TC_4 and TC_5
  while (GCLK->STATUS.bit.SYNCBUSY);              // Wait for synchronization

  // Select the generic clock generator used as source to the generic clock multiplexer
  // GCLK->CLKCTRL.reg = (uint16_t) (GCLK_CLKCTRL_CLKEN | GCLK_CLKCTRL_GEN_GCLK0 | GCLK_CLKCTRL_ID(GCM_TC4_TC5)) ;
  while (GCLK->STATUS.bit.SYNCBUSY);

  TC_Reset(); //Reset TC5

  // Set Timer counter 5 Mode to 16 bits, it will become a 16 bit counter ('mode1' in the datasheet)
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_MODE_COUNT16;
  // Set TC5 waveform generation mode to 'match frequency'
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_WAVEGEN_MFRQ;//TC__CTRLA_WAVEGEN_MFRQ
  setDivisor(DIV_16);                             // Divide the clock by 16 to get 1 MHz
 
  // Set the compare-capture register. 
  // The counter will count up to this value (it's a 16bit counter so we use uint16_t)
  // this is how we fine-tune the frequency, make it count to a lower or higher value
  //system clock should be 1MHz (8MHz/8) at Reset by default
  TC5->COUNT16.CC[0].reg = samplePeriod - 1 ; //samplePeriod * 1 µs
  while (TC_IsSyncing());
 
  // Configure interrupt request
  NVIC_DisableIRQ(TC5_IRQn);
  NVIC_ClearPendingIRQ(TC5_IRQn);
  NVIC_SetPriority(TC5_IRQn, 0);
  NVIC_EnableIRQ(TC5_IRQn);

  // Enable the TC_5 interrupt request
  TC5->COUNT16.INTENSET.bit.MC0 = 1;
  while (TC_IsSyncing()); //wait until TC5 is done syncing 
} 


/****************************************************************************/
/*    Function that is used to check if TC5 is done syncing                 */
/****************************************************************************/
//returns true when it is done syncing
bool TC_IsSyncing(void) {
  return TC5->COUNT16.STATUS.reg & TC_STATUS_SYNCBUSY;
}

/****************************************************************************/
/*    This function enables TC5 and waits for it to be ready                */
/****************************************************************************/
void TC_Startcounter(void) {
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_ENABLE; //set the CTRLA register
  while (TC_IsSyncing()); //wait until snyc'd
}

/****************************************************************************/
/*    Reset TC5                                                             */
/****************************************************************************/
void TC_Reset(void) {
  TC5->COUNT16.CTRLA.reg = TC_CTRLA_SWRST;
  while (TC_IsSyncing());
  while (TC5->COUNT16.CTRLA.bit.SWRST);
}

/****************************************************************************/
/*    Disable TC_5                                                          */
/****************************************************************************/
void TC_Disable(void) {
  TC5->COUNT16.CTRLA.reg &= ~TC_CTRLA_ENABLE;
  while (TC_IsSyncing());
}

/****************************************************************************/
/*              Set prescaler for Timer TC5                                 */
/****************************************************************************/
//The clock normally counts at the GCLK_TC frequency, but we can set it to divide that frequency to slow it down
//you can use different prescaler divisons (like TC_CTRLA_PRESCALER_DIV64 to get a different range)
void setDivisor(uint16_t divisor) {
    switch (divisor) {
        case    0: TC_Disable(); break; // Stop Timer
        case    1: TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV1 | TC_CTRLA_ENABLE; break;    //Divide GCLK_TC frequency by 1
        case    2: TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV2 | TC_CTRLA_ENABLE; break;    //Divide GCLK_TC frequency by 2
        case    4: TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV4 | TC_CTRLA_ENABLE; break;    //Divide GCLK_TC frequency by 4
        case    8: TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV8 | TC_CTRLA_ENABLE; break;    //Divide GCLK_TC frequency by 8
        case   16: TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV16 | TC_CTRLA_ENABLE; break;   //Divide GCLK_TC frequency by 16
        case   64: TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV64 | TC_CTRLA_ENABLE; break;   //Divide GCLK_TC frequency by 64
        case  256: TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV256 | TC_CTRLA_ENABLE; break;  //Divide GCLK_TC frequency by 256
        case 1024: TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV1024 | TC_CTRLA_ENABLE; break; //Divide GCLK_TC frequency by 1024       
        default: return;
    }
}

/****************************************************************************/
/*              Interrupt Service Routine (ISR) for timer TC5               */
/****************************************************************************/
void TC5_Handler(void)  {                            //    
  // Check for overflow (OVF) interrupt
  if (TC5->COUNT16.INTFLAG.bit.OVF && TC5->COUNT16.INTENSET.bit.OVF) {
    // Put your timer overflow (OVF) code here:     
    // ...
   
    REG_TC5_INTFLAG = TC_INTFLAG_OVF;         // Clear the OVF interrupt flag
  }

  // Check for maTC_h counter 0 (MC0) interrupt
  if (TC5->COUNT16.INTFLAG.bit.MC0 && TC5->COUNT16.INTENSET.bit.MC0) {
    // Put your counter compare 0 (CC0) code here:
    state = ACTIVE_STATE ;
    //digitalWrite(PIN_MARK, !digitalRead(PIN_MARK)) ;      // Toggle Mark pin
    REG_TC5_INTFLAG = TC_INTFLAG_MC0;         // Clear the MC0 interrupt flag
  }

  // Check for maTC_h counter 1 (MC1) interrupt
  if (TC5->COUNT16.INTFLAG.bit.MC1 && TC5->COUNT16.INTENSET.bit.MC1) {
    // Put your counter compare 1 (CC1) code here:
    // ...
   
    REG_TC5_INTFLAG = TC_INTFLAG_MC1;        // Clear the MC1 interrupt flag
  }
}
