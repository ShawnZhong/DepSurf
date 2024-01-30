// #define BPF_NO_PRESERVE_ACCESS_INDEX
#include "vmlinux.h"
//

#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>

char LICENSE[] SEC("license") = "Dual BSD/GPL";

SEC("kprobe/vfs_read")
int BPF_KPROBE(vfs_read_entry, struct file* file) {
  struct path path;
  path = BPF_CORE_READ(file, f_path);
  struct dentry* dentry = path.dentry;
  return BPF_CORE_READ(dentry, d_flags);
}
