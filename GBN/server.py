# -*- coding: utf-8 -*-

from socket import *
import select
import time 
def seqIsAvailable():
    global nextseqnum, base, SEND_WIND_SIZE, SEQ_SIZE, isACK
    if (nextseqnum>=base):
        if (nextseqnum-base<=SEND_WIND_SIZE-1 and isACK[nextseqnum]):
            return True
    elif (nextseqnum+SEQ_SIZE-base<=SEND_WIND_SIZE-1 and isACK[nextseqnum]):
        return True
    return False 

def AckHandle(str_num):
    global base, isACK, SEQ_SIZE, nextseqnum
    ackn = ord(str_num) - 1
    print "Recv a ack seq: %d" % ackn
    if (base <= ackn):
        #accumulative ack
        for i in range(base, ackn+1):
            isACK[i] = True
        base = (ackn+1) % SEQ_SIZE
    else:
        #ring back
        for i in range(base, SEQ_SIZE):
            isACK[i] = True
        for i in range(0, ackn+1):
            isACK[i] = True
        base = ackn+1
    print "base is %d" % base
    print "nextseqnum is %d" % nextseqnum

def retransmit():
    #may have problems
    global base, nextseqnum, isACK, total_seq, SEND_WIND_SIZE, SEQ_SIZE
    print "start retransmission"
    print "before retransmission total_seq = %d" % total_seq
    #set ack True for sending purpose 
#    for i in range(SEND_WIND_SIZE):
#        isACK[(i+base)%SEQ_SIZE] = True
#    nextseqnum = base
#    total_seq = total_seq - SEND_WIND_SIZE
    if (nextseqnum >= base):
        step = nextseqnum - base
    else:
        step = nextseqnum + SEQ_SIZE - base
    for i in range(step):
        isACK[(i+base)%SEQ_SIZE] = True
    print "step is %d" % step 
    total_seq = total_seq - step 
    print "after retransmit total_seq = %d" % total_seq
    nextseqnum = base
    
#parameter definition
#send data domain size 
BUFFER_LENGTH = 1024
SEND_LENGTH = 1000
recv_buffer = ""
send_buffer = ""
timeout_in_seconds = 0.01
#Sequence size 
SEQ_SIZE = 20
SEND_WIND_SIZE = 10
serverPort = 9000
isACK = [True for i in range(SEQ_SIZE)]
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('',serverPort))
base = 0
nextseqnum = 0 
total_seq = 0
isFinished = False

def main():
    global BUFFER_LENGTH, recv_buffer, send_buffer, timeout_in_seconds, SEQ_SIZE, serverPort, isACK, nextseqnum, base, isFinished, total_seq
    #set serverSocket is nonblocking 
    fp = open("test.txt", "r")
    content = ''.join(fp.readlines())
    print 'len(content) is %d' % len(content)
    serverSocket.setblocking(0)
    print "The server is ready to receive"
    while (not isFinished):
        #receive connect request from client
        ready = select.select([serverSocket], [], [], timeout_in_seconds)
        if ready[0]:
            recv_buffer, clientAddr = serverSocket.recvfrom(BUFFER_LENGTH)
        else:
            # receives the data from client 
            time.sleep(0.5)
            continue
        #command receive 
        print "recv command from client %s" % recv_buffer 
        if (recv_buffer == "-time"):
            send_buffer = time.asctime(time.localtime(time.time()))
            serverSocket.sendto(send_buffer, clientAddr)
        elif (recv_buffer == '-quit'):
            send_buffer = "Good bye~"
            serverSocket.sendto(send_buffer, clientAddr)
        elif (recv_buffer == '-testgbn'):
            wait_counter = 0
            print "Begain to test GBN protocol,please don't abort the process\n"
            print "Shank hands state"
            stage = 0
            isRun = True
            while(isRun):
                if (stage == 0):
                    #sender A 
                    send_buffer = "A"
                    serverSocket.sendto(send_buffer, clientAddr)
                    time.sleep(0.5)
                    stage = 1
                elif (stage == 1):
                    #wait for receive "B"
                    ready = select.select([serverSocket], [], [], timeout_in_seconds)
                    if (ready[0]):
                        recv_buffer, clientAddr = serverSocket.recvfrom(BUFFER_LENGTH)
                        if (recv_buffer[0] == "B"):
                            print "Begin file transfer"
                            base = 0
                            nextseqnum = 0
                            wait_counter = 0
                            total_seq = 0           #total receive package number 
                            stage = 2
                    else:
                        wait_counter = wait_counter + 1
                        if(wait_counter > 20):
                            #connection failed 
                            isRun = False
                            print "Connection setup timeout!"
                        time.sleep(0.5)
                        continue 
                elif (stage == 2):
                    #send one packet each time
                    if (seqIsAvailable()):
                        print "total_seq = %d, base = %d, nextseqnum = %d" % (total_seq, base, nextseqnum)
                        #send data 
                        #since 0 indicates error transmission
                        #send data 
                        if (total_seq*SEND_LENGTH > len(content)):
                            print 'total_seq is %d' % total_seq
                            if (base == nextseqnum):
                                print "File transmission finished\n"
                                #send finished 
                                isFinished = True
                                break
                        else:
                            send_buffer = chr(nextseqnum+1) 
                            isACK[nextseqnum] = False
                            send_buffer += content[total_seq*SEND_LENGTH:(total_seq+1)*SEND_LENGTH]
                            print "Send a packet with a sequence of %d\n" % nextseqnum
                            serverSocket.sendto(send_buffer, clientAddr)
                            nextseqnum = (nextseqnum + 1) % SEQ_SIZE
                            total_seq = total_seq + 1
                            time.sleep(0.5)
                    #wait for ack 
                    ready = select.select([serverSocket], [], [], timeout_in_seconds)
                    if (ready[0]):
                        #receive ack
                        recv_buffer, clientAddr = serverSocket.recvfrom(BUFFER_LENGTH)
                        AckHandle(recv_buffer[0]) #str to int !!
                        #restart timer
                        wait_counter = 0
                    else:
                        #ack is not coming
                        wait_counter = wait_counter + 1
                        if (wait_counter > 20): 
                            retransmit()
                            #restrart timer
                            wait_counter = 0             
    serverSocket.close()    
    fp.close()
if __name__ == "__main__":
    main()