/* create a hardware timer */
hw_timer_t * timer = NULL;

#define MAX_BUFFER 9    
#define MAX_PAQ 5   
#define BAUD 512000 
#define ADC0 36        // define the ADC pins you want to use
#define ADC1 39
#define ADC2 34
#define ADC3 35
#define LED 2  
#define LEDOFF LOW
#define LEDON HIGH 
      

//------ Globals -----
static bool read_adxl = false;
static bool enviar; 
static uint8_t paq[8];          //Command reception buffer.
static uint8_t paq_completo, index_paq;    //Pack management flags.  
static uint8_t data[MAX_BUFFER];       //ADC data.
static uint8_t data_cod[2*MAX_BUFFER];   //Maximum array size.
int sps_rate = 200;// in microseconds; should give 5KHz toggles
int seq = 31;

//----------------------------------------
// Timer0 CTC service interrupt
//----------------------------------------
void IRAM_ATTR onTimer()
{
  read_adxl = true;         //Read accelerometer data.
}

void setup() 
{ 
 
    paq_completo = 0;
    index_paq = 0;
    pinMode(LED, OUTPUT);
    digitalWrite(LED, LOW);    // turn the LED off by making the voltage HIGH
    enviar = false;
    Serial.begin(BAUD);
    
    // Setup Timer
    /* Use 1st timer of 4 */
    /* 1 tick take 1/(80MHZ/80) = 1us so we set divider 80 and count up */
    timer = timerBegin(0, 80, true);

    /* Attach onTimer function to our timer */
    timerAttachInterrupt(timer, &onTimer, true);

    /* Set alarm to call onTimer function every second 1 tick is 1us     => 1 second is 1000000us */
    /* Repeat the alarm (third parameter) */
    timerAlarmWrite(timer, sps_rate, true);

    /* Start an alarm */
    timerAlarmEnable(timer);
}

void loop() {
    int conta_cod, i, rdg;
    uint8_t dato_rx[1];
    char  ADCH, ADCL;
    
    //--------- Read UART received data----------------
    if (Serial.available() > 0)
    {
        Serial.readBytes(dato_rx, 1); 
        if (dato_rx[0] == 0x7E)     //End of packet?
        {
            paq_completo = 1;
            index_paq = 0;        
        }
        else 
        {
            paq[index_paq] = dato_rx[0];
            ++index_paq;
        }
        if (index_paq > MAX_PAQ)
        {
            index_paq = 0;
        }
    }
    //---------- If packet complete ------
    if (paq_completo == 1)
    {
        paq_completo = 0;
      
        if ((paq[0] == 'E') && (paq[1] == 'N') && (paq[2] == 'Q'))
        {
            enviar = true;
            seq=31; // reset sequence number
            if(paq[3]=='1')
            {
              timerAlarmWrite(timer, 10000, true);
            }
            else if(paq[3]=='2')
            {
              timerAlarmWrite(timer, 4000, true);
            }
            else if(paq[3]=='3')
            {
              timerAlarmWrite(timer, 2000, true);
            }
            else if(paq[3]=='4')
            {
              timerAlarmWrite(timer, 1000, true);
            }
            else if(paq[3]=='5')
            {
              timerAlarmWrite(timer, 500, true);
            }
             else if(paq[3]=='6')
            {
              timerAlarmWrite(timer, 200, true);
            }
            else if(paq[3]=='6')
            {
              timerAlarmWrite(timer, 100, true);
            }
            else
            {
              timerAlarmWrite(timer, 67, true);
            }
            flash_led();                            
        }  
        
        if ((paq[0] == 'E') && (paq[1] == 'O') && (paq[2] == 'T'))
        {
            enviar = false;
            flash_led();
        }           
    }
    if ((read_adxl == true)  &&  (enviar == true))
    {     
        read_adxl = false;

        rdg=analogRead(ADC0);
        ADCH=(char)(int(rdg/256));
        ADCL=(char)(int(rdg%256));

        data[0] = ADCH;
        data[1] = ADCL;
                   
        rdg=analogRead(ADC1);
        ADCH=(char)(int(rdg/256));
        ADCL=(char)(int(rdg%256));
        data[2] = ADCH;      
        data[3] = ADCL;
  
        rdg=analogRead(ADC2);
        ADCH=(char)(int(rdg/256));
        ADCL=(char)(int(rdg%256));
  
        data[4] = ADCH;    
        data[5] = ADCL;      

        rdg=analogRead(ADC3);
        ADCH=(char)(int(rdg/256));
        ADCL=(char)(int(rdg%256));
  
        data[6] = ADCH;    
        data[7] = ADCL;  

        if(seq++>158)
          seq=32;

        data[8] = (char)seq;
        

        //Encode data[] in data_cod[]
        conta_cod = 0;
        for(i=0; i<MAX_BUFFER; ++i)
        {
            if (data[i] == 0x7E)
            {
                data_cod[conta_cod] = 0x7D;
                ++conta_cod;
                data_cod[conta_cod] = 0x5E;
                ++conta_cod;
            }
            else if (data[i] == 0x7D)
            {
                data_cod[conta_cod] = 0x7D;
                ++conta_cod;
                data_cod[conta_cod] = 0x5D;
                ++conta_cod;
            }
            else
            {
                data_cod[conta_cod] = data[i];
                ++conta_cod;
            }
        }

        //Send data_cod[]
        for(i=0; i < conta_cod; ++i)
        {
            Serial.write(data_cod[i]);
        }
        Serial.write(0x7E);     //End of packet

        
    }         
}

void flash_led()
{
  digitalWrite(LED, LEDON);    
  delay(200);              
  digitalWrite(LED, LEDOFF);  
  delay(200);              
  digitalWrite(LED, LEDON); 
  delay(200);              
  digitalWrite(LED, LEDOFF);  
}


