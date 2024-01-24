#include <bpf/libbpf.h>
#include <fcntl.h>
#include <sched.h>
#include <unistd.h>

#include <stdexcept>
#include <thread>
#include <vector>

#include "ebpf.skel.h"

static int libbpf_print_fn(enum libbpf_print_level level, const char *format,
                           va_list args) {
  return vfprintf(stderr, format, args);
}

class BPF {
 public:
  BPF() {
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

__attribute__((noinline)) extern "C" int uprobed_sub(int a, int b) {
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

extern "C" void run_sub() {
  for (int i = 0;; i++) {
    /* trigger our BPF programs */
    fprintf(stderr, ".");
    // uprobed_add(i, i + 1);
    uprobed_sub(i * i, i);
    sleep(1);
  }
}

int main() {
  if (getuid() != 0) throw std::runtime_error("Run as root");

  /* Set up libbpf errors and debug info callback */
  libbpf_set_print(libbpf_print_fn);

  BPF bpf;

  // create a background thread to print the output
  std::thread t(print_output);
  t.detach();

  run_sub();
}
