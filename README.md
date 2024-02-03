# PassStatMKR
Modified software to run the PassStat potentiostat using an Arduino MKR Zero. Initial code provided by Raymond Campagnolo.

The PassStat (https://doi.org/10.1016/j.ohx.2022.e00290) is a low-cost potentiostat based around the Teensy 3.6. However, the Teensy 3 series is now deprecated, and the Teensy 4 series lacks the DAC pin needed for this application. The code and notes in this repository provide updates so that the PassStat board may be used with the Arduino MKR Zero instead of a Teensy.

List of connections:
- IN1 on J1 of PassStat to A0 on MKR Zero
- IN2 on J1 of PassStat to A1 on MKR Zero
- V- on J4 of PassStat to ground rail on breadboard
- V+ on J4 of PassStat to 5V rail on breadboard
- WE (working electrode) on J2 of PassStat to one side of test resistor
- RE and CE (reference and counter electrodes) on J2 of PassStat to other side of test resistor
