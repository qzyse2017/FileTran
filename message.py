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


CARRY_CUR_DIR = b'H'#
EXIT = b'Z'


std_msg_length = 4096#standard message length


def pack_login_msg(username,password,status_code):
	#use ":" to split the password and the username 
	seq_num = 0
	msg_content = bytearray(32)
	username += (16-len(username)) * ' ' 
	password += (16-len(password)) * ' '
	msg_content[:16] = username.encode('utf-8')
	msg_content[16:32] = password.encode('utf-8')
	encoded_login_msg = __universal_encode_pack(LOGIN,seq_num,msg_content)
	return encoded_login_msg

def decode_msg(rcv_msg):
	dict_msg = dict()
	status_code = rcv_msg[0:1]
	dict_msg['status_code'] = status_code



	if status_code == GET:
		dict_msg['file_name_get'] = rcv_msg[5:].strip(b'\x00').decode('utf-8')

	elif status_code == GET_SIZE:
		dict_msg['transfer_byte_length'] = int.from_bytes(rcv_msg[1:5],byteorder ='big')
		dict_msg['get_file_size'] = int.from_bytes(rcv_msg[5:9],byteorder ='big')
		transfer_byte_length = dict_msg['transfer_byte_length']
		dict_msg['file_byte'] = rcv_msg[9:transfer_byte_length + 9]

	elif status_code == ON_TRANSFER_GET or status_code == ON_TRANSFER_PUT:
		dict_msg['transfer_byte_length'] = int.from_bytes(rcv_msg[1:5],byteorder = 'big')
	
	elif status_code == PUT:
		#the file name length is contrained to less than 32 bytes
		dict_msg['transfer_byte_length'] = int.from_bytes(rcv_msg[1:5],byteorder = 'big')
		transfer_byte_length = dict_msg['transfer_byte_length'] 
		file_name_byte = bytearray(32)
		file_name_byte =  bytes(rcv_msg[9:41])
		dict_msg['file_name_put'] = file_name_byte.strip(b'\x00').decode('utf-8')
		dict_msg['file_size'] = int.from_bytes(rcv_msg[5:9],byteorder = 'big')
		dict_msg['file_byte'] = rcv_msg[41:41+transfer_byte_length]

	elif status_code == DIR:
		pass

	elif status_code == CARRY_DIR:
		files = []
		read_cursor = 32
		while(read_cursor < 4096):
			file_name = bytes(rcv_msg[read_cursor:read_cursor+32]).strip(b'\x00').decode('utf-8')
			if file_name != '':
				files.append(file_name)
			read_cursor += 32
		dict_msg['dir_result'] = files		

	elif status_code == NO_DIR_FILE:
		pass

	elif status_code == SUCC_PUT:
		pass
	
	elif status_code == ERR_INTERRUPT_PUT:
		dict_msg['err_length'] = int.from_bytes(rcv_msg[1:5],byteorder = 'big')
	
	elif status_code == SUCC_GET:
		pass

	elif status_code == REDUNDANT_FILE:
		pass

	elif status_code == ERR_INTERRUPT_GET:
		dict_msg['err_length'] = int.from_bytes(rcv_msg[1:5],byteorder = 'big')

	elif status_code == CD:
		dict_msg['cd_dir'] = rcv_msg[5:].strip(b'\x00').decode('utf-8')

	elif status_code == MKDIR:
		dict_msg['mkdir_name'] = rcv_msg[5:].rstrip(b'\x00').decode('utf-8')

	elif status_code == PWD:
		pass

	elif status_code == SUCC_LOGIN:
		dict_msg['cur_dir'] = rcv_msg[5:].strip(b'\x00').decode('utf-8')

	elif status_code == ERR_LOGIN:
		dict_msg['err_info'] = rcv_msg[5:].strip(b'\x00').decode('utf-8')

	elif status_code == CARRY_CUR_DIR:
		dict_msg['server_current_dir_item'] = rcv_msg[5:].strip(b'\x00').decode('utf-8') 

	return dict_msg


def encode_msg_byte(status_code,msg_seq,byte_universal_content):
	return __universal_encode_pack(status_code,msg_seq,byte_universal_content)

def encode_msg_str(status_code,msg_seq,str_content):
	byte_content = str_content.encode('utf-8')
	return __universal_encode_pack(status_code,msg_seq,byte_content)


def __universal_encode_pack(status_code,msg_seq,byte_universal_content):
	'''the universal content descript content including filename,file bytecode.etc'''
	encoded_msg = bytearray(std_msg_length)
	#set the byte as status code
	encoded_msg[0:1] = status_code
	encoded_msg[1:5] = msg_seq.to_bytes(4,byteorder = 'big')
	encoded_msg[5:] = byte_universal_content
	return encoded_msg

	




		
		