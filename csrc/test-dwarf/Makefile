.PHONY: all clean dwarf

all: dwarf

main:
	gcc -g -gdwarf-5 -O2 -c main.c -o main.o

clean:
	rm -f main.o

dwarf: main
	llvm-dwarfdump main.o 
