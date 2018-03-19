/**Olivia Giles
 * Project Lab 3, group 2
 *
 * *Drone Algorithm:
 *  1. Setup
 *
 *  2. When receive drive instructions
 *      a. Read magnetometer
 *      b. Calculate Turn
 *      c. Drive
 **/
#include "msp430g2553.h"
#include <string.h>
#include <math.h>
#include <stdlib.h>

#define RXD BIT1      //UART
#define TXD BIT2      //UART
#define SCLK BIT5     //SPI
#define MISO BIT6     //SPI
#define MOSI BIT7     //SPI

#define CS_OUT    P2OUT
#define CS_DIR    P2DIR
#define CS   BIT0     //Serial port enable (drive low to enable magnetometer)

//magnetometer addresses for data
#define OUT_X_L 28h //X low byte
#define OUT_X_L 29h //X high byte
#define OUT_Y_L 2Ah //Y low byte
#define OUT_Y_H 2Bh //Y high byte


////////////////////////////////////////////////////////////////////////////////////
//       Variables
////////////////////////////////////////////////////////////////////////////////////
const char string[] = { "$$$" };
char btrx[64] = {""};  //bluetooth rx buffer
char *endptr;
//unsigned int i;       // tx counter
unsigned int j;         // rx counter

char mrx[64] = {""};   //magnetometer rx buffer
unsigned int k;         //rx counter

double driveVector[2]; //holds the x and y coordinates of destination of drive vector
int go;                //Boolean flag. 1 = drive, 0 = stop

double heading;
double distance;
double targetHeading;
double targetDistance;

///////////////////////////////////////////////////////////////////////////////////
//      function declarations
///////////////////////////////////////////////////////////////////////////////////
void setup(void);
void SPI_TX(void);
void drive(void);
double readMagnetometer(void);

///////////////////////////////////////////////////////////////////////////////////
//      Start of main program
//////////////////////////////////////////////////////////////////////////////////
int main(void){
    setup();
    go = 0;
    while (1) //always
    {
        while(go && distance){ //Go mode and distance to go
            //where am I?
            heading = readMagnetometer();

            //go to the target
            int tolerance = 5; //Tolerance for heading direction
            if(targetHeading <= (heading + tolerance)  && targetHeading >= (heading - tolerance)){
                drive(); //drone drives. Distance is decremented
            }
            else if(targetHeading > heading){
                //turn right
            }
            else if(targetHeading < heading){
                //turn left
            }
        }
    }
}

/////////////////////////////////////////////////////////////////////////////////////
//   function definitions
/////////////////////////////////////////////////////////////////////////////////////
void setup(void){
    WDTCTL = WDTPW + WDTHOLD; // Stop WDT

        DCOCTL = 0; // Select lowest DCOx and MODx settings
        BCSCTL1 = CALBC1_1MHZ; // Set DCO
        DCOCTL = CALDCO_1MHZ;

        //i = 0;

        P2DIR |= 0xFF; // All P2.x outputs
        P2OUT &= 0x00; // All P2.x reset

        P1DIR |= BIT0; //red LED for testing purposes
        P1SEL |= RXD + TXD + MOSI + MISO + SCLK + CS; // setup pins for UART and SPI
        P1SEL2 |= RXD + TXD + MOSI + MISO + SCLK + CS; // "" ""
        P1OUT &= 0x00;

        //UART setup
        UCA0CTL1 |= UCSSEL_2; // SMCLK
        UCA0BR0 = 0x08; // 1MHz 115200
        UCA0BR1 = 0x00; // 1MHz 115200
        UCA0MCTL = UCBRS2 + UCBRS0; // Modulation UCBRSx = 5
        UCA0CTL1 &= ~UCSWRST; // **Initialize USCI state machine**

        //SPI setup
        UCB0CTL1 = UCSWRST;
        UCB0CTL0 |= UCCKPH + UCMSB + UCMST + UCMODE_0 + UCSYNC; // 3-pin active-low slave, 8-bit SPI master
        UCB0CTL1 |= UCSSEL_2; // SMCLK
        UCB0BR0 = 10; //100khz divider
        UCB0BR1 = 0; //second byte of divider (0)
        UCB0CTL1 &= ~UCSWRST; // **Initialize USCI state machine**
        CS_DIR |= CS;   //setup slave select pin
        CS_OUT |= CS;

        UC0IE |= UCA0RXIE; // Enable USCI_A0 RX interrupt
        __bis_SR_register(GIE); // Enter LPM0 w/ int until Byte RXed
}

/**
 * SPI Transmit
 */
/*void SPI_TX(void){
    for(int x=0; x<=j; x++){
        UCB0TXBUF = rx[x]; //send string index by index
        __delay_cycles(100); // 100 khz divider => 10 us per bit => 80 us per byte
        //best practice is to ensure UCB0TXIFG is ready
    }
}*/
void SendSPIData(char val){
    while(!(IFG2 & UCB0TXIFG)); //TX buffer ready?
    UCB0TXBUF = val
}

//__attribute__((ramfunc)) //attempt to move operation to ram. I don't understand the blue error messages
double readMagnetometer(void){
    //SPI connection
    CS_OUT &= ~(CS); //turn on slave select (active low)
    SendSPIData(); //send address for OUT_X_L register on magnetometer
    //calculate heading
    double yGaussData = 10;
    double xGaussData = 20;
    double compasheading = atan(yGaussData/xGaussData);
    return compasheading;
}
////////////////////////////////////////////////////////////////////////////////////
// UART Bluetooth interrupt
////////////////////////////////////////////////////////////////////////////////////

//we're only RXing over uart, so no need for this tx vector
/*#pragma vector=USCIAB0TX_VECTOR
__interrupt void USCI0TX_ISR(void)
{
    UCA0TXBUF = string[i++]; // TX next character
    if (i == sizeof(string) - 1){ // TX over?
        UC0IE &= ~UCA0TXIE; // Disable USCI_A0 TX interrupt
        __delay_cycles(500000);
    }
} */

/** Receive Bluetooth over UART(USCA), Receive magnetometer data over SPI (USCB)
 *  -> parse bluetooth -> drive vector
 */
#pragma vector=USCIAB0RX_VECTOR
__interrupt void USCI0RX_ISR(void)
{
    //Bluetooth
    if (UCA0RXBUF != '\r') // not carriage return?
    {
        P1OUT ^= BIT0;
        btrx[j] = UCA0RXBUF; //load in the command
        j++;
    }
    else //carriage return
    {
        switch(btrx[0]) {
           case 's'  :   //stop
              go = 0;
              break;
           case 'x' : //x coordinate begins with a 'x'
              driveVector[0] = strtod(btrx+1, &endptr);
              break;
          case 'y' : //y coordinate begins with a 'y'
              driveVector[1] = strtod(btrx+1, &endptr);
        }
        //convert driveVector to polar
        targetHeading = atan(driveVector[0]/driveVector[1]);                    //angle = arctan(y/x)
        targetDistance = sqrt(pow(driveVector[0], 2) + pow(driveVector[1], 2)); //magnitude = sqrt(x^2+ y^2)
    }

    //magnetometer
    if(UCB0RXBUF){

    }
}


/** old code for UART
#pragma vector=USCIAB0RX_VECTOR
__interrupt void USCI0RX_ISR(void)
{
    if (UCA0RXBUF != '\r') // not carriage return?
    {
        P1OUT ^= BIT0;
        rx[j] = UCA0RXBUF;
        j++;
    }
    else //carriage return
    {
        //P1OUT |= BIT0; //test cr received
        UCA0MCTL = 0; //turn off modulation for SPI
        SPI_TX(); //send the string before clearing
        //P1OUT |= BIT0; //test SPI transmitted
        j = 0;
        for(int x=0; x<200;x++){
            rx[x]='\0'; //clear string
        }
        UCA0MCTL = UCBRS2 + UCBRS0; //turn modulation back on when done
    }
}*/
