.DEFAULT_GOAL := ebpf
.PHONY: config all clean ebpf

config:
	cmake -B build -S . -DCMAKE_BUILD_TYPE=Release

all: config
	cmake --build build 

ebpf: config
	cmake --build build --target ebpf
	sudo ./build/ebpf

clean:
	rm -rf build
