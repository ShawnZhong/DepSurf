#include <unistd.h>
#include <stdio.h>
#include <fcntl.h>
#include <dirent.h>
#include <stdlib.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <string.h>
#include <errno.h>
#include <sys/sysmacros.h>

#define PANIC(msg) \
  do {             \
    perror(msg);   \
    exit(1);       \
  } while (0)

#define DEBUGFS "/debug"

void list_dir(const char *path, int max_depth) {
  if (max_depth == 0) return;

  DIR *dir = opendir(path);
  if (dir == NULL) PANIC("opendir");

  struct dirent *entry;
  while ((entry = readdir(dir)) != NULL) {
    if (entry->d_type == DT_DIR) {
      if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
        continue;
      }

      char new_path[4096];
      snprintf(new_path, sizeof(new_path), "%s/%s", path, entry->d_name);
      printf("%s\n", new_path);
      list_dir(new_path, max_depth - 1);
    }
  }

  closedir(dir);
}

void print_file(const char *path) {
  FILE *fp = fopen(path, "r");
  if (fp == NULL) PANIC("fopen");

  char buf[4096];
  while (fgets(buf, sizeof(buf), fp) != NULL) {
    printf("%s", buf);
  }
  fclose(fp);
}

void mount_fs(const char *fs, const char *path) {
  if (mkdir(path, 0755) == -1 && errno != EEXIST) PANIC("mkdir");
  if (mount(NULL, path, fs, 0, NULL) == -1) PANIC("mount");
}

int main() {
  mount_fs("devtmpfs", "/dev");
  // mknod -m 640 /dev/kmem c 1 2

  // mount_fs("debugfs", DEBUGFS);
  // print_file(DEBUGFS "/tracing/available_events");
  list_dir("/", -1);
  pause();
}
