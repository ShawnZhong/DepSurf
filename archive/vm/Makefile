.PHONY: run clean 

run: init.cpio
	qemu-system-aarch64 \
		-machine virt \
		-bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd \
		-cpu cortex-a53 \
		-m 256M \
		-kernel vmlinuz-5.4.0-26-generic \
		-initrd $< \
		-nographic \
		-append "nokaslr"

init: init.c
	gcc -Wall -Werror -static -o $@ $< 

init.cpio: init
	echo $< | cpio -o -H newc > $@

kill: 
	sudo kill -9 $(ps aux | grep 'qemu' | awk '{print $2}')

clean:
	rm -f init init.cpio
