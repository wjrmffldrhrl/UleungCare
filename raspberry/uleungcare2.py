import get_sensor as sensor # communication with arduino
import sys
import requests #communication with web server
import json
import os
import time #delay
from datetime import datetime


def IR_send(ser,decode_type,IR_data):

	print('send data ['+str(decode_type)+']'+'['+'0x'+str(IR_data)+']')
	order = '4 '+str(decode_type)+' '+'0x'+str(IR_data)+' '
	print(order)
	ser.write(order.encode())
	time.sleep(1)

def regist_IR(ser):
	decode_type_list = list() # input decode type
	IR_data_list = list() # input IR data
	count = 0

	while True:
		print('wait data')

		data = ser.readline().decode()

		data = data.split(',')

		decode_type_list.append(data[0])
		IR_data_list.append(data[1])

		print(data[0])
		print(data[1])

		count=count+1

		if(count > 20):
			break

	how_many = 0 # find max data

	for i in decode_type_list: # find max decode type
		if(how_many < decode_type_list.count(i)):
			how_many = decode_type_list.count(i)
			decode_type = i

	how_many = 0

	for i in IR_data_list: # find max IR Data
		if(how_many < IR_data_list.count(i)):
			how_many = IR_data_list.count(i)
			IR_data = i

	print("decode type : ",decode_type,'IR data : ',IR_data)
	ser.write(' 2 '.encode()) # end regist


	return [decode_type,IR_data]

	#time.sleep(2)
	#ser.write('2'.encode()) # end regist
	#control termination in arduino

def IR_fileOpen(data):
	f = open('/home/pi/UleungCare/raspberry/RemoteController.txt', 'a', encoding="utf8")

	for i in data:
		f.write(i+'\t')
	f.write('\n')
	f.close()

def IR_fileRead(command):
	f = open('/home/pi/UleungCare/raspberry/RemoteController.txt', 'r', encoding="utf8")
	IRlist = list()
	while True:
		line = f.readline()
		if not line:
			break
		if command in line:
			line = line.replace('\n', '')
			#print(line)
			#print('This Line!!')
			IRlist = list(line.split('\t'))
		#print(line)

	#print(IRlist)
	f.close()

	return IRlist



def main():
	print('connect arduino')
	while True: # wait arduino when didn't connected
		try:
			ser = sensor.set_dev()
			break
		except:
			print('no device')
			time.sleep(1)

	home_data = [0,0] # home data [temperature,light]
	past_remote_data = {} # check data chage
	past_rgb_led ={'ledThreshold':0,'red':0,'green':0,'blue':0}

	ledThreshold = 0

	ledonoff = True # led control with ledThreshold

	while True: # start main code

		print('get home data')
		now = datetime.now()
		data = sensor.get_data(ser) # get temperature & light

		host = os.popen('hostname -I').read() # get host ip
		host = host.replace('\n','')
		host = host.replace(' ','')
		host = 'http://'+host+':8091'
		try: # input data for trans to web server
			home_data = {'temperature':data[0],'light':data[1],'cctvURL':host}

		except: # wait arduino when home data didn't recive
			print('wait arduino')
			time.sleep(1)
			continue


		rs = requests.post('http://kyu9341.pythonanywhere.com/uleung/raspberry/',data=home_data)

		new_remote_data = rs.json() # recive new data
		#('tvOnOff', 0)
		#('airconOnOff', 0)
		#('tvChUpDown', 0)
		#('tvVolUpDown', 0)
		#('airconTempUpDown', 0)
		#('ledRed', 0)
		#('ledGreen', 0)
		#('ledBlue', 255)
		#('ledThreshold', 1)
		#('airconThreshold', 0)

		new_rgb_led = {'red':new_remote_data['ledRed'],'green':new_remote_data['ledGreen'],'blue':new_remote_data['ledBlue']}
		ledThreshold = new_remote_data['ledThreshold']
		tempThreshold = new_remote_data['airconThreshold']
		home_temp = float(data[0])
		print('time :',now)

		try:

			# if data didn't change pass this part
			if new_remote_data == past_remote_data:
				print('same data')

			else:
				print('data change')
				print('control...') # control code is here

				key_list = list(new_remote_data.keys()) # find 999 or -999
				value_list = list(new_remote_data.values())
				#print(key_list)
				#print(value_list)

				regist_flag = 0 # when do remote regist = 1


				if 999 in value_list: # if user want regist remote data
					print('find 999')
					value = 999
					regist_flag = 1
				elif -999 in value_list:
					print('find -999')
					value = -999
					regist_flag = 1
				else:
					regist_flag = 0

				if regist_flag == 1: # regist start
					print('start regist')
					regist_key = key_list[value_list.index(value)] # check remote button name

					if regist_key == 'tvChUpDown': # change regist_key name
						if value == 999:
							regist_key = 'tvChUp'
						elif value == -999:
							regist_key = 'tvChDown'
					elif regist_key == 'tvVolUpDown':
						if value == 999:
							regist_key = 'tvVolUp'
						elif value == -999:
							regist_key = 'tvVolDown'
					elif regist_key == 'airconTempUpDown':
						if value == 999:
							regist_key = 'airconTempUp'
						elif value == -999:
							regist_key = 'airconTempDown'

					ser.write(' 2 '.encode()) # call regist_IR() in arduino
					IR_data = regist_IR(ser)
					IR_data.insert(0,regist_key)
					print('remote data : ',IR_data[0],IR_data[1],IR_data[2])

					IR_fileOpen(IR_data) # write data txt

					#ser.write('2'.encode()) # end regist_IR
					#time.sleep(2)


				# regist end


				# remote control

				IR_list = [0,0,0] 	# input remote data
							# if did not control remote
							# pass this function



				if((new_remote_data['tvOnOff'] != past_remote_data['tvOnOff']) and (past_remote_data['tvOnOff'] != 999)):
					IR_list = IR_fileRead('tvOnOff')
					#print('send IR data :',IR_list[0])
					#IR_send(ser,IR_list[1],IR_list[2])
				elif((new_remote_data['airconOnOff'] != past_remote_data['airconOnOff']) and ( past_remote_data['airconOnOff'] != 999)):
					IR_list = IR_fileRead('airconOnOff')
					#print('send IR data :',IR_list[0])
					#IR_send(ser,IR_list[1],IR_list[2])

				elif(new_remote_data['tvChUpDown'] != 0):
					if(new_remote_data['tvChUpDown']>0):
						IR_list = IR_fileRead('tvChUp')
						#print('send IR data :',IR_list[0])
						#IR_send(ser,IR_list[1],IR_list[2])
					else:
						IR_list = IR_fileRead('tvChUp')
						#print('send IR data :',IR_list[0])
						#IR_send(ser,IR_list[1],IR_list[2])
					repeat = new_remote_data['tvChUpDown']

				elif(new_remote_data['tvVolUpDown'] != 0):
					if(new_remote_data['tvVolUpDown']>0):
						IR_list = IR_fileRead('tvVolUp')
						#print('send IR data :',IR_list[0])
						#IR_send(ser,IR_list[1],IR_list[2])
					else:
						IR_list = IR_fileRead('tvVolDown')
						#print('send IR data :',IR_list[0])
						#IR_send(ser,IR_list[1],IR_list[2])

					repeat = new_remote_data['tvVolUpDown']

				elif(new_remote_data['airconTempUpDown'] != 0):
					if(new_remote_data['airconTempUpDown']>0):
						IR_list = IR_fileRead('airconTempUp')
						#print('send IR data :',IR_list[0])
						#IR_send(ser,IR_list[1],IR_list[2])
					else:
						IR_list = IR_fileRead('airconTempDown')
						#print('send IR data :',IR_list[0])
						#IR_send(ser,IR_list[1],IR_list[2])
					repeat = new_remote_data['airconTempUpDown']
				elif(new_remote_data['powerOnOff'] != 0):
					os.system('sudo init 0') # raspberry power off





				if IR_list == [0,0,0]:
					print('did not control remote')
				elif regist_flag == 0:
					print('send IR data :',IR_list[0])
					IR_send(ser,IR_list[1],IR_list[2])

				regist_flag = 0


		except Exception as t:
			e =  sys.exc_info()[0]
			es = sys.exc_info()[2]
			print('no data',e,es.tb_lineno)
			print(t)




		try:    #ledThreshold control

			if ledonoff:	# led on
				print("led data input & turn on led")
				order = '1 '+str(new_rgb_led['red'])+' '+str(new_rgb_led['green'])+' '+str(new_rgb_led['blue'])+' '
				# need space '(here)1 ' for remote data send
				ser.write(order.encode())
			else:		# led off
				print('led off (did not pass ledThreshold)')
				order = '1 0 0 0 '
				ser.write(order.encode())



			if ledThreshold == 1: # led always on
				ledonoff = True

			elif ledThreshold == 2:
				if int(home_data['light']) > 100:
					ledonoff = True
				else:
					ledonoff = False
					#print('led off')
					#order = '1 0 0 0'
					#ser.write(order.encode())

			elif ledThreshold == 3:
				if int(home_data['light']) > 250:
					ledonoff = True
				else:
					ledonoff = False
					#print('led off')
					#order = '1 0 0 0'
					#ser.write(order.encode())

			elif ledThreshold == 4:
				if int(home_data['light']) > 400:
					ledonoff = True
				else:
					ledonoff = False
					#print('led off')
					#order = '1 0 0 0'
					#ser.write(order.encode())

			elif ledThreshold == 5:
				if int(home_data['light']) > 600:
					ledonoff = True
				else:
					ledonoff = False
					#print('led off')
					#order = '1 0 0 0'
					#ser.write(order.encode())

		except:
			es = sys.exc_info()[0]
			print('ledThreshold error : ',es)



#		try: # aircon temp control
#
#
#			if new_remote_data['airconThreshold'] != 0: # when user want control temp
#
#				if (home_temp+2) > tempThreshold: # temp over Threshold 
#					if new_remote_data['airconOnOff'] == 0: # airconditioner off
#						print('home temp high, turn on airconditioner')
#						IR_list = IR_fileRead('airconOnOff')
#						print('send IR data :',IR_list[0])
#						IR_send(ser,IR_list[1],IR_list[2])
#					else:					# airconditioner on
#						print('home temp high, airconditioner aleady')
#						IR_list = IR_fileRead('airconTempDown')
#						print('send IR data :',IR_list[0])
#						IR_send(ser,IR_list[1],IR_list[2])
#				else:				# temp down
#					if new_remote_data['airconOnOff'] == 1: # airconditioner on
#						print('now home temp down, turn off airconditioner')
#						IR_list = IR_fileRead('airconOnOff')
#						print('send IR data :',IR_list[0])
#						IR_send(ser,IR_list[1],IR_list[2])
#
#
#			else:
#				print('user did not want control temp')
#
#
#
#		except Exception as t:
#			e =  sys.exc_info()[0]
#			es = sys.exc_info()[2]
#			print('aircon temp threshold error',e,es.tb_lineno)
#			print(t)
#


		for data in new_remote_data.items(): # print remote data
			print(data)

		past_remote_data = new_remote_data # data sync
		past_rgb_led = new_rgb_led
		print('\n')
		time.sleep(2)



#os.system('sh home/pi/mjpg.sh')
main()
