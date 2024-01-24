## Install Dependencies

Install 

```sh
sudo apt install -y make cmake clang llvm libelf-dev linux-tools-$(uname -r)
```

Install `bpftrace` on Ubuntu:

```sh
sudo apt install bpftrace
```


<details>
<summary>Install `bpftrace-dbgsym` on Ubuntu:</summary>

Add debug symbol packages:

https://wiki.ubuntu.com/Debug%20Symbol%20Packages

```sh
echo "deb http://ddebs.ubuntu.com $(lsb_release -cs) main restricted universe multiverse
deb http://ddebs.ubuntu.com $(lsb_release -cs)-updates main restricted universe multiverse
deb http://ddebs.ubuntu.com $(lsb_release -cs)-proposed main restricted universe multiverse" | \
sudo tee -a /etc/apt/sources.list.d/ddebs.list

sudo apt install ubuntu-dbgsym-keyring

sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F2EDC64DC5AEE1F6B9C621F0C8CAB6595FDFF622

sudo apt-get update

sudo apt install bpftrace-dbgsym
```
</details>

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
