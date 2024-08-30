#include<stdio.h>
#include<string.h>
#include<stdint.h>

/**
 * Scan through CRC8 polynomials to find a fit for a collection of AA CAN2 messages with known CRCs.
 */

uint8_t CRC8(const uint8_t *data, int length, const uint8_t polynomial, const uint8_t final_xor) 
{
   uint8_t crc = 0x00;

   for(int i=0; i<length; i++)
   {
      crc ^= *data++; 
      for (int j=0; j<8; j++) {
          if ((crc & 0x01) > 0) {
              crc = (crc >> 1) ^ polynomial;
          } else {
              crc >>= 1;
          }
      }
   }
   return crc ^ final_xor;
}

int main(int argc, char** argv) {
    const char* messages[5] = { "Ping", "ackCAN 1", "setCAN ", "getSystemData", "CAN2 in use"};
    const uint8_t expected_results[5] = { 0xdb, 0xaa, 0xb2, 0x15, 0x95};

    for (uint16_t poly = 0x00; poly < 0xff; poly++) {
        for (uint16_t x = 0x00; x <= 0x01; x++) {
            const uint8_t xor = x ? 0xff : 0x00;
            
            int polyFitsAll = 1;
            for (int i = 0; i < 5; i++) {
                uint8_t calculated_crc = CRC8((uint8_t*)messages[i], strlen(messages[i]), (uint8_t)poly, xor);
                uint8_t expected_crc = expected_results[i];
                if (calculated_crc != expected_crc) {
                    polyFitsAll = 0;
                }
            }
            if (polyFitsAll) {
                printf("Found poly! Poly=0x%02x xor=0x%02x\n", poly, xor);
                return 0;
            }
        }
    }

    printf("Poly not found\n");
    return -1;
}

