Code for the MSP430g2553 on the drones

USCIA - UART Mode connection to H-05 bluetooth module

<table>
  <tr>
    Pin connections
  </tr>
  <tr>
    <td>MSP430</td>
    <td>H-05</td>
  </tr>
  <tr>
    <td>P1.1 RXD</td>
    <td>TX</td>
  </tr>
  <tr>
    <td>P1.2 TXD</td>
    <td>RX</td>
  </tr>
</table> 

USCIB - SPI Mode connection to LIS3MDL Magnetometer
 
  <table>
  <tr>
    Pin connections
  </tr>
    <tr>
      <td>MSP430</td>
      <td>Magnetometer</td>
    </tr>
    <tr>
      <td>"3-wire mode"</td>
      <td>"4-wire mode"</td>
    </tr>
    <tr>
      <td>P2.0 slave select</td>
      <td>= CS</td>
    </tr>
     <tr>
      <td>P1.5 SCLK clock</td>
      <td>= SPC</td>
    </tr>
     <tr>
      <td>P1.6 MISO</td>
      <td>= SDO</td>
    </tr>
    <tr>
      <td>P1.7 MOSI</td>
      <td>= SDI</td>
    </tr>
  </table>
