# FileTran
_A simple file transfer script in python based on socket level protocol_

## How to Use
- ```git clone git@github.com:qzyse2017/FileTran.git```
- to start the server, use ```python transferServer.py ```
- to start the client, use ```python transferClient.py <server-ip> <server-port>```
- set username and password in ```usr.json```

## Feature
- Commands to get directories' infomation from client: `pwd`,```lcd <directory_name>```, ```lmkdir <directory_name>```, `lp`(analogous to pwd),``ldir``

- Commands to get directories' infomation from server and operate files between client and server：`fdir`,``fmkdir <directory_name>``,``fcd <directory_name>``, ``fput <file_name>``, ``fget <file_name>``, ``fpwd``(get the current directory on server)

- command to exit：```exit``` 

- package the directory and download them all together: use ``pack_get``


## More instructions
I wrote some more instructions about the tool in [report.md](report.md) in Chinese, it was part of my previous report and I do not going to maintain the repository in long term, so I will not translate it to English, if you have any problems, please make a new [issue](https://github.com/qzyse2017/FileTran/issues/new) to report it. Thanks a lot!