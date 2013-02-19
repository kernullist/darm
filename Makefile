CC = gcc
CFLAGS = -std=c99 -Wall -O2 -s

SRC = $(wildcard *.c)
OBJ = $(SRC:.c=.o)

GENCODEC = armv7-tbl.c
GENCODEH = armv7-tbl.h

STUFF = $(GENCODEC) $(GENCODEH) $(OBJ) tests\tests.exe

default: $(STUFF)

$(GENCODEC):
	python darmgen.py $@

$(GENCODEH):
	python darmgen.py $@

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $^

%.exe: %.c $(OBJ) $(GENCODEO)
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm $(STUFF)