# -*- coding: utf-8 -*-

import socket
import threading
import re
cache={}
threads=[]

def asClient(connection):
    try:
        while True:
            data = connection.recv(65535)   
            if not (data and len(data)):
                break
            print "############ raw HTTP req: ############\n"
            print data
            print "#######################################"
            cturl = re.search(r'GET\s+([^\s]+)\s+HTTP[^\r]*\r\n',data)
            if cturl:
                cturl = cturl.group(1)
            remoteaddr = re.search(r'Host:\s*([^\n\r]*)\s*[\r\n]+',data)
            cfg = False                

            if remoteaddr:
                remoteaddr=remoteaddr.group(1)
                print "remoteaddr = %s\n" % (remoteaddr)

            else:
                break   
            #print remoteaddr

            if cturl == None: #at the same time resend packet to the server
                if cturl in cache:
                    connection.sendall(cache[cturl][0])
                    cfg=True         
                    continue          

            nsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            nsaddr = (remoteaddr,80)
            nsock.connect(nsaddr)
            nsock.settimeout(1.5)
            nsock.sendall(data)
            #print "receiving data from server"
            rawdata = ''
            
            try:
                while True:
                    ssdata = nsock.recv(65535)
                    #print 'hehe'
                    sslen = re.search(r'Content-Length:\s*([0-9]+)\s*\r\n',ssdata)

                    if sslen:
                        sslen = int(sslen.group(1))
                        rawdata = ssdata
                        
                        sslen -= len(ssdata[ssdata.find('\r\n\r\n')+4:])
                        if not cfg:
                            connection.sendall(ssdata)
                        #print 'ssdata:'+ssdata
                    else:                        
                        if ssdata and len(ssdata):
                            if not cfg:
                                connection.sendall(ssdata)
                            #print repr(ssdata)
                            continue
                        else:
                            break
                    
                    while sslen>0:
                        ssdata = nsock.recv(65535)
                        #print ssdata
                        rawdata+=ssdata
                        sslen-=len(ssdata)
  
                        if ssdata and len(ssdata):
                            if not cfg:
                                connection.sendall(ssdata)                    
                        else:                
                            raise
            except:
                pass
            finally:                
                nsock.close()
    except:
        pass
    finally:
        connection.close()  
        return 


sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_address = ('localhost',16270)
sock.bind(server_address)
sock.listen(100)
print  '套接字已建立，开始监听 %d 端口...\n' % (8889)

while True:
    connection , client_address =  sock.accept()
    connection.settimeout(1.5)
    print  '建立连接，客户端地址为: ',client_address
    t = threading.Thread(target=asClient,args=(connection,)) 
    t.start()
