#!/bin/bash

KEYLENGTH=2048
pubprivfile=combined.pem
pubfile=public.pem
keyfile=private.pem

# generate combined private+public key
openssl genpkey -algorithm rsa -pkeyopt rsa_keygen_bits:${KEYLENGTH} -outform pem -out ${pubprivfile} >& /dev/null 

# split up into private and public keys
openssl rsa -in ${pubprivfile} -outform PEM -pubout -out ${pubfile} >& /dev/null
openssl rsa -in ${pubprivfile} -outform PEM -out ${keyfile} >& /dev/null
