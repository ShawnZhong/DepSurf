#include <fcntl.h>
#include <unistd.h>

int main() {
  int fd = open("1.txt", O_CREAT | O_RDWR, 0644);
  close(fd);
  unlink("1.txt");
  pause();
}
