#!/usr/bin/env python3

from utils import system

system("sudo kill -9 $(ps aux | grep 'qemu' | awk '{print $2}')")
