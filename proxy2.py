# -*- coding: utf-8 -*-

import socket
import threading
import re
cache = {}
threads=[]

def asClient(browserConnection):
    try:
        while True:
            data = browserConnection.recv(65535)   
            if not (data and len(data)):
                break
            # print "############ req: ############\n%s\n#######################################" % (data)
            # cturl = re.search(r'GET\s+([^\s]+)\s+HTTP[^\r]*\r\n',data)
            # if cturl:
            #     cturl = cturl.group(1)
            remoteaddr = re.search(r'Host:\s*([^\n\r]*)\s*[\r\n]+',data)
            if remoteaddr:
                remoteaddr=remoteaddr.group(1)
                print "remoteaddr = %s\n" % (remoteaddr)

            else:
                break   
            # if cturl == None: #at the same time resend packet to the server
            #     if cturl in cache:
            #         browserConnection.sendall(cache[cturl][0])
            #         cfg=True         
            #         continue          

            internetSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            nsaddr = (remoteaddr,80)
            internetSock.connect(nsaddr)
            internetSock.settimeout(1.5)
            internetSock.sendall(data)
            
            try:
                while True:
                    ssdata = internetSock.recv(65535)
                    sslen = re.search(r'Content-Length:\s*([0-9]+)\s*\r\n',ssdata)

                    if sslen:
                        sslen = int(sslen.group(1))
                        rawdata = ssdata
                        sslen -= len(ssdata[ssdata.find('\r\n\r\n')+4:]) # truncate http head
                        browserConnection.sendall(ssdata)
                        
                    else:                        
                        if ssdata and len(ssdata):
                            browserConnection.sendall(ssdata)
                            continue
                        else:
                            break
                    
                    while sslen>0:
                        ssdata = internetSock.recv(65535)
                        rawdata+=ssdata
                        sslen-=len(ssdata)
  
                        if ssdata and len(ssdata):
                            browserConnection.sendall(ssdata)   
                # while True:
                #     ssdata = internetSock.recv(65535)
                #     sslen = re.search(r'Content-Length:\s*([0-9]+)\s*\r\n',ssdata)

                #     if sslen:
                #         sslen = int(sslen.group(1))
                #         rawdata = ssdata
                #         sslen -= len(ssdata[ssdata.find('\r\n\r\n')+4:])
                #         browserConnection.sendall(ssdata)
                #         # print "sslen:%d\n" % (sslen)
                #     else:                        
                #         if ssdata and len(ssdata):
                #             browserConnection.sendall(ssdata)
                #             continue
                #         else:
                #             break
                    
                #     while sslen>0:
                #         ssdata = internetSock.recv(65535)
                #         rawdata+=ssdata
                #         sslen-=len(ssdata)
  
                #         if ssdata and len(ssdata):
                #             browserConnection.sendall(ssdata)                    
            except:
                pass
            finally:                
                internetSock.close()
    except:
        pass
    finally:
        browserConnection.close()  
        return 


sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_address = ('localhost', 8889)
sock.bind(server_address)
sock.listen(100)
print  '套接字已建立，开始监听 %d 端口...\n' % (8889)

while True:
    browserConnection , client_address =  sock.accept()
    browserConnection.settimeout(1.5)
    # print  '建立连接，客户端地址为: ',client_address
    t = threading.Thread(target=asClient,args=(browserConnection,)) 
    t.start()
