# Socket编程实验报告--文件传输 
## 实验结果简要介绍： 
使用 socket 实现了二进制文件传输功能，基本命令： 
1. 对本地文件夹进行操作：```lcd <directory_name>, lmkdir <directory_name>, lp(类似pwd),ldir ```
2. 对服务端文件进行相关操作：```fdir,fmkdir <directory_name>,fcd <directory_name>. fput <file_name>,fget <file_name>,fpwd（查看用户在服务端进行浏览所处的的位置）```
3. 退出命令：```exit（服务端也退出）```

使用方法为执行 ```python transferClient.py <服务器的 ip> <服务器端口号>```和 ```python transferServer.py``` 

服务器端口可以手动在代码中修改（全文搜索到"port"，然后更改）

附带登陆认证功能，密码用户名通过 server 所在的目录下 usr.json 文件以键值对的形式预定一些用户名和密码。 

实验时设置为： { "1":"1", "usr2":"testkey2", "usr3":"testkey3" } 


## 关键组件： 
代码文件有 message.py，transferServer.py，transferClient.py 三个，server 端和 client 均需要 用到 message.py。 

message.py负责对发送的信息进行编码，对接收到的信息进行解码。decode_msg(rcv_msg) 是 主 要 解 码 函 数 ， encode_msg_byte(status_code,msg_seq,byte_universal_content) 和 encode_msg_str(status_code,msg_seq,str_content)是主要的编码函数。 

对用户名和密码进行处理的函数是message中的pack_login_msg(username,password,status_code)和server下的parse_usr_info(rcv_msg)。 

每一个文件开头处以全局变量形式规定了所有的二进制状态码，后面会将其填充到发送信息 的头部。 

Server 和 client 均将读取网络信息的部分封装成 read_as_bytearray 函数，将传来的信息读成 bytearray，考虑到 bytearray 的操作可以对 byte 串进行修改（bytes 不可以），且 bytearray 的 很多操作是直接使用该位置的引用，减少对内存内容的复制，可以加快操作。


## 步骤说明： 
主要过程是服务端先启动，客户端之后启动，连接到服务端。之后调用 transferFileClient类的start方法，用户输入密码和用户名发给服务端后，服务端先 parse_usr_info 得到密码用户名，再check_user_db从json文件里读取服务端预定义的用户名密码，如果出现匹配，则允许用户登录，否则关闭该连接。 

Client 登录成功后进入 interactive方法，开始不断询问用户输入指令，并且查找对应的方法进行执行。当命令为 l 开头时，表明需要的操作只和本地有关，不发信息给 server，f开头的命令会发信息给 server。 

对于server和client，类似的操作具体在每一端思路一致。 

cd:给全局变量（字符串）current_work_dir 扩充进入的文件夹名称 

dir：调用 os.listdir()返回目录信息 

pwd:返回全局变量 current_work_dir 

mkdir：调用 os.mkdir 

get,put:读取文件，编码二进制，再传输。get 命令的返回会在第一个信息中正文开始部分包 括文件大小。put 命令，正文部分开始处附加该文件的名称和大小。put，get，mkdir 操作都 有检查重名处理，不会出差错。之后把收到的信息解码，创建，写入本地文件。

## 协议设计： 

每个发送的 bytearray 长度固定，4096。开始 1 个 byte 为状态码，涵盖了来自 client 的命令 或者是传输结果反馈等信息，具体参照代码开头部分（任意一个代码文件打开都有）。之后是一个表明内容长度部分，长度 4byte，用于表明传输内容如果是文件byte序列时，这个信 序列包括多少 byte。（此处是我没设计好，中途改变了设计方案，按照现在的设计，其实这部分两个 byte就够用）。 

后面的部分（正文）根据内容不同格式不一。 

主要有： 

传输密码用户名：用户名和密码各占 16byte，限制了用户名和密码的设置不应超过这个长 度。传输时在16byte的填满部分填充b’\x00’，解码时去掉，防止unicode无法正确将bytearray 初始化时包含的 b’\x00’解析为正确字符。 

对登录信息进行反馈，依靠状态码和失败时的字符信息，提示用户名不存在或者密码错误， 传输时反馈信息长度未限制。 

下面针对具体命令根据信息来源说明正文格式 

### dir： 
client：无 

Server：携带当前工作目录下项目的信息，每一个项目为一个名称字符串，unicode 编 码为二进制形式传输，限制长 32byte，空余部分填充 b’\x00’。 

### pwd：
client：无 

Server：server 端当前工作路径，不限制长度，编码二进制后传输 

### mkdir：
client：创建的文件夹名称，unicode 二进制编码，长度不限制，空位置填充 b’\x00’ 

Server：无 

### cd：
client:要进入的文件夹名称，unicode 二进制编码，长度不限制，空位置填充 b’\x00’ 

server：返回 NO_DIR_FILE 的状态码，或者是成功时返回和客户端发送消息相同的信息 回去。 

### get：

client：要获取的文件名称，unicode 二进制编码，长度不限制，空位置填充 b’\x00’， 成功时发送 SUCC_GET 状态码的信息 

Server：第一个包，文件大小（4byte），后面文件内容的byte。后面的包正文为该文件 剩余内容的byte，解析时参考头部 byte 长度信息进行解析。 

### put：
client：第一个包，文件大小（4byte），文件名（32byte），后面文件内容 byte。后面的包正文为该文件剩余内容的 byte，解析时参考头部 byte 长度信息进行解析。 

Server：成功时发送含SUCC_PUT状态码的信息。其中针对put和get，可以通过状态码判断是否是第一个包。

## 可能遇到的问题和解决办法：

### 网络中断：
删掉错误文件，重传 
### 文件过大
导致第一个包含大小信息的部分大小信息被截断，使得传输不完全：删除错误文件， 先在服务端拆分成小文件再传。 

## 改进方案： 
### 设计缺陷： 
在 fget 时候超过一个包时有时候会出现server端 connection.sendall 函数发送停止的问题，基本是由于发送过快，client端丢包，导致server端没有收到预定的回复，出现问题，其实应该sleep几秒的，但是具体没有想到很好的解决方案。

客户端退出后，服务端也会自动退出，这里是之前为了简单就这样设计了，还需要对控制流程再改进。 

缺乏对文件传输中断的处理，状态码虽然有设计，但是实际缺乏检测中断的部分。


## 可以添加的功能： 
### 给文件设置访问权限： 

默认所有文件未声明时为公开可访问，开一个 json 文件，里面包含了特别要求权限的文件 和可以访问的用户名列表。设置一个表示登录用户是谁的全局变量，默认为空串。登录时，给其赋值登录的人名。当其要获取文件时，查看该文件是否在特别权限表中，并确定该用户 是否有权限。新加一个状态码，表示没有权限，返回相关信息给客户端。 

### 在线浏览文件大小，区分文件夹和文件目录： 
在server端读取文件夹下项目信息时调用api加入对其是否是文件夹的判断， 同时检查大小，把传输该信息的包中每一个项目占用的byte数从32个名称大小增加到34byte， 增加的 16bit 中，一个 bit 表示是否是文件夹，2 个 bit 表示大小单位（B，kB，MB，GB），剩下 13 位编 码大小，前 10 位表示整数部分，后 3 位表示小数。 

### 流水线多线程加速下载： 

对于大文件，如果传输速度收到很大限制，可以考虑在服务端多线程处理，边压缩，边传输， 流水线方式进行，client端类似操作，接受并解压（但是好像这样不会快很多，因为压缩后文件一般还是很大）