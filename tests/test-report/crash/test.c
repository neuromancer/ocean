int main(int argc, char **argv) {
 
 //for (;;) ;

 int len = 0;
 int i = 0;
 char buf[128];

 if (argc > 1) {
   len = strlen(argv[1]);
   
   for (i=0; i < len-2; i++) {
     if (!strncmp(argv[1]+i,argv[1]+i+2,2)) {
      printf("%s","Bad!\n");
      strcpy(buf,argv[1]);  
     }

   }
  

  printf("%s\n", argv[1]);
 }

 return 0;
}
