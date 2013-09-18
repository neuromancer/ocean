int main(int argc, char **argv) {
  char small [128];
  //if (argc == 1)
  //  return 0;
 
  //printf("%x", (int) *( (int*) argv[1]+10));
  if ((*((int*) argv[1]+10)) == 0x65666768)
   strcpy(argv[1], small);

  printf("%s", small);
  return 0;

}
