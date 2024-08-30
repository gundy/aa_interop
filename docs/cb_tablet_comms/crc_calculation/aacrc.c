#include<stdio.h>
#include<string.h>
#include<stdint.h>

uint8_t AACRC8(const uint8_t *data, int length) 
{
   uint8_t crc = 0x00;

   for(int i=0; i<length; i++)
   {
      crc ^= *data++; 
      for (int j=0; j<8; j++) {
          if ((crc & 0x01) > 0) {
              crc = (crc >> 1) ^ 0xB2;
          } else {
              crc >>= 1;
          }
      }
   }
   return crc ^ 0xff;
}

int main(int argc, char** argv) {
    if (argc == 0) {
        printf("Usage: crc <string>");
    } else {
        printf("aacrc8(\"%s\") = %02X\n", argv[1], CRC8((uint8_t*)argv[1], strlen(argv[1])));
    }
}

