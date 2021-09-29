
#objective of program: to open, close and read usb data with refreshing ability
import timeit
import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import os
import time 
import math

#declaring and setting variable defining block data capture size
datapoints = 200

#define arrays
int_data1=np.zeros((datapoints,3),dtype='int16')
time_mul=np.zeros((datapoints,1),dtype='int16')
outbuf=np.zeros((6,1),dtype='uint8')
backbuf=np.zeros((6,1),dtype='uint8')
gainbuf=np.zeros((6,1),dtype='uint8')

#define serial command string
outbuf[0]=0x55 #Header
outbuf[1]=0x4d #M - mode
outbuf[2]=0x30 #code
outbuf[3]=0x6d #m - submode
outbuf[4]=0x30 #code
outbuf[5]=0xaa #Footer

gainbuf[0]=0x55 #Header
gainbuf[5]=0xaa #Footer

#define keyboard commands
experiment={'m':1,'i':3,'q':4}
testcase={'a':1,'o':2,'c':3,'q':4}

experiment_plt={1:'m',3:'i'}
testcase_plt={1:'a',2:'o',3:'c'}


#------------------------------
def is_hex(num):
#------------------------------
	try:
		int(num, 16)
		return True
	except ValueError:
		return False

#------------------------------
def is_float(string):
#------------------------------
    try:
        float(string)
        return True
    except ValueError:
        return False


#------------------------------------
def readusbecho(backbuf1):
#------------------------------------
# reads data single command from usb
    for i in range (0, 1, 1):
        k = 0
        if (ser.in_waiting < 1): # no data at the port
            print('no data')
        while k < 6 :
            chr_data=ser.read(1)
            x = int.from_bytes(chr_data, byteorder='big')
            if k < 1:
                #look for start character
                for nhead in range (0,50,1):
                    if (x == 85): # header found
                        nhead=50
                    else:
                        chr_head=ser.read(1)
                        x=int.from_bytes(chr_head, byteorder='big')
            backbuf1[k]= x
            k+=1
    return #no return?

#------------------------------------
def usbcommand(outbuf1):
#------------------------------------
# writes command to usb and checks received string
    #write data to serial port
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    for i in range (0,6,1):
        ser.write(outbuf1[i])
    s='sendstring {}\n'.format(outbuf1)
    print(s)

    #read back and check sent data
    readusbecho(backbuf)
    s='receivestring {}\n'.format(backbuf)
    print(s)

    #check echoed data
    valid = 1
    for i in range (0,6,1):
        if (backbuf[i] != outbuf1[i]):    
            valid = 0;
    print('sendata=',valid)
    return valid

#------------------------------------
class Index(object):
    ind = 0

    def capture_data(self, event):
        global capture
        capture=1
        #print('capture',state)
        
    def stop(self, event):
        global capture
        capture=2
        #print('stop',state)
        plt.ion
        
    def quit(self,event):
        global capture
        capture=0
        #print('quit',state)
#------------------------------------


#------------------------------------
#Main code:

#define arrays
time1 = np.zeros((datapoints,1),dtype='int32') #stores time data 
data_p1 = np.zeros((datapoints,1),dtype='int16') #stores data to be used in figure 1 plot
data_p2 = np.zeros((datapoints,1),dtype='int16') #stores data to be used in figure 2 plot
data_p1_prev = np.zeros((2,1),dtype='int16') #used in connecting datasets together for data p1
data_p2_prev = np.zeros((2,1),dtype='int16') #used in connecting datasets together for data p2
time_prev = np.zeros((1,1),dtype='int32') #used to test rollover between datasets
data_connect_time = np.zeros((3,1),dtype='int32') #used in connecting datasets together for time
data_connect = np.zeros((3,2),dtype='int16') #used in connecting datasets together for data p1 and p2

#define variables used in program operations
repeat = 0 #conditional variable for if statements regarding plotting and data block connections
start = 0 
start_prev = 0
rollover=0 #variable storing most current rollover multiplier
unit_div = 256 #variable to store divisions of current and voltage data to represent units
time_unit = 0.0001 #variable to convert time data from count to seconds
comm_check = 0 #used for error trap of opening of the USB serial port
capture = 1 #used as a state to control user commands to capture and plot data


modeChar = 0 #variable used to store user input 
usbport= input("Please enter serial port ID: ").strip()
modeChar = input('Experiment? (i=inductor, m=motor or q=quit): ').strip() 

while modeChar.lower() != 'q':

	#open serial port
	#while loop to error trap com port selection
	while(comm_check == 0):
		print('Opening USB port')
		try:
		    ser = serial.Serial(port=usbport, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=0.5)
		    print(ser)
		    print(ser.is_open)
		except ValueError:
			print('USB port not found')
			time.sleep(1) #wait 1s
		else:
			comm_check = 1

	#intialising arrays for new run
	time1 = np.zeros((datapoints,1),dtype='int32')
	data_p1 = np.zeros((datapoints,1),dtype='int16')
	data_p2 = np.zeros((datapoints,1),dtype='int16')

	#intialising operation variables
	repeat = 0 
	start = 0
	start_prev = 0
	rollover=0
	comm_check = 0
	capture = 1

	#User input section
	correct = 0 
	#condition to allow the repeating of experiments
	if(modeChar == 'r'):
		modeChar = input('Experiment? (i=inductor, m=motor or q=quit): ').strip()

	#while loop traps errors for experiment selection
	while(correct == 0):
		#try and except in order to catch error where user enters a invalid option for experiment
		try:
			check=experiment[modeChar.lower()] 
		except KeyError:
			print('Experiment: ' + str(modeChar) +' not recognised, please enter value from the valid list only')
			modeChar = input('Experiment? (i=inductor, m=motor or q=quit): ').strip()
			correct = 0
		else:
			#if modeChar == 'm':
			#	print('for a new test, set the potentiometer fully anticlockwise, and press the reset button on the cypress board')
			temp=experiment[modeChar.lower()] 
			correct = 1

	#if condition to serve quit option 
	if(modeChar=='q'):
		break
	outbuf[1]=0x4d #M - mode
	outbuf[2]=temp
	mode = temp
	outbuf[3]=0x6d #m - submode
	#inductor testcase if condition
	if (outbuf[2]==3):  
		correct1 = 0 #second variable used for error traps
		#while loop to trap error for testcase selection
		while(correct1 == 0):
			try:
				modeChar = input('Test method (o=open loop, c=closed loop, a=ac, or q=quit): ').strip()
				check=testcase[modeChar.lower()]
			except KeyError:
				print('Test method: '+ str(modeChar) +  ' not recognised, please enter a value from the valid list only')
				correct1 = 0
			else:
				temp=testcase[modeChar.lower()]
				correct1 = 1
		if(modeChar=='q'):
			break
		outbuf[4]=temp
	#else then test for motor experiment conditions 
	elif (outbuf[2] ==1):
		outbuf[4]=0x02 #AC motor defaults to closed loop
	else:
		outbuf[4]=0x01 #DC motor defaults to open loop
	submode=temp
	outbuf[5]=0xaa
	#checking for comms error
	commsok=usbcommand(outbuf)
	if (commsok < 1):
		print('Comms error')
		input('Program will restart due to error, press enter to close this message')
		modeChar = 'r'
		continue


#keyboard entry to set PI gains for inductor closed loop case
	if ((mode ==3) and (submode==3)): 
		correct2 = 0
		#error trap for entering of Proportional gain
		while(correct2 == 0):
			gain = input('Enter Proportional gain value (between 0 and 1000): ').strip()
			#if condition to check if gain entered is a float
			if is_float(gain) != True:
				print('Please enter a digit value')
			#if condition to check if gain is in range
			elif (float(gain)<0) or (float(gain)>1000):
				print('Proportional gain out of range, please re-enter')
			else: #convert to int32Q8 format, send high byte first
				correct2 = 1 
				gain = math.floor(float(gain))
				gainbuf[1]=0x50; #P - proportional
				gainbuf[2]=np.uint8(gain/0x100)
				gainbuf[3]=np.uint8(gain-(0x100*outbuf[2]))
				gainbuf[4]=np.uint8(gain-(0x100*outbuf[2])-outbuf[3])*0x100
				gainbuf[5]=0xaa

				#checking for comms error
				commsok=usbcommand(gainbuf)
				if (commsok < 1):
					print('Comms error')
					input('Program will restart due to error, press enter to close this message')
					break
				correct2_inner = 0
				#error trap for entering of integral gain
				while(correct2_inner == 0):            
					gain = input('Integral gain (between 0 and 250000): ').strip()
					#if conditions same purpose as P gain
					if is_float(gain) != True:
						print('Please enter a digit value')
					elif (float(gain)<0) or (float(gain)>250000):
						print('Integral gain out of range, please re-enter both gains')
					else: #convert to int32Q8 format, send high byte first
						gain = math.floor(float(gain))
						correct2_inner = 1
						gain=gain*0.0256 # multiply by delta T =0.1ms and Q8=256
						gainbuf[1]=0x49; #I - integral
						gainbuf[2]=np.uint8(0x00)
						gainbuf[3]=np.uint8(gain/256)
						gainbuf[4]=np.uint8(gain%256)
						gainbuf[5]=0xaa
					#checking for comms error
					commsok=usbcommand(gainbuf)
					if (commsok <1):
						print('Comms error')
						input('Program will restart due to error, press enter to close this message')
						break
					

	#declare plot variables

	#setting of a new object 
	callback = Index()
	plt.ion() #ion() done to allow plotting to be interactive
	fig = plt.figure(1) 
	ax = fig.add_subplot(111)
	plt.subplots_adjust(left = 0.15, bottom = 0.2) #adjusting the borders of the plot screen to be wide enough for the axes titles and the buttons
	axcapture = plt.axes([0.45, 0.01, 0.15, 0.075]) #setting axes of where to place the button capture
	axstop = plt.axes([0.62, 0.01, 0.15, 0.075]) #setting axes of where to place the button stop capture
	axquit = plt.axes([0.8, 0.01, 0.19, 0.075]) #setting axes of where to place the button stop experiment
	bcapture = Button(axcapture, 'Capture', hovercolor='blue') #declaring the buttons
	bstop = Button(axstop, 'Stop capture', hovercolor='blue')
	bquit = Button(axquit, 'Stop experiment', hovercolor='blue')
	bcapture.on_clicked(callback.capture_data) #setting the funtion that the buttons will call
	bstop.on_clicked(callback.stop)
	bquit.on_clicked(callback.quit)

	mode = int(mode)
	submode = int(submode)

	#if condition used to create a second figure for motor case, otherwise one figure is used
	if experiment_plt[mode] == 'm':
		fig2 = plt.figure(2) 
		bx = fig2.add_subplot(111)
		plt.subplots_adjust(left = 0.15, bottom = 0.2) #buttons for the second figure  
		bxcapture = plt.axes([0.45, 0.01, 0.15, 0.075])
		bxstop = plt.axes([0.62, 0.01, 0.15, 0.075])
		bxquit = plt.axes([0.8, 0.01, 0.19, 0.075])
		bcapture1 = Button(bxcapture, 'Capture', hovercolor='blue')
		bstop1 = Button(bxstop, 'Stop capture', hovercolor='blue')
		bquit1 = Button(bxquit, 'Stop experiment', hovercolor='blue')
		bcapture1.on_clicked(callback.capture_data)
		bstop1.on_clicked(callback.stop)
		bquit1.on_clicked(callback.quit)
		bx.grid(color = 'black', linestyle = '--', linewidth = 0.5)

	ax.grid(color = 'black', linestyle = '--', linewidth = 0.5)


	print('press start button on cypress board to start the test')
	print('place some experiment starting directions')
	print(' waiting for data...')

	#Data collection and plotting while loop
	#condition end determined by ratio of total data points to collect to block size 
	while(capture > 0 and commsok >= 1):
		if (capture==1):
			#Data collection section
			i = 0
			n = datapoints

			#where data collection happens for a single block length datapoints
			while (i < n ):
				errflag = 0
				k = 0
				nhead = 0
				x = 0
				byte = 0
				intermediate_data = 0
				
				#while loop where each if statement tests each byte in the line of data
				if (ser.in_waiting < 1): # no data at the port
					pass
				else:
					while (k < 8):
						byte=ser.read(1)
						x = int.from_bytes(byte, byteorder='big')
						if k == 0:
							#try 50 times to find header byte
							for nhead in range (0,50,1):
								if (x == 85): # header found
									nhead=50
								else:
									byte=ser.read(1)
									x=int.from_bytes(byte, byteorder='big')
							#if header not found after 50 attempts then decide its a comms error and restart program 
							if x != 85:
								print("could not find header, comms error predicted. Program will shut down")
								capture = 0
								break

						if k == 1:
							if (x == 238): #error code found, 0xee is 238 in decimal unsigned and -18 signed
								errflag = 1
								intermediate_data = 0
								print('error detected') 
							else:
								intermediate_data = x

						elif k == 2:
						    if (x ==  238) and (errflag > 0): #error code detected again, 0xee is 238 in decimal unsigned and -18 signed
						        errflag = 1
						        i -= 1 	   #if there is an error, turn on errflag and then negate i variable to replace error data
						        print('error detected again') 
						    else:
						        errflag = 0
						        int_data1[i,0] = x + intermediate_data*256 #multiply previous intermediate value by 256 as it's the higher byte in 16 bits
						        intermediate_data = 0

						elif k == 3:
							#if error flag is raised then data discarded and error displayed
						    if (errflag>0):
						        if (x == 8):
						            print('comms error')
						        if (x == 4):
						            print('hardware watchdog error')
						        if (x == 2):
						            print('undefined interrupt error')
						        if (x == 1):
						            print('motor stall error')
						    else:
						    	intermediate_data = x

						elif k == 4:
							#if error flag is raised then data discarded and error displayed
						    if (errflag > 0):                      
						        if (x == 128):
						            print('software watchdog error')
						        if (x == 64):
						            print('AtoD error')
						        if (x == 32):
						            print('connection error')
						        if (x == 16):
						            print('motor open phase error')
						        if (x == 8):
						            print('hardware over current error')
						        if (x == 4):
						            print('integral time over current error')
						        if (x == 2):
						            print('bus under voltage error')
						        if (x == 1):
						            print('bus over voltage error')
						    else:
						    	int_data1[i,1]= x + (intermediate_data)*256
						    	intermediate_data = 0

						elif k == 5:
							intermediate_data = x

						elif k == 6:
							#if error flag is set then don't set time data
							#otherwise check if time data is set, if true discard data collected
						    if (errflag == 0):
						    	int_data1[i,2]= x + (intermediate_data)*256
						    	intermediate_data = 0
						    	if (int_data1[i,2])< 0:
						    		i -= 1
						    		print('negative time')

						elif k == 7:
							pass

						k+=1
					i+=1

			#Plotting section

			#Time subsection
			tlim = 0
			#if statement to set the rollover limit for each experiment
			if experiment_plt[mode] == 'i' and testcase_plt[submode] == 'c':
				tlim=1250
			else:
				tlim=5000

			start_prev = 0

			#recording previous data values
			time_prev[0] = time1[datapoints-1]

			data_p1_prev[0,0] = data_p1[datapoints-1]
			data_p2_prev[0,0] = data_p2[datapoints-1]

			#for loop collecting time data
			#this also sets all variables in time multiplier array to most current rollover value
			#to ensure values prerollover values are correctly set
			for i in range(0,datapoints,1):
				time1[i] = int_data1[i,2]
				time_mul[i,0] = rollover 

			#testing if the rollover occured between last previous dataset and first next dataset values
			test = time1[0] + tlim*rollover
			if (test<time_prev[0]):
				rollover+=1
				for i in range(0,datapoints,1):
					time_mul[i,0] = rollover
			
			#checking if rollover occurs within current dataset
			for i in range (1,datapoints,1):
				if (time1[i] < time1[i-1]):           
					rollover +=1
					start = i
					#apply new rollover to values after rollover
					for a in range(start,datapoints,1):
						time_mul[a,0] = rollover
					#apply previous rollover to values before rollover, not redundant as needed if more than one rollover occurs
					for b in range(start_prev,start,1):
						time_mul[b,0] = rollover-1
					start_prev = start

			#execute rollover calculated to time dataset
			for i in range (0,datapoints,1):
				time1[i] = time1[i] + tlim*time_mul[i,0]

			start = 0

			#data for plot figure 1 being inputted in array
			for i in range(0,datapoints):
				data_p1[i] = int_data1[i,0]


			#data for plot figure 2 being inputted in array
			for i in range(0,datapoints):
				data_p2[i] = int_data1[i,1]


			#setting the array used to connect subsequent blocks to each other
			#repeat variable greater than 0 to avoid the connection of the first 
			#data point to 0,0
			if repeat > 0:
				data_connect_time[0,0] = time_prev[0]
				data_connect_time[1,0] = time1[0]

				data_connect[0,0] = data_p1_prev[0,0]
				data_connect[1,0] = data_p1[0]

				data_connect[0,1] = data_p2_prev[0,0]
				data_connect[1,1] = data_p2[0]


			plt.pause(0.1) #without pause plotting is too fast and it won't show any data 

			#setting data onto plot figures subsection
			#plotting for inductor
			if experiment_plt[mode] == 'i':
				#closed loop plotting
				if testcase_plt[submode] == 'c':
					ax.set_xlabel('Time (s)')
					ax.set_ylabel('Current (A)')
					ax.set_title('Current measured and reference vs time')
					line1, = ax.plot(time1*time_unit,data_p1/unit_div,'r-') #disclaimer: the setting of marker style and marker size doesnt work here, 
					line1, = ax.plot(time1*time_unit,data_p2/unit_div,'b-') #I havent figure out why

					#plotting the connection to between sets of data after 2 datasets exists
					#above for repeat to ensure that connection between first and zero axis doesnt happen 
					if repeat > 0:
						line1, = ax.plot(data_connect_time[0:2,0]*time_unit,data_connect[0:2,0]/unit_div,'r-') 
						line1, = ax.plot(data_connect_time[0:2,0]*time_unit,data_connect[0:2,1]/unit_div,'b-')

					#setting the legend once, otherwise multiple legends appear
					if repeat == 0:
						plt.legend(["Measured Current (A)","Reference Current (A)"],loc ="upper left")

				#open loop plotting
				elif testcase_plt[submode] == 'o':
					ax.set_xlabel('Time (s)')
					ax.set_ylabel('Current (A)/Voltage (V)')
					ax.set_title('Current measured and Voltage reference vs time')
					line1, = ax.plot(time1*time_unit,data_p1/unit_div,'r-')
					line1, = ax.plot(time1*time_unit,data_p2/unit_div,'b-')

					if repeat > 0:
						line1, = ax.plot(data_connect_time[0:2,0]*time_unit,data_connect[0:2,0]/unit_div,'r-')
						line1, = ax.plot(data_connect_time[0:2,0]*time_unit,data_connect[0:2,1]/unit_div,'b-')

					if repeat == 0:
						plt.legend(["Measured Current (A)","Reference Voltage (V)"],loc ="upper left")

				#AC case plotting
				elif testcase_plt[submode] == 'a':
					ax.set_xlabel('Time (s)')
					ax.set_ylabel('Current (100mA)/Voltage (V)')
					ax.set_title('Current measured and Voltage reference vs time')
					line1, = ax.plot(time1*time_unit,(data_p1/unit_div)*10,'r-') 
					line1, = ax.plot(time1*time_unit,data_p2/unit_div,'b-')		 

					if repeat > 0:
						line1, = ax.plot(data_connect_time[0:2,0]*time_unit,(data_connect[0:2,0]/unit_div)*10,'r-')
						line1, = ax.plot(data_connect_time[0:2,0]*time_unit,data_connect[0:2,1]/unit_div,'b-')

					if repeat == 0:
						plt.legend(["Measured Current (100mA)","Reference Voltage (V)"],loc ="upper left")

			#motor experiment plotting
			elif experiment_plt[mode] == 'm':
				ax.set_xlabel('Time (s)')
				ax.set_ylabel('Speed (rpm)')
				ax.set_title('Speed vs time')	
				bx.set_xlabel('Time (s)')
				bx.set_ylabel('Voltage reference (V)')
				bx.set_title('Voltage reference vs time')
				line1, = ax.plot(time1*time_unit,data_p1,'r-')
				line2, = bx.plot(time1*time_unit,data_p2/unit_div,'b-')

				if repeat > 0:
					line1, = ax.plot(data_connect_time[0:2,0]*time_unit,data_connect[0:2,0],'r-')
					line2, = bx.plot(data_connect_time[0:2,0]*time_unit,data_connect[0:2,1]/unit_div,'b-')
					
			repeat+=1
		else:
			fig.canvas.flush_events()
			if modeChar == 'm':
				fig2.canvas.flush_events()

	input("press enter to close plots")
	plt.close('all')
	ser.close()
	correct = 0
	#error trap to ask to repeat or close plot
	while (correct == 0):
		answer = input('Repeat experiment? (q=quit, r=repeat): ')
		if(answer.lower() == 'r' or answer.lower() == 'q'):
			modeChar = answer.lower()
			correct = 1
		else:
			print("Please enter a valid input, either q or r.")


