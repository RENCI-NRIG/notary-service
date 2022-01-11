# SAFE Keys - principal keys for development

[Secure Access For Everyone (SAFE)](https://github.com/RENCI-NRIG/SAFE), is an integrated system for managing trust using a logic-based declarative language. Logical trust systems authorize each request by constructing a proof from a context — a set of authenticated logic statements representing credentials and policies issued by various principals in a networked system.

Development SAFE principal keys for notary service will be generated at: `./safe/keys`

```console
$ ls -alh ./safe/keys
...
-rw-r--r--  1 xxxxx  xxxxx   3.2K Jul 17 12:05 safe-principal.key
-rw-r--r--  1 xxxxx  xxxxx   800B Jul 17 12:05 safe-principal.pub
```

Keys generated from the `safe` directory using openssl:

```
openssl rsa -in ../ssl/privkey.pem \
    -outform pem -pubout \
    -out ./keys/safe-principal.pub
openssl rsa -in ../ssl/privkey.pem \
    -outform pem \
    -out ./keys/safe-principal.key
```
