# pip install jwcrypto
# ref: https://github.com/latchset/jwcrypto

import json

import requests
from jwcrypto import jwk

jwks_url = "https://127.0.0.1:8443/jwks"
# TEST: using CILogon JWKS endpoint
# jwks_url = "https://cilogon.org/oauth2/certs"

# get keys
jwks = requests.get(jwks_url, verify=False)

if jwks.status_code == 200:
    jwks_keys = json.loads(jwks.content.decode('utf-8'))
    for key in jwks_keys.get('keys'):
        pubkey = jwk.JWK.from_json(json.dumps(key).encode())
        print(pubkey.export_to_pem().decode('utf-8'))
