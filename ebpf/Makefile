all:
	cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
	cmake --build build 

clean:
	rm -rf build

main:
	cmake --build build --target main
	./build/main

ebpf:
	cmake --build build --target ebpf
	sudo ./build/ebpf
