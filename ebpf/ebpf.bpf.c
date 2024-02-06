#include "vmlinux.h"

#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>
#include <linux/errno.h>

char LICENSE[] SEC("license") = "GPL";

static __always_inline int strncmp(const char *s1, const char *s2, unsigned long n) {
    int i;
    for (i = 0; i < n; i++) {
        if (s1[i] != s2[i]) {
            return s1[i] - s2[i];
        }
    }
    return 0;

}

SEC("lsm/inode_setxattr")
int BPF_PROG(prog, struct dentry *dentry, const char *name) {
    bpf_printk("inode_setxattr: %s", name);

    // copy name to stack
    char name_buf[32];
    bpf_probe_read_str(name_buf, sizeof(name_buf), name);

    // reject "user.malicious" xattr
    if (strncmp(name_buf, "user.malicious", 14) == 0) {
        bpf_printk("reject user.malicious");
        return -EACCES;
    }
    return 0;
}

// setfattr -n user.malicious -v val /tmp/test
