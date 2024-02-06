#include "vmlinux.h"

#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>

char LICENSE[] SEC("license") = "GPL";


SEC("kprobe/do_syscall_64")
int BPF_KPROBE(prog, struct pt_regs* regs, int nr){
    bpf_printk("KPROBE ENTRY: syscall nr = %d\n", nr);
    return 0;
}
