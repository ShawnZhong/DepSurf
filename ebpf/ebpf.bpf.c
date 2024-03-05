#include "vmlinux.h"

#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>
#include <linux/errno.h>

char LICENSE[] SEC("license") = "GPL";

static __always_inline int strncmp(const char *s1, const char *s2,
                                   unsigned long n) {
  int i;
  for (i = 0; i < n; i++) {
    if (s1[i] != s2[i]) {
      return s1[i] - s2[i];
    }
  }
  return 0;
}

// SEC("lsm/inode_setxattr")
// int prog(struct pt_regs *ctx) {
//   const char *name = (const char *)PT_REGS_PARM2(ctx);

//   char name_buf[32];  // copy name to stack
//   bpf_probe_read_str(name_buf, 32, name);

//   if (strncmp(name_buf, "user.malicious", 14) == 0)
//     return -EACCES;  // reject "user.malicious" xattr
//   return 0;
// }
// setfattr -n user.malicious -v val /tmp/test

// struct {
//   __uint(type, BPF_MAP_TYPE_RINGBUF);
//   __uint(max_entries, 1024);
// } fds SEC(".maps");

// SEC("kprobe/close_fd")
// int prog(struct pt_regs *ctx) {
//   int fd = PT_REGS_PARM1(ctx);  // get the 1st arg
//   bpf_ringbuf_output(&fds, &fd, sizeof(fd), 0);
//   return 0;  // not used
// }

// struct {
//   __uint(type, BPF_MAP_TYPE_RINGBUF);
//   __uint(max_entries, 1024);
// } rb SEC(".maps");

// SEC("kprobe/vfs_statx")
// int prog(struct pt_regs *ctx) {
//   struct filename *fnp = (void *)PT_REGS_PARM2(ctx);  // get the 1st arg
//   char *filename = BPF_CORE_READ(fnp, name);

//   char buf[32] = {'h', 'e', 'l'};
//   //   bpf_probe_read_str(buf, sizeof(buf), filename);
//   bpf_ringbuf_output(&rb, &buf, 32, 0);
//   return 0;  // not used
// }

SEC("kprobe/do_execveat_common")
int prog(struct pt_regs *ctx) {
  // unsigned long arg1 = ctx->di;
  unsigned long arg1 = PT_REGS_PARM2(ctx);
  struct filename *f = (void *)arg1;
  const char *str;
  bpf_probe_read(&str, sizeof(str), &f->name);
  bpf_printk("execve: %s", name);
}
