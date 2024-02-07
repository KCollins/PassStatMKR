# PassStatMKR
Modified software to run the PassStat potentiostat using an Arduino MKR Zero. Initial code provided by Raymond Campagnolo.

The PassStat (https://doi.org/10.1016/j.ohx.2022.e00290) is a low-cost potentiostat based around the Teensy 3.6. However, the Teensy 3 series is now deprecated, and the Teensy 4 series lacks the DAC pin needed for this application. The code and notes in this repository provide updates so that the PassStat board may be used with the Arduino MKR Zero instead of a Teensy.


## Setup
Jumper positions: With capacitors C3 and C4 at the "north" end of the board:
 - JP1 in "South" configuration
 - JP2 in "East" configuration
 - JP3 jumpered

List of connections:
- IN1 on J1 of PassStat to DAC/A0 on MKR Zero
- CURR_OUT on PassStat to A1 on MKR Zero
- V- on J4 of PassStat GND on MKR0 (may wish to connect both to ground rail on breadboard)
- V+ on J4 of PassStat to 5V on MKR0 (may wish to connect both to positive rail on breadboard)

For testing, connect:
- WE (working electrode) on J2 of PassStat to one side of test resistor
- RE and CE (reference and counter electrodes) on J2 of PassStat to other side of test resistor

## Software
### Required python libraries
You will need the following python libraries installed to run the python script: pip, pyserial, numpy and matplotlib. 
(Make sure to install pyserial and _not_ serial!)

### Connecting to the Board
Refer to the "Computer Control" section of the _HardwareX_ paper. If you are not running Linux, you will have to change Line 33 of the python script. The prefix of the port number will depend on your operating system, and the port number will vary according to what your computer assigns. You will have to [check the port number in Arduino IDE](https://support.arduino.cc/hc/en-us/articles/4406856349970-Select-board-and-port-in-Arduino-IDE)). Once you have your port number, run the python script from the terminal in your computer.

If the computer has difficulty connecting, you may want to close the Arduino IDE. The python script probably won't be able to run if the serial window is open.

An example run of the script in terminal might look something like this: 
```
aurelius@MarcusAurelius:~/Documents/PassStatMKR$ python3 MKR0_CV_RTIA_Acq_Graph_v0.py 
 Enter the port's number (Return => default port) : 0
Arduino MKR0

Arduino MKR0 board detected on "/dev/ttyACM0"

 Enter the RTIA value in kΩ (Return => 1 MΩ) : 
 Enter the curent unit (mA, uA, nA or pA) (Return => mA) : 
Enter Parameters: cycle count, min voltage, max voltage, slew rate. (e.g.:  2,-1.25,1.25,0.5 ). Hit enter, then ACQ to start acquisition and TRA to graph the data 

>>2,-1.25,1.25,0.5
The acquisition will take roughly :  22.00  seconds
You Transmitted : 2,768,256,9775
>>ACQ
Acquisition Started
Data/Acq_Pot_MKR_ZERO0.txt
Acquisition Ended 
>>TRA
Enter the acquisition's number to graph [0,0] (Return => last acq) : 
Tracing Started 
Using default unit: mA.
Tracing Ended 
>>ACQ
Acquisition Started
Data/Acq_Pot_MKR_ZERO1.txt
Acquisition Ended 
>>TRA
Enter the acquisition's number to graph [0,1] (Return => last acq) : 
Tracing Started 
```
