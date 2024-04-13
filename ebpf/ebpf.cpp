#include <fcntl.h>
#include <unistd.h>
#include <linux/if_link.h>
#include <net/if.h>

#include <stdexcept>
#include <thread>
#include <string_view>

#include "ebpf.skel.h"

struct BPF {
  BPF() {
    libbpf_set_print(
        [](enum libbpf_print_level level, const char* format, va_list args) {
          switch (level) {
            case LIBBPF_DEBUG:
              fprintf(stderr, "\033[1;30m[DEBUG]\033[0m ");
              break;
            case LIBBPF_INFO:
              fprintf(stderr, "\033[1;32m[INFO] \033[0m ");
              break;
            case LIBBPF_WARN:
              fprintf(stderr, "\033[1;33m[WARN] \033[0m ");
              break;
          }
          return vfprintf(stderr, format, args);
        });

    skel = ebpf_bpf__open();
    if (!skel) throw std::runtime_error("Failed to open BPF skeleton");

    if (ebpf_bpf__load(skel))
      throw std::runtime_error("Failed to load BPF skeleton");

    if (ebpf_bpf__attach(skel))
      throw std::runtime_error("Failed to attach BPF skeleton");
  }

  ~BPF() { ebpf_bpf__destroy(skel); }

  struct ebpf_bpf* skel;
};

extern "C" __attribute__((noinline)) int uprobed_sub(int a, int b) {
  asm volatile("");
  return a - b;
}

void print_trace() {
  int fd = open("/sys/kernel/debug/tracing/trace_pipe", O_RDONLY);
  if (fd < 0) throw std::runtime_error("Failed to open trace_pipe");
  while (1) {
    char buf[4096];
    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    if (n <= 0) break;
    buf[n] = '\0';
    char* curr = buf;
    char* next = strchr(curr, '\n');
    while (next != NULL) {
      *next = '\0';
      printf("\033[1;32m[TRACE]\033[0m %s\n", curr);
      curr = next + 1;
      next = strchr(curr, '\n');
    }
  }
}

void print_ringbuf(struct bpf_map* rb) {
  auto handle_event = [](void* ctx, void* data, size_t data_sz) -> int {
    char* event = (char*)data;
    event[30] = '\0';
    printf("\033[1;32m[EVENT]\033[0m %s\n", event);
  };

  struct ring_buffer* ringbuffer =
      ring_buffer__new(bpf_map__fd(rb), handle_event, NULL, NULL);

  if (!ringbuffer) throw std::runtime_error("Failed to create ring buffer");

  while (1) {
    if (ring_buffer__poll(ringbuffer, 100 /* timeout, ms */) < 0) break;
  }
}

int main() {
  if (getuid() != 0) throw std::runtime_error("Run as root");

  BPF bpf;

  std::thread t1(print_trace);
  t1.detach();

  // std::thread t3([bpf]() { print_ringbuf(bpf.skel->maps.rb); });
  // t3.detach();

  std::thread t2([]() { system("bash"); });
  t2.join();

  // for (int i = 0;; i++) {
  //   uprobed_sub(i * i, i);
  //   sleep(1);
  // }
}
