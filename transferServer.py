import socket
import os
import sys
import json
import message


std_msg_length = 4096
usr_info_file = './usr.json'
current_work_dir = os.getcwd()


#Status Code
#FOR CMD 
LOGIN = b'0'#
DIR = b'3'#
PWD = b'4'#
MKDIR = b'6'#
CD = b'7'#
GET = b'9'#
PUT = b'C'#


#FOR RETURNED MSG
ERR_LOGIN = b'2'#
SUCC_LOGIN = b'1'#

CARRY_DIR = b'5'#
NO_DIR_FILE = b'8'#for cd or get 

ERR_INTERRUPT_GET = b'A'#
SUCC_GET = b'B'#
ON_TRANSFER_GET = b'F'#
GET_SIZE = b'J'

ERR_INTERRUPT_PUT = b'D'#
SUCC_PUT = b'E'#
ON_TRANSFER_PUT = b'G'#
REDUNDANT_FILE = b'I'

CARRY_CUR_DIR = b'H'
EXIT = b'Z'

def read_as_bytearray(connection):
	buf = bytearray(std_msg_length)
	view = memoryview(buf)
	recvd_msg_length = connection.recv_into(view)
	return buf

def parse_usr_info(rcv_msg):
	err = False
	username = ""
	password = ""
	if rcv_msg[0:1] != LOGIN:
		err = True
		return username,password,err
	raw_username = (rcv_msg[5:21]).decode('utf-8')
	username = str(raw_username).strip()
	raw_password = (rcv_msg[21:37]).decode('utf-8')
	password = str(raw_password).strip()
	return username,password,err


def check_user_db(username,password):
	f = open(usr_info_file)
	usr_key = json.load(f)
	find_flag = False
	return_msg = ""
	for usr in usr_key:
		if usr == username:
			if usr_key[usr] == password:
				find_flag = True
				return return_msg,find_flag #while find the true usrename and password 
								  #the return message is null
			else:
				return_msg = "wrong password"
				find_flag = False
				return return_msg,find_flag		  

	if find_flag == False:
		return_msg = "no such username"
		return return_msg,find_flag

				
		

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('localhost',4040)) # change localhost and 4040 to IP and PORT# of server
serversocket.listen(1024)

login = False
while True:
	connection,(addr,port) = serversocket.accept()
	if login == False:
		print("Server connected to " + addr)
		running = True
		login_info = read_as_bytearray(connection)
		username,password,parse_err = parse_usr_info(login_info)
		if parse_err:
			print("the first msg is not about login")
			connection.close()
			break
		check_msg,login = check_user_db(username,password)
		login_recv_msg = message.encode_msg_str(SUCC_LOGIN,0,current_work_dir)
		if login:
			connection.sendall(login_recv_msg)
			print(username + " login")
		else:
			login_recv_msg = message.encode_msg_str(ERR_LOGIN,0,check_msg)
			connection.sendall(login_recv_msg)
			print(username + " tried to login but failed due to " + check_msg )
			connection.close()
			break

	while login:
		cmd_rcv = read_as_bytearray(connection)
		dict_msg = message.decode_msg(cmd_rcv)
		status_code = dict_msg['status_code']

		if status_code == DIR:
			array_all = bytearray(27)
			dir_result = bytearray(std_msg_length-32)
			write_pos = 32
			for file in os.listdir(current_work_dir):
				dir_result[write_pos:write_pos+32] = file.encode('utf-8')
				write_pos += 32

			array_all += dir_result
			send_msg = message.encode_msg_byte(CARRY_DIR,0,array_all)
			connection.sendall(send_msg)
			continue     

		elif status_code ==PWD :
			send_message = message.encode_msg_str(CARRY_CUR_DIR,0,current_work_dir)
			connection.sendall(send_message)
		
		elif status_code ==MKDIR :
			mkdir_name = dict_msg['mkdir_name']
			os.mkdir(current_work_dir + '\\' + mkdir_name)
			pass
		
		elif status_code == CD :
			cd_dir = dict_msg['cd_dir']
			find = False
			for file  in os.listdir(current_work_dir):
				if file == cd_dir:
					current_work_dir += '\\' + cd_dir
					find = True
					send_msg = message.encode_msg_str(CD,0,cd_dir)
					connection.sendall(send_msg)
					break
			if find is False:
				send_status_code = NO_DIR_FILE
				send_msg = message.encode_msg_str(NO_DIR_FILE,0,'')
				connection.sendall(send_msg)

		elif status_code == GET :
			file_name_get = current_work_dir + '\\' + dict_msg['file_name_get']
			file_size = 0
			try:
				file_size = os.path.getsize(file_name_get)
			except OSError as e:
				send_msg = message.encode_msg_str(NO_DIR_FILE,0,'')
				connection.sendall(send_msg)
				continue                    
				
			f = open(file_name_get,'rb')
			info_length = 1+4+4
			read_size = min(std_msg_length-info_length,file_size)
			chunk = f.read(read_size)
			file_size_array = bytearray(4)
			file_size_array[:4] = file_size.to_bytes(4,byteorder = 'big')
			file_size_array += chunk
			send_size = read_size
			send_msg = message.encode_msg_byte(GET_SIZE,send_size,file_size_array)
			connection.sendall(send_msg)

			info_length = 1+4
			while send_size < file_size:
				read_size = min(std_msg_length-info_length,file_size-send_size)
				chunk = f.read(read_size)  
				send_msg = message.encode_msg_byte(ON_TRANSFER_GET,read_size,chunk)
				connection.sendall(send_msg)
				send_size += read_size

			f.close()
			rcv_msg = read_as_bytearray(connection)
			dict_msg = message.decode_msg(rcv_msg)
			if dict_msg['status_code'] == ERR_INTERRUPT_GET:
				print('File transfer error for file : ' + file_name_get + 'for user : ' + username)
				continue
			
		elif status_code == PUT :
			first_transfer_byte_length = dict_msg['transfer_byte_length']
			file_name_put = dict_msg['file_name_put']
			file_name_path = current_work_dir + '\\' + file_name_put
			file_byte = dict_msg['file_byte']
			file_all_length = dict_msg['file_size']
			rcv_file_size = first_transfer_byte_length
			for file in os.listdir(current_work_dir):
				if file == file_name_put:
					send_msg = message.encode_msg_str(REDUNDANT_FILE,0,'')
					continue
				
			f = open(file_name_path,'wb')
			f.write(file_byte)
			if file_all_length == rcv_file_size:
				send_msg = message.encode_msg_str(SUCC_PUT,0,'')
				connection.sendall(send_msg)
				f.close()
				continue
			
			while rcv_file_size < file_all_length:
				rcv_msg = read_as_bytearray(connection)
				dict_msg = message.decode_msg(rcv_msg)
				transfer_byte_length = dict_msg['transfer_byte_length']
				rcv_file_size += transfer_byte_length
				file_byte = rcv_msg[5:5+transfer_byte_length]
				f.write(file_byte)
				

			if rcv_file_size == file_all_length:
				send_msg = message.encode_msg_str(SUCC_PUT,0,'')
				connection.sendall(send_msg)
				f.close()
				continue

			if rcv_file_size != file_all_length:
				print('error while transfering file:' + file_name_put)
				send_msg = message.encode_msg_str(ERR_INTERRUPT_PUT,0,'')
				connection.sendall(send_msg)
				f.close()
				continue

		elif status_code == EXIT:
			sys.exit(0)
  
		else:
			pass










