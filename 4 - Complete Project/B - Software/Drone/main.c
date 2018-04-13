/**Olivia Giles
 * Project Lab 3, group 2
 *
 * *Drone Algorithm:
 *  1. Setup
 *  2. receive drive directions from queen
 *  3. transmit magnetometer data at request from queen
 *
 *
 *  Pin assignments
 *      P1.0
 *      P1.1  UART RX
 *      P1.2  UART TX
 *      P1.3
 *      P1.4  SPI Chip Select
 *      P1.5  SPI Clock
 *      P1.6  SPI MISO
 *      P1.7  SPI MOSI
 *
 *      P2.0  H-bridge h1
 *      P2.1  H-bridge enableB
 *      P2.2  H-bridge enableA
 *      P2.3  H-bridge h2
 *      P2.4  H-bridge h3
 *      P2.5  H-bridge h4
 *      P2.6
 *      P2.7
 *
 **/
#include "msp430g2553.h"
#include <msp430.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#define RXD BIT1      //UART
#define TXD BIT2      //UART
#define SCLK BIT5     //SPI
#define MISO BIT6     //SPI
#define MOSI BIT7     //SPI

#define h1      BIT0
#define enableB BIT1
#define enableA BIT2
#define h2      BIT3
#define h3      BIT4
#define h4      BIT5

//magnetometer addresses for data
#define OUT_X_L 28h //X low byte
#define OUT_X_H 29h //X high byte
#define OUT_Y_L 2Ah //Y low byte
#define OUT_Y_H 2Bh //Y high byte

#define instructionXL 0b11101000;

////////////////////////////////////////////////////////////////////////////////////
//       Variables
////////////////////////////////////////////////////////////////////////////////////
const char string[] = { "$$$" };
char btrx[64] = {""};  //bluetooth rx buffer
unsigned int i;       // tx counter
unsigned int j;         // rx counter

char mrx[64] = {""};   //magnetometer rx buffer
unsigned int k;         //rx counter


///////////////////////////////////////////////////////////////////////////////////
//      function declarations
///////////////////////////////////////////////////////////////////////////////////
void setup(void);
void SPI_TX(char toSend);
void drive(char direction);

///////////////////////////////////////////////////////////////////////////////////
//      Start of main program
//////////////////////////////////////////////////////////////////////////////////
int main(void){
    //chip select
    P1DIR |= BIT4;
    P1OUT |= BIT4;           // reset slave

    setup();
    P1OUT &= ~BIT4;          // Now with SPI signals initialized,

    __delay_cycles(1000);

    while (1) //always
    {
        //drive('f');

        /*
        SPI_TX(0b10001111);//read dummy register output: 0011 1101 (3Dh)

        if(mrx[k] == 0x3D){
            while(1){
                SPI_TX(0b10100111); //read = 1, Multiple = 0, address= 27h
                if(mrx[k] != 0x3D){
                    while(1){
                        __delay_cycles(10);
                    }
                }
            }
        }
        */
        //SPI_TX(0b10101001); //read = 1, Multiple = 0, address= 29h
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

        i = 0;
        j=0;
        k=0;

        P2DIR |= 0xFF; // All P2.x outputs
        P2OUT &= 0x00; // All P2.x reset

        P1DIR |= BIT0; //red LED for testing purposes
        P1SEL |= RXD + TXD + MOSI + MISO + SCLK; // setup pins for UART and SPI
        P1SEL2 |= RXD + TXD + MOSI + MISO + SCLK; // "" ""
        P1OUT &= 0x00;

        //TimerA1 for PWM setup
        P2SEL |= 0x06;      // Set selection register 1 for P2.1 and P2.2 timer-function
        TA1CCTL1 = OUTMOD_7;    //Reset/set
        TA1CCR0  = 20000;       //Period
        TA1CCR1  = 10000;       //Duty-cycle
        TA1CTL   = TASSEL_2 + MC_1; //SMCLK, timer in up-mode


        //UART setup
        UCA0CTL1 |= UCSSEL_2; // SMCLK
        //UCA0BR0 = 0x08; // 1MHz 115200
        //UCA0BR1 = 0x00; // 1MHz 115200
        //UCA0MCTL = UCBRS2 + UCBRS0; // Modulation UCBRSx = 5
        UCA0BR0 = 104; //1MHz 9600
        UCA0BR1 = 0;
        UCA0MCTL = UCBRS0; //modulation UCBRSx = 1
        UCA0CTL1 &= ~UCSWRST; // **Initialize USCI state machine**

        //SPI setup
        UCB0CTL1 = UCSWRST;
        UCB0CTL0 |= UCCKPH + UCMSB + UCMST + UCMODE_0 + UCSYNC; // 3-pin active-low slave, 8-bit SPI master
        UCB0CTL1 |= UCSSEL_2; // SMCLK
        UCB0BR0 = 10; //100khz divider
        UCB0BR1 = 0; //second byte of divider (0)
        UCB0CTL1 &= ~UCSWRST; // **Initialize USCI state machine**

        UC0IE |= UCA0RXIE; // Enable USCI_A0 RX interrupt
        UC0IE |= UCB0RXIE;
        __bis_SR_register(GIE); // Enter LPM0 w/ int until Byte RXed
}

/**
 * SPI Transmit
 */
void SPI_TX(char toSend){
    P1OUT &= ~BIT4;
    while(!(IFG2 & UCB0TXIFG)); //TX buffer ready?
    UCB0TXBUF = toSend;
    __delay_cycles(1000);
        //best practice is to ensure UCB0TXIFG is ready
}

/**
 * Drive the tank based on the command received: stop, forward, right, left
 */
void drive( char direction){
    switch(direction) {
       case 's'  :   //stop
          //clear enable bits
          P2OUT &= ~(enableA + enableB+ h1+h2+h3+h4);
          break;
       case 'f' : //go forward
          //turn on h1, h4 and enable A&B
           P2OUT &= ~(h1 + h4);
           P2OUT |= enableA + enableB + h2 + h3;
          break;
      case 'r' : //go right
          //turn on h2, h4 and enable A&B
          P2OUT &= ~(h1 + h3);
          P2OUT |= enableA + enableB + h2 + h4;
          break;
      case 'l':  //go left
          //turn on h1, h3 and enable A&B
          P2OUT &= ~(h2 + h4);
          P2OUT |= enableA + enableB + h1 + h3;
          break;
      case 'b': //go backwards
          //h1, h4, enable A, enable B
          P2OUT &= ~(h2 + h3);
          P2OUT |= enableA + enableB + h1 + h4;
          break;
      case '+': //fast
          TA1CCR1  = 10000;
          break;
      case '-': //slow
          TA1CCR1  = 5000;
          break;
      //default:
          //command is not recognized
     }
}


////////////////////////////////////////////////////////////////////////////////////
// UART Bluetooth interrupt
////////////////////////////////////////////////////////////////////////////////////

/*
#pragma vector=USCIAB0TX_VECTOR
__interrupt void USCI0TX_ISR(void)
{
  //  UCA0TXBUF = string[i++]; // TX next character
    if (i == sizeof(string) - 1){ // TX over?
        UC0IE &= ~UCA0TXIE; // Disable USCI_A0 TX interrupt
        __delay_cycles(10000); //delay for response
    }
}

/** Receive Bluetooth over UART(USCA), Receive magnetometer data over SPI (USCB)
 *  -> parse bluetooth -> drive vector
 */
#pragma vector=USCIAB0RX_VECTOR
__interrupt void USCIAB0RX_ISR(void)
{
    //USCIA, UART Bluetooth interrupt
    if(IFG2 &= UCA0RXIFG)
    {
        if (UCA0RXBUF != '\r') // not carriage return?
        {
            P1OUT ^= BIT0;     //toggle LED
            btrx[j] = UCA0RXBUF; //load in the command to memory
            drive(btrx[j]);  //drive if the command is 'l', 'r', 'f', or 'b'

            if(btrx[j] == 'm') //magnetometer data requested
            {
                //get magnetometer data
                SPI_TX(0b10001111);//read dummy register output: 0011 1101 (3Dh)
                //transmit magnetometer data
                for(i=0; i > sizeof mrx; i=i+1)
                {
                    UC0IE |= UCA0TXIE; //enable USCI_A0 TX interrupt
                    UCA0TXBUF = mrx[i];
                }
            }
            //j++;
        }
        else //carriage return
        {
            j=0;
        }
    }
    //USCIB, SPI, magnetometer interrupt
    else
    {
       mrx[k] = UCB0RXBUF;   //magnetometer rx buffer
       //k++;         //rx counter
       //P1OUT |= BIT0;                          //light LED
       //reset chip select
       __delay_cycles(100);
       P1OUT |= BIT4;
    }
}
