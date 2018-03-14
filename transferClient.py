import sys
import socket
import hashlib
import os
import message
import packDir


std_msg_length = 4096
current_dir = os.getcwd() 

#Status Code
#FOR CMD 
LOGIN = b'0'#
DIR = b'3'#
PWD = b'4'#
MKDIR = b'6'#
CD = b'7'#
GET = b'9'#
PUT = b'C'#
PAC_GET = b'K'


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



class transferFileClient():
	"""docstring for transferFileClient"""
	def __init__(self, ip_port):
		super(transferFileClient, self).__init__()
		self.ip_port = ip_port

	def connect(self):
		''''connect to the server '''
		self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.client.connect(self.ip_port)

	def start(self):
		'''start the program'''
		self.connect()
		while True:
			#no space in username and password
			username = input("username: ").strip()
			password = input("password: ").strip()

			#transfer the username and password and pack them
			login_msg = message.pack_login_msg(username,password,LOGIN)
			self.client.sendall(login_msg)
			rcv_msg = self.__read_as_bytearray()
			dict_msg = message.decode_msg(rcv_msg)
			status_code = dict_msg['status_code']
			if status_code == SUCC_LOGIN:
				print('you have logined successfully!enter your command')
				cur_server_dir = dict_msg['cur_dir']
				print('in server the current directory is ' + cur_server_dir)
			else:
				self.client.close()
				return

			self.interactive()

	def interactive(self):
		'''begin to interactive'''
		while True:
			command = input("--> ").strip()
			if not command:continue
			if command == "exit":
				send_msg = message.encode_msg_str(EXIT,0,'')
				self.client.sendall(send_msg)
				self.client.close()
				sys.exit(0)
				break
				
			command_name = command.split()[0]
			if hasattr(self,command_name):           
				func = getattr(self,command_name)
				func(command)
			else:print("no command has the name you input")

	def fpwd(self,command):
		'''check the current directory in the server'''
		send_msg = message.encode_msg_str(PWD,0,'')
		self.client.sendall(send_msg)
		rcv_msg = self.__read_as_bytearray()
		dict_msg = message.decode_msg(rcv_msg)
		print('in the server , the current work directory is ' + dict_msg['server_current_dir_item'])


	def fdir(self,command):
		'''check what files the current directory  in the server has'''
		send_msg = message.encode_msg_str(DIR,0,'')
		self.client.sendall(send_msg)
		rcv_msg = self.__read_as_bytearray()
		dict_msg = message.decode_msg(rcv_msg)
		output_string = ''
		for file_item in dict_msg['dir_result']:
			output_string += file_item + ' '
		print(output_string)

		
	def fcd(self,command):
		'''shift to other directory in the server'''
		arg_list = command.split()
		cd_dir_name = arg_list[1]
		send_msg = message.encode_msg_str(CD,0,cd_dir_name)
		self.client.sendall(send_msg)
		rcv_msg = self.__read_as_bytearray()
		dict_msg = message.decode_msg(rcv_msg)
		if dict_msg['status_code'] == NO_DIR_FILE:
			print('no such file or directory')

	def fmkdir(self,command):
		'''create a new directory'''
		arg_list = command.split()
		mkdir_name = arg_list[1]
		send_msg = message.encode_msg_str(MKDIR,0,mkdir_name)
		self.client.sendall(send_msg)

	def fget(self,command):
		'''get file in the server'''
		arg_list = command.split()
		get_file_name = arg_list[1]
		for file in os.listdir(current_dir):
			if file == get_file_name:
				print("redundant file name ,eror")
				return
		send_msg = message.encode_msg_str(GET,0,get_file_name)
		self.client.sendall(send_msg)

		rcv_msg = self.__read_as_bytearray()
		dict_msg = message.decode_msg(rcv_msg)
		status_code = dict_msg['status_code']
		if status_code == NO_DIR_FILE:
			print('no such dir or file')
			return

		file_size = dict_msg['get_file_size']
		f = open(current_dir + '\\' + get_file_name,'wb')
		f.write(dict_msg['file_byte'])
		rcv_file_size = dict_msg['transfer_byte_length']
		#print('file_size: ' + str(file_size))#test

		while rcv_file_size < file_size:
			rcv_msg = self.__read_as_bytearray()
			dict_msg = message.decode_msg(rcv_msg)
			status_code = dict_msg['status_code']
			if status_code == ON_TRANSFER_GET:
				transfer_byte_length = dict_msg['transfer_byte_length']
				file_byte = rcv_msg[5:5+transfer_byte_length]
				f.write(file_byte)
				#print('rcv_file_size: ' + str(rcv_file_size))#test
				rcv_file_size += transfer_byte_length
			else:
				break

		send_msg = message.encode_msg_str(SUCC_GET,0,'')
		self.client.sendall(send_msg)
		f.close()

	def pack_get(self,command):
		arg_list = command.split()
		pack_file_name = arg_list[1]
		for file in os.listdir(current_dir):
			if pack_file_name == file:
				print("redundant file name ,eror")
				return
		send_msg = message.encode_msg_str(PAC_GET,0,pack_file_name)
		self.client.sendall(send_msg)

		rcv_msg = self.__read_as_bytearray()
		dict_msg = message.decode_msg(rcv_msg)
		print(rcv_msg)
		status_code = dict_msg['status_code']
		if status_code == NO_DIR_FILE:
			print('no such dir or file')
			return

		file_size = dict_msg['get_file_size']
		zipName = pack_file_name + '_tmp.zip'
		f = open(current_dir + '\\' + zipName,'wb')
		f.write(dict_msg['file_byte'])
		rcv_file_size = dict_msg['transfer_byte_length']
		#print('file_size: '+ str(file_size))#test


		while rcv_file_size < file_size:
			rcv_msg = self.__read_as_bytearray()
			dict_msg = message.decode_msg(rcv_msg)
			status_code = dict_msg['status_code']
			if status_code == ON_TRANSFER_GET:
				transfer_byte_length = dict_msg['transfer_byte_length']
				file_byte = rcv_msg[5:5+transfer_byte_length]
				f.write(file_byte)
				#print('rcv_file_size: '+ str(rcv_file_size))#test
				rcv_file_size += transfer_byte_length
			else:
				break

		send_msg = message.encode_msg_str(SUCC_GET,0,'')
		self.client.sendall(send_msg)
		f.close()
		packDir.unzipDirectory(current_dir,zipName)
		#print('current_dir: ' + str(current_dir))#test
		#print('zipName: ' + str(zipName))#test
		os.remove(zipName)


	def fput(self,command):
		'''put file to server'''
		arg_list = command.split()
		put_file_name = arg_list[1]
		put_file_path = current_dir + '\\'+ put_file_name 
		file_size = 0
		try:
			file_size = os.path.getsize(put_file_path)
		except OSError as e:
			print('no such file or directory')

		info_legth = 1+4+4+32
		f = open(put_file_path,'rb')
		read_size = min(std_msg_length-info_legth,file_size)
		send_size = read_size
		chunk = f.read(std_msg_length-info_legth)    
		file_size_array = bytearray(4)
		file_size_array[:4] = file_size.to_bytes(4,byteorder = 'big')
		name_byte = bytearray(32)
		name_byte[:32] = put_file_name.encode('utf-8') + b'\x00' * (32-len(put_file_name))
		name_byte += chunk
		file_size_array += name_byte
		send_msg = message.encode_msg_byte(PUT,send_size,file_size_array)
		self.client.sendall(send_msg) 

		info_length = 1+4
		while send_size < file_size:
			read_size = min(std_msg_length-info_legth,file_size - send_size)
			chunk = f.read(read_size) 
			send_msg = message.encode_msg_byte(ON_TRANSFER_PUT,read_size,chunk)
			self.client.sendall(send_msg)
			send_size += read_size 

		f.close()
		rcv_msg = self.__read_as_bytearray()
		dict_msg = message.decode_msg(rcv_msg)

		if dict_msg['status_code'] == ERR_INTERRUPT_PUT:
			print('File transfer error for file : ' + put_file_name)
			return
		elif dict_msg['status_code'] == REDUNDANT_FILE:
			print('the same name file has been in server')
			return
		elif dict_msg['status_code'] == SUCC_PUT:
			return


	def lpwd(self,command):
		print("Current Directory: " + current_dir)

	def lcd(self,command):
		cd_dir_name = command.split()[1]
		cd_dir_name.strip()
		global current_dir
		trunc_pos = 0
		if cd_dir_name == '..':
			for idx in range(len(current_dir)):
				if current_dir[-idx-1] == '\\':
					trunc_pos = -idx-1
					current_dir = current_dir[:trunc_pos]
					break
			print("Current Directory: " + current_dir)
			return

		find_flag = False
		for file in os.listdir(current_dir):
			if file == cd_dir_name:
				find_flag = True
		if find_flag is False:
			print('no such directory')
			return
		current_dir += '\\' + cd_dir_name

		print("Current Directory: " + current_dir)

	def lmkdir(self,command):
		dir_name = command.split()[1]
		os.mkdir(current_dir + '\\' + dir_name)

	def ldir(self,command):
		for file in os.listdir(current_dir):
			file_list = ''
			file_list += ' ' + file
			print(file_list)
		
	def __read_as_bytearray(self):
		buf = bytearray(std_msg_length)
		view = memoryview(buf)
		recvd_msg_length = self.client.recv_into(view)
		return buf

		
if __name__ == '__main__':
	current_dir = os.getcwd()
	try:
		ip = sys.argv[1]
		port = sys.argv[2]
	except IndexError as e:
		print('please enter the right parameter as : <ip addr> <port>')
		sys.exit(0)
	print("destination ip address: " + ip)
	print("destinaton port: " + port)
	ip_port = (ip,int(port))
	client = transferFileClient(ip_port)
	client.start()

