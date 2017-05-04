import socket
import sys
# import threading
import re

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_address = ('localhost',8888)
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
    # connection.settimeout(1.5)
    print  'connection from',client_address
    #print "receiving data from client"
    # t = threading.Thread(target=c2sworker,args=(connection,)) 
    #threads.append(t)
    # t.start()
