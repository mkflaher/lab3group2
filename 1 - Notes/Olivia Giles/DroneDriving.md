<h1>Drive commands</h1>
Drone's steering is controlled entirly by the Queen. The Queen sends a command and that command is followed until the next command is sent. 

<table>
  <tr>
    <th>Character</th>
    <th></th>
  </tr>
  <tr>
    <td>'f'</td>
    <td>forward</td>
  </tr>  
  <tr>
    <td>'b'</td>
    <td>backward</td>
  </tr>
    <tr>
    <td>'l'</td>
    <td>left</td>
  </tr>
   <tr>
    <td>'r'</td>
    <td>right</td>
  </tr>
  <tr>
    <td>'+'</td>
    <td>speed up by 10% of max speed</td>
  </tr>
  <tr>
    <td>'-'</td>
    <td>slow down by 10% of max speed</td>
  </tr>
</table>

<h1>H-bridge PWM</h1>
Speed starts at 50% duty cycle.

PWM can be implemented using timer A on the MSP430.

    According to this: https://e2e.ti.com/support/microcontrollers/msp430/f/166/t/381874?Timers-and-PWM-MSP430G2553, 
			• P1.1 - TA0.0 - TA0CCR0
			• P1.2 - TA0.1 - TA0CCR1
			• P1.5 - TA0.0 - TA0CCR0
			• P1.6 - TA0.1 - TA0CCR1
			• P2.0 - TA1.0 - TA1CCR0
			• P2.1 - TA1.1 - TA1CCR1   ==> enable A
			• P2.2 - TA1.1 - TA1CCR1   ==> enable B
			• P2.3 - TA1.0 - TA1CCR0
			• P2.4 - TA1.2 - TA1CCR2
			• P2.5 - TA1.2 - TA1CCR2
				
     Enable A and enable B must be on pins that match PWM setup, or else I would have to set up two clocks. 
     Here, P2.1 and P2.1 are both controlled by timer A 1 counting up to the value in count control register 1.   
     
     CCR0 sets period, CCR1 sets the duty-cycle 
     Code to set up P2.1
		P2SEL  |=  0x02; // Set selection register 1 for timer-function 
		P2SEL2 &= ~0x02; // Clear selection register 2 for timer-function (not needed, as it is 0 after startup)
		
		
		TA1CCTL1 = OUTMOD_7;          // Reset/set 
		TA1CCR0  = 20000;             // Period 
		TA1CCR1  = 1500;              // Duty-cycle 
		TA1CTL   = (TASSEL_2 | MC_1); // SMCLK, timer in up-mode
