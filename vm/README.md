```
sudo apt install qemu-kvm genisoimage
```

Add /etc/fstab entry for 9p mount
```
hostshare   /path/to/mount 9p  trans=virtio,version=9p2000.L   0   0
```

sudo mount -a

awk -F\' '$1=="menuentry " || $1=="submenu " {print i++ " : " $2}; /\tmenuentry / {print "\t" i-1">"j++ " : " $2};' /boot/grub/grub.cfg
sudo grub-reboot "1>2" && sudo reboot
