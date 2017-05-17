# -*- coding: utf-8 -*-

from socket import *
import random 
import time
import select
def printTips():
	print  "*****************************************\n"
	print "| -time to get current time |\n"
	print "| -quit to exit client |\n"
	print "| -testgbn to test the gbn |\n"
	print "*****************************************\n"

def lossInLossRatio(ratio):
    tmp = random.uniform(0, 1)
    if (tmp<ratio):
        return True
    else:
        return False 
#parameter definition 
serverName = 'localhost'
serverPort = 9000
clientSocket = socket(AF_INET, SOCK_DGRAM)
BUFFER_LENGTH = 1024
pack_loss_ratio = 0.2
ack_loss_ratio = 0.2
recv_buffer = ""
send_buffer = ""
SEQ_SIZE = 21
TIME_LIMIT = 5
serverAddr = (serverName, serverPort)
fp = open('recv.txt', 'w')

#Sequence size 
SEQ_SIZE = 20
isRun = True
printTips()
random.seed()

while (isRun):
    command = raw_input("Please enter your command:\n")
    if(command == "-testgbn"):
        #start test gbn 
        print "Begin to test GBN protocol, please don't abort the process"
        print "The loss ratio of packet is %.2f,the loss ratio of ack is %.2f\n" % (pack_loss_ratio, ack_loss_ratio)
        clientSocket.sendto("-testgbn", serverAddr)        
        stage = 0        
        while(True):
            clientSocket.setblocking(0)
            ready = select.select([clientSocket], [], [], TIME_LIMIT)
            if (ready[0]):
                recv_buffer, recv_addr = clientSocket.recvfrom(BUFFER_LENGTH)
            else:
                print "timeout disconnect the connection\n"
                isRun = False
                break
            if (stage == 0):
                status_code = recv_buffer[0]
                if (status_code == 'A'):
                    send_buffer = 'B'
                    clientSocket.sendto(send_buffer, serverAddr)
                    print "Ready for file transmission"
                    stage = 1
                    expect_seq = 1
                    last_seq = 0
                    #...
            elif (stage == 1):
                # file receiving started 
                seq_recv = ord(recv_buffer[0])
                isLoss = lossInLossRatio(pack_loss_ratio)
                if (isLoss):
                    print "loss a packet with seq %d" % seq_recv
                    continue
                #check whether the packet is expected
                if (expect_seq == seq_recv):
                    expect_seq = (expect_seq + 1)
                    if (expect_seq == SEQ_SIZE):
                        expect_seq = 1
                    #print "recv data: %s" % recv_buffer[1:]
                    fp.write(recv_buffer[1:])
                    #write to file
                    #send back ack 
                    send_buffer = chr(seq_recv)
                    last_seq = seq_recv
                else:
                    #packet is not expected, send last ack number 
                    if (last_seq == 0):
                        #sender error
                        continue 
                    else:
                        #send last_seq ack
                        send_buffer = chr(last_seq)
                isAckLoss = lossInLossRatio(ack_loss_ratio)
                if (isAckLoss):
                    print "Ack packet with seq %d is lost\n" % ord(send_buffer)
                    continue
                clientSocket.sendto(send_buffer, serverAddr)
                print "Send a ack with sequence %d" % ord(send_buffer)
            time.sleep(0.5)
    else:
        clientSocket.setblocking(1)
        clientSocket.sendto(command,serverAddr)
        recv_buffer, recv_addr = clientSocket.recvfrom(BUFFER_LENGTH)
        print recv_buffer
        if (recv_buffer == "Good bye~"):
            break
    printTips()
fp.close()
#if __name__ == "__main__":
#    print "hello"