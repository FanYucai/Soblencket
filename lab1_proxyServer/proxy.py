# -*- coding: utf-8 -*-

import socket
import threading
import re

def asClient(browserConnection):
    try:
        while True:
            data = browserConnection.recv(65535)   
            if not (data and len(data)):
                break

            remoteaddr = re.search(r'Host:\s*([^\n\r]*)\s*[\r\n]+',data)
            if remoteaddr:
                remoteaddr=remoteaddr.group(1)
                print "remoteaddr = %s\n" % (remoteaddr)
            else:
                break   
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
    server_address = ('localhost', 16270)
    sock.bind(server_address)
    sock.listen(100)
    print  '套接字已建立，开始监听 %d 端口...\n' % (16270)

    while True:
        browserConnection , client_address =  sock.accept()
        browserConnection.settimeout(1.5)
        print  '建立连接，客户端地址为: ',client_address
        t = threading.Thread(target=asClient,args=(browserConnection,)) 
        t.start()