#include <stdio.h>
#include <stdlib.h>
#include <openssl/md5.h>
#include <unistd.h>

int main()
{
        int n;
        MD5_CTX c;
        char buf[512];
        char out[16];
        ssize_t bytes;

        MD5_Init(&c);
        bytes=read(STDIN_FILENO, buf, 512);
        while(bytes > 0)
        {
                MD5_Update(&c, buf, bytes);
                bytes=read(STDIN_FILENO, buf, 512);
        }

        MD5_Final(out, &c);

        for(n=0; n<MD5_DIGEST_LENGTH; n++)
                printf("%02x", out[n]);

        return(0);        
}