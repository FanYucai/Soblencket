/*
* THIS FILE IS FOR IP TEST
*/
// system support
#include <stdio.h>
#include <memory.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdint.h>
#include "sysInclude.h"

#define HEADER_LEN 20
#define get_ip_version(fb) ((fb) >> 4)
#define get_ihl(fb) (((fb) & 0xf) * 4)
#define set_ip_version(fb, x) ((fb) = ((x) << 4) + ((fb) & 0xf))
#define set_ihl(fb, x) ((fb) = ((fb) & 0xf0) + (x))
#define conv_to_net_order(x) (\
(((x) & 0xff000000) >> 24) + (((x) & 0xff0000) >> 8) + (((x) & 0xff00) << 8 ) + (((x) & 0xff) << 24))

extern void ip_DiscardPkt(char* pBuffer,int type);

extern void ip_SendtoLower(char*pBuffer,int length);

extern void ip_SendtoUp(char *pBuffer,int length);

extern unsigned int getIpv4Address();

// implemented by students
typedef struct _ipv4_message{
  uint8_t fb;                       //first byte,version and ihl
  uint8_t tos;                      //type of service
  uint16_t total_length;
  uint16_t id;                      //identification
  uint16_t fragment;                //flasg and offset
  uint8_t ttl;                      //time to live
  uint8_t protocol;
  uint16_t checksum;
  uint32_t src_addr;
  uint32_t des_addr;
}ipv4_message;

uint16_t calc_checksum(char *pBuffer, unsigned short length)
{
  uint32_t cksum = 0;
  uint16_t *p = (uint16_t*)pBuffer;
  for(int i = 0; i < length; i += 2){
    cksum += *p++;
  }
  while(cksum >> 16){
    cksum = (cksum >> 16) + (cksum & 0xffff);
  }
  return ~cksum;
}

int stud_ip_recv(char *pBuffer,unsigned short length)
{
  //检查校验和
  if(calc_checksum(pBuffer, HEADER_LEN)){
    ip_DiscardPkt(pBuffer, STUD_IP_TEST_CHECKSUM_ERROR);return 1;
  }
  //检查TTL
  if(!((ipv4_message*)pBuffer)->ttl){
    ip_DiscardPkt(pBuffer, STUD_IP_TEST_TTL_ERROR);return 1;
  }
  //检查IP版本号
  if(get_ip_version(*pBuffer) != 4){
    ip_DiscardPkt(pBuffer, STUD_IP_TEST_VERSION_ERROR);return 1;
  }
  //检查头部长度
  if(get_ihl(*pBuffer) != length){
    ip_DiscardPkt(pBuffer, STUD_IP_TEST_HEADLEN_ERROR);return 1;
  }
  //检查目的地址
  uint32_t des_addr = getIpv4Address();
  if(((ipv4_message*)pBuffer)->des_addr != conv_to_net_order(des_addr)){
    ip_DiscardPkt(pBuffer, STUD_IP_TEST_DESTINATION_ERROR);return 1;
  }
  ip_SendtoUp(pBuffer, length);
	return 0;
}

int stud_ip_Upsend(char *pBuffer,unsigned short len,unsigned int srcAddr,
				   unsigned int dstAddr,byte protocol,byte ttl)
{
  char *ipmsg = new char[len + HEADER_LEN];
  memset(ipmsg, 0, len + HEADER_LEN);
  set_ip_version(((ipv4_message*)ipmsg)->fb, 4);
  set_ihl(((ipv4_message*)ipmsg)->fb, 5);
  ((ipv4_message*)ipmsg)->total_length = conv_to_net_order(len + HEADER_LEN) >> 16;
  ((ipv4_message*)ipmsg)->id           = 0xabab;
  ((ipv4_message*)ipmsg)->ttl          = ttl;
  ((ipv4_message*)ipmsg)->protocol     = protocol;
  ((ipv4_message*)ipmsg)->src_addr     = conv_to_net_order(srcAddr);
  ((ipv4_message*)ipmsg)->des_addr     = conv_to_net_order(dstAddr);
  ((ipv4_message*)ipmsg)->checksum     = calc_checksum(ipmsg, HEADER_LEN);
  memcpy(ipmsg + HEADER_LEN, pBuffer, len);
  ip_SendtoLower(ipmsg, len + HEADER_LEN);
	return 0;
}