struct S {
  int (*f)();
};

int bar(struct S* s) { s->f(); }

void foo();
int baz() { foo(); }
