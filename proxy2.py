import socket
import threading
import re
cache={}
threads=[]
dspoofurl='www.provence-tomato.com'
def s2cworker(nsock,connection):
    print "receiving data from server"
    while True:
        print "----------receive------------"
        ssdata = nsock.recv(65535)
        #print len(ssdata)
        #print 'ssdata:'+ssdata

        if ssdata and len(ssdata):
            connection.sendall(ssdata)                    
        else:
            break
    print "exit thread"
    nsock.close()
    connection.close()
    return 

def c2sworker(connection):
    try:
        while True:
            data = connection.recv(65535)   
            if not (data and len(data)):
                break
            ctoken = re.search(r'If-Modified-Since:\s*([^\r]+)\s*\r\n',data)
            cturl = re.search(r'GET\s+([^\s]+)\s+HTTP[^\r]*\r\n',data)
            if cturl:
                cturl = cturl.group(1)
            remoteaddr = re.search(r'Host:\s*([^\n\r]*)\s*[\r\n]+',data)
            cfg = False                

            if remoteaddr:
                remoteaddr=remoteaddr.group(1)
                print remoteaddr


            else:
                break   
            #print remoteaddr

            if cturl and ctoken == None: #at the same time resend packet to the server
                if cturl in cache:
                    print 
                    print 'Yay!'+cturl
                    print 'Cached'
                    print 
                    connection.sendall(cache[cturl][0])
                    cnm = data
                    data = cnm[0:cnm.find('\r\n\r\n')] +'\r\nIf-Modified-Since: ' + cache[cturl][1] +cnm[cnm.find('\r\n\r\n'):]
                    #print repr(data)
                    cfg=True         
                    # t = threading.Thread(target=checkcache,args=(remoteaddr,cturl,data)) 
                    # t.start() 
                    continue          
            elif ctoken:#return 304
                #print '#############################'
                print cturl
                print 'cached:',(cturl in cache)
                if cturl and (cturl in cache):
                    print "******************************"
                    tmpdata = 'HTTP/1.1 304 Not Modified\r\nDate: '+ cache[cturl][1]+  '\r\nServer: Apache\r\nConnection: Keep-Alive\r\nExpires: Sun, 11 May 2025 17:30:46 GMT\r\nCache-Control: max-age=315360000\r\n\r\n'
                    #print repr(tmpdata)
                    connection.sendall( tmpdata)                
                    cfg=True
                    # t = threading.Thread(target=checkcache,args=(remoteaddr,cturl,data)) 
                    # t.start()
                    continue
            nsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
               
            nsaddr = (remoteaddr,80)
             
            nsock.connect(nsaddr)
            nsock.settimeout(1.5)
            nsock.sendall(data)
            #print "receiving data from server"
            rawdata = ''
            #print "**********GlobRecStart***********"
            try:
                while True:
                    ssdata = nsock.recv(65535)
                    #print 'hehe'
                    sslen = re.search(r'Content-Length:\s*([0-9]+)\s*\r\n',ssdata)
                    etoken = re.search(r'Last-Modified:\s*([^\r]+)\s*\r\n',ssdata)
                    if etoken:
                        etoken=etoken.group(1)

                    if sslen:
                        sslen = int(sslen.group(1))
                        rawdata = ssdata
                        
                        sslen -= len(ssdata[ssdata.find('\r\n\r\n')+4:])
                        if not cfg:
                            connection.sendall(ssdata)
                        #print repr(ssdata)
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
                    #print repr(rawdata)
                    #print '1$$$$$$$$$$$$$$$$$$$$$'
                    print etoken
                    print cturl
                    if etoken and cturl :
                        #print '$$$$$$$$$$$$$$$$$$$$$'
                        if cturl in cache and cache[cturl][1]!=etoken:
                            cache[cturl]=(rawdata,etoken)
                        else:
                            if not (cturl in cache):
                                cache[cturl]=(rawdata,etoken)
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
server_address = ('localhost',8889)
#print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)
sock.listen(100)
while True:
    #print  'waiting for a connection'
    connection , client_address =  sock.accept()
    # if client_address[0] in blockeduserlist:
    #     connection.close()
    #     print client_address[0] + " is forbiddened!"
    #     continue
    connection.settimeout(1.5)
    print  'connection from',client_address
    t = threading.Thread(target=c2sworker,args=(connection,)) 
    t.start()
