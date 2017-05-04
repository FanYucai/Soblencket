#include <stdio.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>
#include <string.h>
#include <arpa/inet.h>
#include <cstring>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/shm.h>
#include <thread>
#include <iostream>
#include <netdb.h>

#define MAXSIZE 65507 //发送数据报文的最大长度
#define HTTP_PORT 8888 //http 服务器端口
#define QUEUE 20

//Http 重要头部数据
struct HttpHeader{
    char method[4]; // POST 或者 GET，注意有些为 CONNECT，本实验暂不考虑
    char url[1024]; // 请求的 url
    char host[1024]; // 目标主机
    char cookie[1024 * 10]; //cookie
    HttpHeader(){
        memset(this, 0, sizeof(HttpHeader));
    }
};

// unsigned int __stdcall ProxyThread(LPVOID lpParameter);

// 代理相关参数
// SOCKET ProxyServer;
sockaddr_in ProxyServerAddr;
const int ProxyPort = 8888;

//由于新的连接都使用新线程进行处理，对线程的频繁的创建和销毁特别浪费资源
//可以使用线程池技术提高服务器效率
// const int ProxyThreadMaxNum = 20;

struct ProxyParam{
    int clientSocket;
    int serverSocket;
};

bool InitSocket();
void ParseHttpHead(char *buffer, HttpHeader* httpHeader);
int ConnectToServer(char* host);
unsigned int ProxyThread(ProxyParam* lpParameter);


int main(int argc, char* argv[])
{
    printf("代理服务器正在启动\n");
    printf("初始化...\n");

    int ss = socket(AF_INET, SOCK_STREAM, 0);
    //printf("%d\n",ss);
    struct sockaddr_in server_sockaddr;
    server_sockaddr.sin_family = AF_INET;
    server_sockaddr.sin_port = htons(ProxyPort);
    //printf("%d\n",INADDR_ANY);
    server_sockaddr.sin_addr.s_addr = htonl(INADDR_ANY);
    if(bind(ss, (struct sockaddr* ) &server_sockaddr, sizeof(server_sockaddr))==-1) {
        perror("Error: bind");
        exit(1);
    }
    if(listen(ss, QUEUE) == -1) {
        perror("Error: listen");
        exit(1);
    }
    printf("代理服务器正在运行，监听端口 %d\n",ProxyPort);
    ProxyParam *lpProxyParam;
    int conn;
    // HANDLE hThread;
    // DWORD dwThreadID;
    while(1) {
        // 成功返回非负描述字，出错返回-1
        conn = accept(ss, NULL, NULL);
        if( conn < 0 ) {
            perror("Error: connect");
            exit(1);
        }
        printf("successfully accepted...");
        lpProxyParam = new ProxyParam;
        if(lpProxyParam == NULL){continue; }
        lpProxyParam->clientSocket = conn;
        ProxyThread(lpProxyParam);
        // hThread = (HANDLE)_beginthreadex(NULL, 0, &ProxyThread,(LPVOID)lpProxyParam, 0, 0);
        // CloseHandle(hThread);
        // Sleep(200);
    }
    close(conn);
    close(ss);
    return 0;
}

//************************************
// Method: ProxyThread
// FullName: ProxyThread
// Access: public
// Returns: unsigned int __stdcall
// Qualifier: 线程执行函数
// Parameter: LPVOID lpParameter
//************************************
unsigned int ProxyThread(ProxyParam* lpParameter){
    char Buffer[MAXSIZE];
    char *CacheBuffer;
    printf("hahahahahahaha\n");
    memset(Buffer, 0, MAXSIZE);
    int recvSize;
    int ret;
    recvSize = recv(((ProxyParam*)lpParameter)->clientSocket,Buffer,MAXSIZE,0);
    if(recvSize <= 0){
        exit(1);
    }

    HttpHeader* httpHeader = new HttpHeader();
    CacheBuffer = new char[recvSize + 1];
    memset(CacheBuffer, 0, recvSize + 1);
    memcpy(CacheBuffer,Buffer,recvSize);
    ParseHttpHead(CacheBuffer,httpHeader);
    printf("@#$&*()_\n");
    delete CacheBuffer;

    // ########## wrong part #############
    if(ConnectToServer(httpHeader->host) < 0) {
        exit(1);
    }
    printf("代理连接主机 %s 成功\n",httpHeader->host);
    //将客户端发送的 HTTP 数据报文直接转发给目标服务器
    ret = send(((ProxyParam *)lpParameter)->serverSocket,Buffer,strlen(Buffer) + 1,0);
    //等待目标服务器返回数据
    recvSize = recv(((ProxyParam*)lpParameter)->serverSocket,Buffer,MAXSIZE,0);
    if(recvSize <= 0){
        goto error;
    }
    //将目标服务器返回的数据直接转发给客户端
    ret = send(((ProxyParam*)lpParameter)->clientSocket,Buffer,sizeof(Buffer),0);
    //错误处理
    error:
        printf("Error: -123; 关闭套接字\n");
        close(((ProxyParam*)lpParameter)->clientSocket);
        close(((ProxyParam*)lpParameter)->serverSocket);
    return 0;
}


//************************************
// Method: ParseHttpHead
// FullName: ParseHttpHead
// Access: public
// Returns: void
// Qualifier: 解析 TCP 报文中的 HTTP 头部
// Parameter: char * buffer
// Parameter: HttpHeader * httpHeader
//************************************
void ParseHttpHead(char *buffer,HttpHeader * httpHeader){
    char *p;
    char *ptr;
    const char * delim = "\r\n";
    p = strtok_r(buffer,delim,&ptr);//提取第一行
    printf("%s\n",p);
    if(p[0] == 'G'){//GET 方式
        memcpy(httpHeader->method,"GET",3);
        memcpy(httpHeader->url,&p[4],strlen(p) -13);
    }else if(p[0] == 'P'){//POST 方式
        memcpy(httpHeader->method,"POST",4);
        memcpy(httpHeader->url,&p[5],strlen(p) - 14);
    }
    printf("%s\n",httpHeader->url);
    p = strtok_r(NULL,delim,&ptr);

    while(p){
        printf("%s\n *****************", p);
        switch(p[0]){
            case 'H'://Host
              memcpy(httpHeader->host,&p[6],strlen(p) - 6);
              break;
              case 'C'://Cookie
              if(strlen(p) > 8){
                  char header[8];
                  memset(header, 0, sizeof(header));
                  memcpy(header,p,6);
                  if(!strcmp(header,"Cookie")){
                      memcpy(httpHeader->cookie,&p[8],strlen(p) -8);
                  }
              }
              break;
            default:
              break;
        }
        p = strtok_r(NULL,delim,&ptr);
    }
}
//************************************
// Method: ConnectToServer
// FullName: ConnectToServer
// Access: public
// Returns: BOOL
// Qualifier: 根据主机创建目标服务器套接字，并连接
// Parameter: SOCKET * serverSocket
// Parameter: char * host
//************************************
int ConnectToServer(char* host){
    struct hostent* host123 = gethostbyname(host);
    in_addr Inaddr=*( (in_addr*) *host123->h_addr_list);
    printf("%d\n", Inaddr.s_addr);

    // define socketfd
    int socketfd = socket(AF_INET,SOCK_STREAM,0);

    // define sockaddr_in
    struct sockaddr_in serverAddr;
    memset(&serverAddr,0,sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = inet_addr(inet_ntoa(Inaddr));
    serverAddr.sin_addr.s_addr = inet_addr("119.75.217.109");
    serverAddr.sin_port = htons(HTTP_PORT);

    printf("before 123\n");
    int status = connect(socketfd, (struct sockaddr *)&serverAddr, sizeof(serverAddr));
    printf("after 123\n");
    printf("status = %d\n", status);

    if(status != 0)
    {
        close(socketfd);
        printf("Error: in ConnectToServer");
        exit(1);
    }
    return socketfd;
}
