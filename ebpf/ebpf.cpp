#include <bpf/libbpf.h>
#include <fcntl.h>
#include <sched.h>
#include <unistd.h>

#include <stdexcept>
#include <thread>
#include <vector>

#include "ebpf.skel.h"

class BPF {
 public:
  BPF() {
    libbpf_set_print(
        [](enum libbpf_print_level level, const char *format, va_list args) {
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

  struct ebpf_bpf *skel;
};

extern "C" __attribute__((noinline)) int uprobed_sub(int a, int b) {
  asm volatile("");
  return a - b;
}

void print_output() {
  // open debug file
  int fd = open("/sys/kernel/debug/tracing/trace_pipe", O_RDONLY);
  if (fd < 0) throw std::runtime_error("Failed to open trace_pipe");
  while (1) {
    char buf[4096];
    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    if (n <= 0) break;
    buf[n] = '\0';
    printf("%s", buf);
  }
}

int main() {
  if (getuid() != 0) throw std::runtime_error("Run as root");

  BPF bpf;

  // std::thread t(print_output);

  for (int i = 0;; i++) {
    uprobed_sub(i * i, i);
    sleep(1);
  }
}
