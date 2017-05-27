# -*- coding: utf-8 -*-

import socket
import threading
import re

cache = {}
forbiddenURL = ["www.163.com", "www.sina.com"]
forbiddenUser = ["127.0.0.1"]
redirectTo = {"www.bilibili.com": "www.icourse163.com"}

def asClient(browserConnection):
    try:
        while True:
            data = browserConnection.recv(65535)   
            if not (data and len(data)):
                break

            # 获取目的主机
            remoteaddr = re.search(r'Host:\s*([^\n\r]*)\s*[\r\n]+',data)
            if remoteaddr:
                remoteaddr=remoteaddr.group(1)
            else:
                break   

            # 禁止访问的URL
            if remoteaddr in forbiddenURL:
                print("URL %s is forbidden..\n", remoteaddr)
                break

            # 重定向到钓鱼网站
            if remoteaddr in redirectTo:
                remoteaddr = redirectTo[remoteaddr]

            internetSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            nsaddr = (remoteaddr,80)
            internetSock.connect(nsaddr)
            internetSock.settimeout(1.5)
            internetSock.sendall(data)
            
            try:
                while True:
                    ssdata = internetSock.recv(65535)
                    if ssdata and len(ssdata):
                        browserConnection.sendall(ssdata)                      
            except:
                pass
            finally:                
                internetSock.close()
    except:
        pass
    finally:
        browserConnection.close()  
        return 

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_address = ('localhost', 8889)
    sock.bind(server_address)
    sock.listen(100)
    print  '套接字已建立，开始监听 %d 端口...\n' % (8889)

    while True:
        browserConnection , client_address =  sock.accept()
        browserConnection.settimeout(1.5)
        print  '建立连接，客户端地址为: ',client_address
        t = threading.Thread(target=asClient,args=(browserConnection,)) 
        t.start()
