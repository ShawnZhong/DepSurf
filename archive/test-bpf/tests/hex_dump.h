#include <cstdint>
#include <cstdio>

void hexdump(const void* data, size_t size) {
  const auto* p = (const uint8_t*)data;
  for (size_t i = 0; i < size; i++) {
    if (i % 32 == 0) printf("%04zx: ", i);
    printf("%02x", p[i]);
    if (i % 4 == 3) printf(" ");
    if (i % 32 == 31) printf("\n");
  }
}
