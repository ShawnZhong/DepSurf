#include <fcntl.h>
#include <unistd.h>
#include <linux/if_link.h>
#include <net/if.h>

#include <stdexcept>
#include <thread>
#include <string_view>

#include "ebpf.skel.h"

class BPF {
 public:
  BPF() {
    libbpf_set_print(
        [](enum libbpf_print_level level, const char *format, va_list args) {
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

    const char *sec_name = bpf_program__section_name(skel->progs.prog);
    if (std::string_view(sec_name) == "xdp") {
      int ifindex = if_nametoindex("eth0");
      if (bpf_program__attach_xdp(skel->progs.prog, ifindex) == nullptr)
        throw std::runtime_error("Failed to attach XDP program");
    } else {
      if (ebpf_bpf__attach(skel))
        throw std::runtime_error("Failed to attach BPF skeleton");
    }
  }

  ~BPF() { ebpf_bpf__destroy(skel); }

  struct ebpf_bpf *skel;
};

extern "C" __attribute__((noinline)) int uprobed_sub(int a, int b) {
  asm volatile("");
  return a - b;
}

void print_output() {
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

  std::thread t(print_output);

  for (int i = 0;; i++) {
    uprobed_sub(i * i, i);
    sleep(1);
  }
}
