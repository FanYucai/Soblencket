# -*- coding: utf-8 -*-


from socket import *
import random 
import time
import select


def displayHelp():
    print "-------------"
    print " -time"
    print " -quit"
    print " -testgbn[][]"
    print "-------------\n"

def ifLost(ratio):
    tmp = random.uniform(0, 1)
    if (tmp<ratio):
        return True
    else:
        return False 

 
SEQ_SIZE = 20
flag1 = True
displayHelp()
random.seed()
fp = open('recv.txt', 'w')
serverName = 'localhost'
serverPort = 8888
clientSocket = socket(AF_INET, SOCK_DGRAM)
BUFFER_LENGTH = 1024
pack_loss_ratio = 0.2
ack_loss_ratio = 0.2
recv_buffer = ""
send_buffer = ""
SEQ_SIZE = 10
TIME_LIMIT = 5
serverAddr = (serverName, serverPort)


if __name__ == "__main__":
    while (flag1):
        command = raw_input("\n>> ")
        if(command.startswith("-testgbn")):
            print "packet: %.2f; ack: %.2f\n" % (pack_loss_ratio, ack_loss_ratio)
            clientSocket.sendto("-testgbn", serverAddr)        
            stage = 0        
            while(True):
                clientSocket.setblocking(0)
                ready = select.select([clientSocket], [], [], TIME_LIMIT)
                if (ready[0]):
                    recv_buffer, recv_addr = clientSocket.recvfrom(BUFFER_LENGTH)
                else:
                    print ">> timeout.\n"
                    flag1 = False
                    break
                if (stage == 0):
                    status_code = recv_buffer[0]
                    if (status_code == 'A'):
                        send_buffer = 'B'
                        clientSocket.sendto(send_buffer, serverAddr)
                        print ">> Connection built.."
                        stage = 1
                        expect_seq = 1
                        last_seq = 0
                    
                elif (stage == 1):
                    # file receiving started 
                    seq_recv = ord(recv_buffer[0])
                    isLoss = ifLost(pack_loss_ratio)
                    if (isLoss):
                        print ">> Packet #%d: Lost" % seq_recv
                        continue
                    else:
                        print ">> Packet #%d: Received" % seq_recv
                    #check whether the packet is expected
                    if (expect_seq == seq_recv):
                        expect_seq = (expect_seq + 1)
                        if (expect_seq == SEQ_SIZE):
                            expect_seq = 1
                        #print "recv data: %s" % recv_buffer[1:]
                        fp.write(recv_buffer[1:])
            
                        #send back ack 
                        send_buffer = chr(seq_recv)
                        last_seq = seq_recv
                    else:
                        #packet is not the expected one, send last ack number 
                        if (last_seq == 0):
                            #error
                            continue 
                        else:
                            #send last_seq ack
                            send_buffer = chr(last_seq)
                    isAckLoss = ifLost(ack_loss_ratio)
                    if (isAckLoss):
                        print ">> Ack #%d: Lost\n" % ord(send_buffer)
                        continue
                    clientSocket.sendto(send_buffer, serverAddr)
                    print ">> ACK #%d: Sent\n" % ord(send_buffer)
                time.sleep(0.5)
        else:
            clientSocket.setblocking(1)
            clientSocket.sendto(command,serverAddr)
            recv_buffer, recv_addr = clientSocket.recvfrom(BUFFER_LENGTH)
            print recv_buffer
            if (recv_buffer == "Bye"):
                break
    fp.close()
   