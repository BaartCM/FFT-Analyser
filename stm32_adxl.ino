#define MAX_BUFFER 9
#define MAX_PACKETS 5   
#define BAUD 512000 
#define ADC0 PA0             // define the ADC pins you want to use
#define ADC1 PA1
#define ADC2 PA2
#define ADC3 PA3
#define LED  PB9
#define LEDON LOW
#define LEDOFF HIGH 

void handler(void);

//------ Globals -----
static bool read_adxl = false;
static bool start; 
static uint8_t packet[8];          
static uint8_t packet_complete, index_packet;
static uint8_t data[MAX_BUFFER];       //ADC data.
static uint8_t data_array[2*MAX_BUFFER];   //Maximum array size.
int sps_rate = 200;// in microseconds; should give 5KHz toggles
int seq = 31;


void setup() 
{ 
 
    packet_complete = 0;
    index_packet = 0;
    pinMode(LED, OUTPUT);
    pinMode(ADC0, INPUT_ANALOG);
    pinMode(ADC1, INPUT_ANALOG);
    pinMode(ADC2, INPUT_ANALOG);
    pinMode(ADC3, INPUT_ANALOG);
    digitalWrite(LED, LEDOFF);
    start = false;
    Serial.begin(BAUD);
    
    // Setup Timer
    Timer2.setMode(TIMER_CH1, TIMER_OUTPUTCOMPARE);
    Timer2.setPeriod(sps_rate); // in microseconds
    Timer2.setCompare(TIMER_CH1, 1);      // overflow might be small
    Timer2.attachInterrupt(TIMER_CH1, handler);
}

void loop() {
    int counter, i, rdg;
    uint8_t data_rx[1];
    char  ADCH, ADCL;
    
    //--------- Read UART received data----------------
    if (Serial.available() > 0)
    {
        Serial.readBytes(data_rx, 1); 
        if (data_rx[0] == 0x7E)     //End of packet?
        {
            packet_complete = 1;
            index_packet = 0;        
        }
        else 
        {
            packet[index_packet] = data_rx[0];
            ++index_packet;
        }
        if (index_packet > MAX_PACKETS)
        {
            index_packet = 0;
        }
    }
    //---------- If packet complete ------
    if (packet_complete == 1)
    {
        packet_complete = 0;
      
        if ((packet[0] == 'E') && (packet[1] == 'N') && (packet[2] == 'Q'))
        {
            start = true;
            seq=31; // reset sequence number
            if(packet[3]=='1')
            {
              Timer2.setPeriod(10000);
            }
            else if(packet[3]=='2')
            {
              Timer2.setPeriod(4000);
            }
            else if(packet[3]=='3')
            {
              Timer2.setPeriod(2000);
            }
            else if(packet[3]=='4')
            {
              Timer2.setPeriod(1000);
            }
            else if(packet[3]=='5')
            {
              Timer2.setPeriod(500);
            }
             else if(packet[3]=='6')
            {
              Timer2.setPeriod(200);
            }
            else if(packet[3]=='7')
            {
              Timer2.setPeriod(100);
            }
            else
            {
              Timer2.setPeriod(67);
            } 
            flash_led();                            
        }  
        
        if ((packet[0] == 'E') && (packet[1] == 'O') && (packet[2] == 'T'))
        {
            start = false;
            flash_led(); 
        }           
    }
    if ((read_adxl == true)  &&  (start == true))
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
        

        //Encode data[] in data_array[]
        counter = 0;
        for(i=0; i<MAX_BUFFER; ++i)
        {
            if (data[i] == 0x7E)
            {
                data_array[counter] = 0x7D;
                ++counter;
                data_array[counter] = 0x5E;
                ++counter;
            }
            else if (data[i] == 0x7D)
            {
                data_array[counter] = 0x7D;
                ++counter;
                data_array[counter] = 0x5D;
                ++counter;
            }
            else
            {
                data_array[counter] = data[i];
                ++counter;
            }
        }

        //Send data_array[]
        for(i=0; i < counter; ++i)
        {
            Serial.write(data_array[i]);
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

//----------------------------------------
// Timer0 CTC service interrupt
//----------------------------------------
void handler(void) 
{
    read_adxl = true;         //Read accelerometer data.
}

