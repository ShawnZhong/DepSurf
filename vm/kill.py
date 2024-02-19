#!/usr/bin/env python3

from utils.system import system

system("sudo kill -9 $(ps aux | grep 'qemu' | awk '{print $2}')")
