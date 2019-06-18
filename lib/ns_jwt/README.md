## `ns_jwt`: JSON Web Tokens for Notary Service

We will use RS256 (public/private key) variant of JWT signing. (Source: [https://pyjwt.readthedocs.io/en/latest/usage.html#encoding-decoding-tokens-with-rs256-rsa](https://pyjwt.readthedocs.io/en/latest/usage.html#encoding-decoding-tokens-with-rs256-rsa)). For signing, , NS is assumed to be in possession of a public-private keypair. Presidio can access the public key through static configuration or, possibly, by querying an endpoint on NS, that is specified in the token.

NS tokens carry the following claims:

| name | description | type |
| --- | --- | --- |
|data-set | SAFE Token that points to the dataset. Presidio is able to synthesize a token with linked assertions based on data-set, project-id and user id | String, Private |
| project-id | CoManage/NS name of the project, universally unique and distinct. | String, Private |
| ns-token | SAFE Token of the NS generated from its public key | String, Private |
| ns-name | Human-readable NS name | String, Private |
| iss | NS FQDN | String, Registered |
| sub | OSF DCE rendering of DN attributes from user’s X.509 cert | String, Public |
| exp | Expiration date | Date, Registered |
| iat | Issued at date | Date, Registered |
| name | Full name of subject | String, Public |

For dates, a JSON numeric value representing the number of seconds from `1970-01-01T00:00:00Z UTC` until the specified UTC date/time, ignoring leap seconds.  This is equivalent to the IEEE Std 1003.1, 2013 Edition definition "Seconds Since the Epoch", in which each day is accounted for by exactly 86400 seconds, other than that non-integer values can be represented.  See RFC 3339 for details regarding date/times in general and UTC in particular.

### Setup and configuration

No external configuration except for dependencies (PyJWT, cryptography, python-dateutil).

As above, use a virtual environment

```
virtualenv -p $(which python3) venv
source venv/bin/activate
pip install --editable ns_jwt
pip install pytest
```

### Testing

Simply execute the command below. The test relies on having `public.pem` and `private.pem` (public and private portions of an RSA key) to be present in the `tests/` directory. You can generate new pairs using `tests/gen-keypair.sh` (relies on openssl installation).

```
pytest -v ns_jwt
```

### Teardown and Cleanup

None needed.

### Troubleshooting

CI Logon or other JWTs may not decode outright using PyJWT due to `binascii.Error: Incorrect padding` and `jwt.exceptions.DecodeError: Invalid crypto padding`. This is due to lack of base64 padding at the end of the token. Read it in as a string, then add the padding prior to decoding:

```
import jwt

with open('token_file.jwt') as f:
  token_string = f.read()

jwt.decode(token_string + "==", verify=False)
```
Any number of `=` can be added (at least 2) to fix the padding. If token is read in as a byte string, convert to `utf-8` first: `jwt_str = str(jwt_bin, 'utf-8')`, then add padding (Source: https://gist.github.com/perrygeo/ee7c65bb1541ff6ac770)
