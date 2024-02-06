## Install Dependencies

Install 

```sh
sudo apt install make cmake clang-12 llvm-12 pkg-config libelf-dev binutils-dev libcap-dev g++
```

Set clang-12 and clang++-12  to be the default clang
```
sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-12 100
sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-12 100
```


Install `bpftrace` on Ubuntu:

```sh
sudo apt install bpftrace
```

# Hello World for `bpftrace`: 

```sh
sudo bpftrace -e 'BEGIN { printf("Hello eBPF!\n"); }'
```

```sh
sudo bpftrace --unsafe -e 'BEGIN {system("echo \"hello\"");}'
```

```sh
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("Hi! %s %s\n", comm, str(args->filename)) }'
```


Cheat Sheet: https://www.brendangregg.com/BPF/bpftrace-cheat-sheet.html

List all tracepoints: 

```sh
sudo bpftrace -l
sudo bpftrace -lv 'tracepoint:*enter_read' 
```
