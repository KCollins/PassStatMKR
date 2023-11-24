#************************************************
#*      *********************************       *
#*      * Dedicated to MKR0 software    *       *
#*      *    Python_MKR0_CV_v0          *       * 
#*      *********************************       *
#************************************************
#********************
#* Import packages  *
#********************
import serial, time, math

import numpy as np
import matplotlib.pyplot as plt
                   
#*******************
#* Some constants  *
#*******************
PORT_MKR0  = "/dev/cu.usbmodem411"
# PORT_BOARD = "/dev/cu.usbmodem"         # for MAC CPU
#PORT_BOARD = "COM"                     # for PC CPU
PORT_BOARD = "/dev/ttyACM" # for linux.

BAUD_RATE =  115200
TIME_OUT = 30

EMPTY    = ""
BOARD    = "BOARD"
#************************************************
ACQ      = "ACQ"
CMD_ACQ  ="  = Start Acquisition"
#************************************************
CMD      = "CMD"
CMD_CMD  = "  = Print Commands available"
#************************************************
FILE     = "FILE"
CMD_FILE = " = Set File index"
#************************************************
PAR      = "PAR"
CMD_PAR  = "  = Print Parameters"
#************************************************
TRA      = "TRA"
CMD_TRA  = "  = Plot the acquisition data"
#************************************************
RTIA     = "RTIA"
CMD_RTIA = " = Set RTIA value"
#************************************************
UNIT     = "UNIT"
CMD_UNIT = " = Set current unit value"
#************************************************
SET      = "SET"
DEF      = ""
#************************************************
EXIT     = "EXIT"
CMD_EXIT = " = Exit the script "
#************************************************

CMD_KEY = {ACQ: CMD_ACQ, CMD: CMD_CMD, FILE: CMD_FILE, PAR: CMD_PAR, TRA: CMD_TRA, RTIA: CMD_RTIA, UNIT: CMD_UNIT, DEF: EMPTY, EXIT: CMD_EXIT}
CMD_AVA = {ACQ: CMD_ACQ, CMD: CMD_CMD, FILE: CMD_FILE, PAR: CMD_PAR, TRA: CMD_TRA, RTIA: CMD_RTIA, UNIT: CMD_UNIT, DEF: EMPTY, EXIT: CMD_EXIT}
CMD_AVA.pop(ACQ) # Command ACQ not available at start up
CMD_AVA.pop(TRA) # Command TRA not available at start up
#print(CMD_AVA)
cmd_code = EMPTY

BOARD_DETECTED = " board detected on "
MKR0   = "Arduino MKR0"
NEW_LINE = "\n"
COMMA    = ","
ACQ_START  = "Acquisition Started"
ACQ_END    = "Acquisition Ended "
TRA_START  = "Tracing Started "
TRA_END    = "Tracing Ended "
INVITE = ">>"
QUOTE  = '"'
EQUAL  = '='
UNDEFINED = "-"
WARNING = [EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY]
WARNING[0]  ="********************************************************************" 
WARNING[1]  ="*   WARNING - You have reached the MAXIMUM number of acquisition   *" 
WARNING[2]  ="*   WARNING -    You can't set up a new acquisition right now      *"
WARNING[3]  ="*   WARNING -        Your FILES will be overwritten                *"
WARNING[4]  ="*   WARNING -            Your DATA will be LOST                    *"
WARNING[5]  ="*   WARNING - Consider CLOSING this program and OPENING it again   *"
WARNING[6]  ="*   WARNING -        The only available Command is TRA             *"
WARNING[7]  ="********************************************************************" + NEW_LINE
MAX_ACQ     = 16
MAX_CYCLE   = 3
NB_PARAM    = 4

DELAY_01s = 0.1
DELAY_1s  = 1
CODE_STEP = 1

QUANT_DAC_MKR0    = 5.0/1023.        # extracted from calibration process
OFFSET_DAC_MKR0   = 512.0            # extracted from calibration process
QUANT_ADC_MKR0    = 3.3/4095
OFFSET_ADC_MKR0   = 2048.0
COEFF_CONV_MKR0   = 1.51              # inverse of the output voltage divider
CONV_PERIOD_MKR0  = 1.0 * 1000000.    # in order to convert in micros and take care of the first stage gain
DELAY_STAB_MKR0   = 2.0

R10k         = 10000.0                   # to be change to the right value
RTIA_MKR0    =  4700.0
KOHM         =  1000.0
CODE_MAX_RTIA = 255
CODE_MIN_RTIA =  12

COEFF_mA     =          1000.0             # scale in mA
COEFF_microA =       1000000.0             # scale in microA
COEFF_nA     =    1000000000.0             # scale in nA
COEFF_pA     = 1000000000000.0             # scale in pA

#***********************
#* File name to modify *
#***********************
FILE_NAME_MKR0   = "Data/Acq_Pot_MKR_ZERO"
FILE_EXTENT = ".txt"
READ_MODE  = "r"
WRITE_MODE = "w"
UTF_8      = "utf-8"

#****************************
#* Array for data from file 
#****************************
x = []
y = []
x_data = [[[] for j in range(MAX_CYCLE)] for i in range(MAX_ACQ)]
y_data = [[[] for j in range(MAX_CYCLE)] for i in range(MAX_ACQ)]
        
#****************************
#* Array cycle and colors 
#****************************        
nb_mes_cycle = [0,0,0,0]
nb_acq_cycle = [0,0,0,0]
gra_color =["b","g","r"]

#****************************
#* Array for PARAMETERS     *
#****************************
params = [UNDEFINED,UNDEFINED,UNDEFINED,UNDEFINED]
param  = [[UNDEFINED,UNDEFINED,UNDEFINED,UNDEFINED] for  i in range(MAX_ACQ)]   # maximum 16 sets of parameters

#*********************************
#* Function for board detection  *
#*********************************
def board_detection():
        global index_acq, board, index_param
        ctrl_while = True
        while (ctrl_while):
                message = BOARD.encode(UTF_8)
                Arduino_Serial.write(message)
                received = Arduino_Serial.readline()[:-2]  # reads line from Arduino MKR0 and strips out NL + CR
                received_utf8 = received.decode(UTF_8)
                print (received_utf8)
                if (received_utf8 == MKR0):                                       
                        ctrl_while = False      # to break the loop
                        board =  received_utf8  
                        print (NEW_LINE + board + BOARD_DETECTED + QUOTE + port_board + QUOTE + NEW_LINE)
                        index_acq   = 0
                        index_param = 0
#end of board detection function

#*********************************
#* Function to set up constants  *
#********************************* 
def set_contants(board):
        global quant_DAC, offset_DAC, quant_ADC, offset_ADC,coeff_conv,conv_period, rtia, delay_stab, gain     
        if (board == MKR0):
                quant_DAC   = QUANT_DAC_MKR0
                offset_DAC  = OFFSET_DAC_MKR0
                quant_ADC   = QUANT_ADC_MKR0
                offset_ADC  = OFFSET_ADC_MKR0 
                coeff_conv  = COEFF_CONV_MKR0
                conv_period = CONV_PERIOD_MKR0
                rtia = RTIA_MKR0
                delay_stab  = DELAY_STAB_MKR0
                gain = -1.0
#end of set_constants function
                
#*********************************
#* Function to set up RTIA       *
#********************************* 
def set_rtia(board):
        global rtia_val
        str_rtia = input(" Enter the RTIA value in kΩ (Return => 4.7 kΩ) : ")
        if (str_rtia == EMPTY):
                rtia_val = RTIA_MKR0
        else:
                rtia_val = float(str_rtia) * KOHM
#end of set_rtia function

#*********************************
#* Function to set up UNIT       *
#********************************* 
def set_unit(board):
        global str_unit, c_unit
        str_unit = input(" Enter the curent unit (mA, uA, nA or pA) (Return => mA) : ")
        if (str_unit == EMPTY or str_unit == "mA"):
                c_unit = COEFF_mA
        elif (str_unit == "uA"):
                c_unit = COEFF_microA
        elif (str_unit == "nA"):
                c_unit = COEFF_nA
        elif (str_unit == "pA"):
                c_unit = COEFF_pA
#end of set_unit function
                
#****************************************
#* Function test the command received   *
#****************************************
def tst_cmd(received):
        global cmd_code, cmd_status
        if (received not in CMD_AVA):
                if (received in CMD_KEY):
                        print ("Command not available")
                        cmd_status = False
                else:
                        cmd_code = SET
                        cmd_status = True
        else:
                cmd_code = received
                cmd_status = True
#end of tst_cmd function
                
#****************************************
#* Function to set up acquisition size  *
#**************************************** 
def set_acq_size(board):
                global nb_cycle, nb_acq_tot, nb_acq_cycle
                if (board == MKR0):
                        nb_acq_half_cycle =  code_vstart - code_vstop
                        if ( nb_acq_half_cycle < 0):
                                nb_acq_half_cycle = - nb_acq_half_cycle  
                        if (nb_cycle == 1):
                                nb_acq_cycle[0] = (2 * nb_acq_half_cycle) + 1
                                nb_acq_tot = nb_acq_cycle[0]
                        if (nb_cycle == 2):
                                nb_acq_cycle[0] = (2 * nb_acq_half_cycle) 
                                nb_acq_cycle[1] = nb_acq_cycle[0] + 1
                                nb_acq_tot = nb_acq_cycle[0] + nb_acq_cycle[1] 
                        if (nb_cycle == 3):
                                nb_acq_cycle[0] = (2 * nb_acq_half_cycle)
                                nb_acq_cycle[1] = nb_acq_cycle[0]
                                nb_acq_cycle[2] = nb_acq_cycle[0] + 1
                                nb_acq_tot = nb_acq_cycle[0] + nb_acq_cycle[1] + nb_acq_cycle[2]
                #print (nb_acq_tot, nb_acq_cycle[0], nb_acq_cycle[1], nb_acq_cycle[2])                              
#end of set_acq_size function
                                
#***************************************
#* Function to set up ACQ values       *
#***************************************
def set_acq_value(board):
        global nb_cycle, code_vstart, code_vstop
        period = round(conv_period * quant_DAC/srate)           # compute the period according to srate
        str_vstart = str(int(round( vstart/(quant_DAC * gain) + offset_DAC)))   # compute the DAC code for Vstart
        str_vstop  = str(int(round(  vstop/(quant_DAC * gain) + offset_DAC)))   # compute the DAC code for Vstop
        str_period = str(period)
        
        transmit = str_cycle + COMMA + str_vstart + COMMA + str_vstop + COMMA + str_period
        message = transmit.encode(UTF_8)
        Arduino_Serial.write(message)
        print ("You Transmitted :", transmit)
        #print ("Acquisition number/cycle :", 2*(int(str_vstart) - int(str_vstop) + 1))               
        nb_cycle    = int(str_cycle)              
        code_vstart = int(str_vstart)
        code_vstop  = int(str_vstop)
#end of set_acq_value function
                                
#************************************
#* Function to set up file          *
#************************************ 
def set_up_file(board, index_file):
        global file
        file_name = FILE_NAME_MKR0                        
        file_name = file_name + str(index_file + index_acq) + FILE_EXTENT 
        file = open(file_name, WRITE_MODE,encoding = UTF_8)   # create a new file
        print(file_name)
#end of set_up_file function 

#************************************
#* Function to handle acquisition   *
#************************************ 
def get_acq():
        global index_acq, index_param, acq_time, x_data, y_data
        i_acq = 0
        ctrl_while = True
        time.sleep(acq_time - 1) # to avoid a long time out for the serial link
        while (ctrl_while):
                data = Arduino_Serial.readline()[:-2]  # reads line from Arduino and stips out NL + CR
                data_utf8 = data.decode(UTF_8)
                if ( data_utf8 != 0 ):                          
                        line = data_utf8.split(COMMA)
                        #print (line)
                        if ( i_acq >= 0 and i_acq < nb_acq_cycle[0]):
                                i_cycle = 0
                        if ( i_acq >= nb_acq_cycle[0] and i_acq < nb_acq_tot ):
                                i_cycle = 1
                        if ( i_acq >= (nb_acq_cycle[0] + nb_acq_cycle[1]) and i_acq < nb_acq_tot ):
                                i_cycle = 2
                        #print(index_acq, i_cycle)
                        val_v = (int(line[0]) - offset_DAC) * gain * quant_DAC
                        val_c = (int(line[1]) - offset_ADC) * quant_ADC * coeff_conv * (c_unit/rtia_val) # select COEFF_mA or COEFF_microA
                        x_data[index_acq][i_cycle].append(val_v)                                                
                        y_data[index_acq][i_cycle].append(val_c)
                        data_file = (f"{val_v:.6f}") + COMMA + (f"{val_c:.6f}") # six decimals
                        nbytes = file.write(data_file + NEW_LINE)   # write data from Arduino in the file + NL  
                        i_acq = i_acq + 1
                        if (i_acq == nb_acq_tot):
                                ctrl_while = False
        index_param += 1
        index_acq   += 1
        file.flush()            # Don't forget to flush before closing the file
        file.close
        CMD_AVA[TRA] = CMD_TRA
        #print(CMD_AVA)
#end of get_acq function
        
#****************************************
#* Function to set acquisition limits   *
#****************************************
def set_acq_limits(params):
        global f_cycle, str_cycle, vstart, vstop, srate, param, index_acq
        for i in range(NB_PARAM) :
                if (i == 0 ):
                    if (params[i] != EMPTY):
                         param[index_acq][0] = params[0]
                    else:
                        params[0] = param[index_acq - 1][0]
                        param[index_acq][0] = params[0]
                    f_cycle = float(params[0])
                    str_cycle  = params[0]
 
                elif (i == 1) :
                    if (params[i] != EMPTY):
                        param[index_acq][1] = params[1]
                    else:
                        params[1] = param[index_acq - 1][1]
                        param[index_acq][1] = params[1]
                    vstart  = float(params[1])
                
                elif (i == 2) :
                    if (params[i] != EMPTY):
                        param[index_acq][2] = params[2]
                    else:
                        params[2] = param[index_acq - 1][2]
                        param[index_acq][2] = params[2]
                    vstop   = float(params[2])
                        
                elif (i == 3) :
                    if (params[i] != EMPTY):
                        param[index_acq][3] = params[3]
                    else:
                        params[3] = param[index_acq - 1][3]
                        param[index_acq][3] = params[3]
                    srate   = float(params[3])        # extracts the srate value in V/s
                                                                            
#print(param[index_acq])
                                                    
#********************************
#* Function to plot cycle       *
#********************************
def plot_cycle (index_acq, nb_cycle, x_data, y_data):
        global str_unit
        for i_cycle in range(nb_cycle):
                x = x_data[index_acq][i_cycle]
                y = y_data[index_acq][ i_cycle]
                plt.plot(x, y, gra_color[i_cycle],label = "Cycle" + str(i_cycle + 1))                              
        flat_x_data = [item for sublist in x_data[index_acq] for item in sublist]
        flat_y_data = [item for sublist in y_data[index_acq] for item in sublist]
        plt.xlim(min(flat_x_data), max(flat_x_data))        # set x limits
        plt.ylim(min(flat_y_data), max(flat_y_data))        # set y limits    
        plt.title("Acquisition " + str(index_acq) +"\n" + "Cycles with a scan rate of " + param[index_acq][3] + " V/s \n Range["+ param[index_acq][1]+ " V, " + param[index_acq][2] + " V]")            # Title
        plt.xlabel("E (V)")             # x labels
        if (str_unit  == "uA"):
                    str_unit = "µA"
        if (str_unit  == ""):
                    print("Using default unit: mA.")
                    str_unit = "mA"
        plt.ylabel("I (" + str_unit + ")")            # y labels
        plt.legend()
        plt.show()          # Show graph on screen
# end of function

                                
#********************************
#* Entering the modem's number  *
#********************************
modem_number = input(" Enter the port's number (Return => default port) : ")
if (modem_number == EMPTY):
        port_board = PORT_MKR0
else:
        modem_number = str(modem_number)
        port_board = PORT_BOARD + modem_number
       
#********************************
#* Openning of the serial link  *
#********************************
Arduino_Serial = serial.Serial(port_board, BAUD_RATE, timeout=TIME_OUT)
time.sleep(DELAY_1s) #give the connection a second to settle

#****************************************
#* Board detection  & set up constants  *
#****************************************
board_detection()
set_contants(board)
index_file = 0

#********************************
#* RTIA set-up & UNIT           *
#********************************
set_rtia(board)
set_unit(board)
        
#********************************
#* Printing of input message    *
#********************************
print ("Enter Parameters like 2,-1.25,1.25,0.5 then ACQ to start acquisition and TRA to graph the data \n")
         
#********************************
#* Infinite loop                *
#********************************                
while True:
        if (index_acq == MAX_ACQ):            # setting WARNING message
                for w in range(8):
                        print(WARNING[w])
                CMD_AVA = {CMD: CMD_CMD, PAR: CMD_PAR, TRA: CMD_TRA, DEF: EMPTY, EXIT: CMD_EXIT}

        received = input(INVITE)
        tst_cmd(received)
        #accepts input puts it in variable 'received'
        if (cmd_code == SET and cmd_status == True): #in case you entered "1,-1.25,1.25,5"
                #print ("You Entered :", received)   
                params = [name.strip() for name in received.split(COMMA)]
                set_acq_limits(params)
                #print(f_cycle, vstart, vstop, srate)                                                     
                acq_time = (2.0 * f_cycle * abs(vstart - vstop)/srate) + delay_stab # add the delay to stabilize vstart
                print( "The acquisition will take roughly : ", (f"{acq_time:.2f}"), " seconds")              
                set_acq_value(board)
                CMD_AVA[ACQ] = CMD_ACQ
        
#********************************
#* "ACQ" is received            *
#********************************
        if ( cmd_code == ACQ and cmd_status == True):                                 #if input is "ACQ"
                message = received.encode(UTF_8)
                Arduino_Serial.write(message)                                                                    
                print(ACQ_START)
                set_up_file(board, index_file)
                time.sleep(DELAY_01s)                
                set_acq_size(board)
                set_acq_limits(params)
                get_acq()
                print (ACQ_END)
#end of first if loop
     

#********************************
#* "TRA" is received            *
#********************************
        if ( cmd_code == TRA and cmd_status == True):                                 #if input is "TRA"                                                                    
                acq_graph = input( "Enter the acquisition's number to graph [0," + str(index_acq -1) +"] (Return => last acq) : ")
                if (acq_graph == EMPTY):
                        index_acq_graph = index_acq - 1
                else:
                        index_acq_graph = int(acq_graph)
                print(TRA_START)
                time.sleep(DELAY_01s)
                plot_cycle (index_acq_graph, nb_cycle, x_data, y_data)
                print(TRA_END)
        #end of if statement              

 
#*******************************
#* "RTIA" is received           *
#*******************************
        if ( cmd_code == RTIA and cmd_status == True):
                set_rtia(board)
        # end of if statement

#*******************************
#* "UNIT" is received           *
#*******************************
        if ( cmd_code == UNIT and cmd_status == True):
                set_unit(board)
        # end of if statement

#*******************************
#* "PAR" is received           *
#*******************************
        if ( cmd_code == PAR and cmd_status == True):
                #print (index_param)
                for i in range(MAX_ACQ):                       
                        str_param = "Acq " + str(i) + " :" + param[i][0]
                        if ( i > (index_param - 1)):
                                str_param = UNDEFINED
                                for j in range(3):
                                        str_param += COMMA + UNDEFINED
                                print (str_param)
                        else:
                                for j in range(3):
                                        str_param += COMMA + param[i][j+1]
                                print (str_param)
                      
#********************************
#* "FILE" is received           *
#********************************
        if ( cmd_code == FILE and cmd_status == True ):
                str_file_index = input(" Enter a number for the starting of indexing file (Return => 0) : ")
                if (str_file_index == EMPTY):
                        str_file_index = "0"
                index_file = int(str_file_index)
                set_up_file(board, index_file)
                           
# end of infinite loop

#********************************
#* "CMD" or "" is received      *
#********************************
        if (cmd_code == CMD or cmd_code == DEF) and cmd_status == True:
                for key in CMD_AVA:
                        if (key != EMPTY):
                                print(key, CMD_AVA[key])
                                
#********************************
#* "EXIT" is received           *
#********************************
        if (cmd_code == EXIT):
                exit()
