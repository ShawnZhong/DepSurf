// #define BPF_NO_PRESERVE_ACCESS_INDEX
#include "vmlinux.h"
//

// #include <linux/ptrace.h>
// #include <linux/types.h>
// struct file
// #include <linux/fs.h>

// SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause
/* Copyright (c) 2020 Facebook */

#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>

char LICENSE[] SEC("license") = "Dual BSD/GPL";

SEC("kprobe/vfs_read")
int BPF_KPROBE(vfs_read_entry, struct file *file) {
  struct path path;
  path = BPF_CORE_READ(file, f_path);             // relocation here
  bpf_printk("vfs_read_entry: %p", path.dentry);  // relocation or not?
  return 0;
}
