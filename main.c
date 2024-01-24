/**
; int trace(struct pt_regs *ctx) { // Line  14
   0:   b7 02 00 00 3a 20 25 64 r2 = 1680154682
; ({ char _fmt[] = "close fd: %d"; bpf_trace_printk_(_fmt, sizeof(_fmt), PT_REGS_PARM1(ctx)); }); // Line  16
   1:   63 2a f8 ff 00 00 00 00 *(u32 *)(r10 - 8) = r2
   2:   18 02 00 00 63 6c 6f 73 00 00 00 00 65 20 66 64 r2 = 7234505471517748323 ll
   4:   7b 2a f0 ff 00 00 00 00 *(u64 *)(r10 - 16) = r2
   5:   b7 02 00 00 00 00 00 00 r2 = 0
   6:   73 2a fc ff 00 00 00 00 *(u8 *)(r10 - 4) = r2
   7:   79 13 00 00 00 00 00 00 r3 = *(u64 *)(r1 + 0)
   8:   bf a1 00 00 00 00 00 00 r1 = r10
   9:   07 01 00 00 f0 ff ff ff r1 += -16
  10:   b7 02 00 00 0d 00 00 00 r2 = 13
  11:   85 00 00 00 06 00 00 00 call 6
; return 0; // Line  17
  12:   b7 00 00 00 00 00 00 00 r0 = 0
  13:   95 00 00 00 00 00 00 00 exit
*/

#include <linux/bpf.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>

char prog[] = "\xb7\x02\x00\x00\x3a\x20\x25\x64\x63\x2a\xf8\xff\x00\x00\x00\x00\x18\x02\x00\x00\x63\x6c\x6f\x73\x00\x00\x00\x00\x65\x20\x66\x64\x7b\x2a\xf0\xff\x00\x00\x00\x00\xb7\x02\x00\x00\x00\x00\x00\x00\x73\x2a\xfc\xff\x00\x00\x00\x00\x79\x13\x00\x00\x00\x00\x00\x00\xbf\xa1\x00\x00\x00\x00\x00\x00\x07\x01\x00\x00\xf0\xff\xff\xff\xb7\x02\x00\x00\x0d\x00\x00\x00\x85\x00\x00\x00\x06\x00\x00\x00\xb7\x00\x00\x00\x00\x00\x00\x00\x95\x00\x00\x00\x00\x00\x00\x00";

int main(){
    // call bpf_prog_load
    struct bpf_prog_load_opts opt = {
      .sz = sizeof(prog),

    };
    int prog_fd = bpf_prog_load(BPF_PROG_TYPE_KPROBE, "test", "GPL", prog, sizeof(prog), &opt);
    if (prog_fd < 0) {
        printf("bpf_prog_load failed\n");
        return 1;
    }
    printf("bpf_prog_load succeeded\n");

}
