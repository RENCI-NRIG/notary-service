import logging
from datetime import datetime, timedelta
from typing import Dict

import jwt
from dateutil import tz


class NSJWT:
    """ JWT generation and verification for Notary Service """

    VERSION="1.0"

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.unset = True

    def setToken(self, jwt: str) -> None:
        if not self.unset:
            raise NSJWTError("JWT already initialized")
        self.jwt = jwt
        self.encoded = True
        self.unset = False

    def setClaims(self, *, projectId: str, dataSet: str, nsToken: str, iss: str, nsName: str, sub: str, name: str):
        if not self.unset:
            raise NSJWTError("Token or claims already initialized")

        self.claims = {
            'data-set': dataSet,
            'project-id': projectId,
            'ns-token': nsToken,
            'ns-name': nsName,
            'iss': iss,
            'sub': sub,
            'name': name,
            'ver': self.VERSION
        }
        self.encoded = False
        self.unset = False

    def getClaims(self) -> Dict[str, str]:
        if self.unset:
            raise NSJWTError("Token not initialized")

        if self.claims is not None:
            return self.claims
        else:
            raise NSJWTError("Token not decoded")

    def encode(self, privateKey: str, validity: timedelta) -> str:
        """ sign and base64 encode the token with validity from now until now + timedelta """
        if self.unset:
            raise NSJWTError("Claims not initialized, unable to encode")

        if self.encoded:
            self.log.info("Returning previously encoded token for project %s user %s" % (self.projectId, self.name))
            return self.jwt

        self.claims['iat'] = int(datetime.now().timestamp())
        self.claims['exp'] = int((datetime.now() + validity).timestamp())
        self.jwt = jwt.encode(self.claims, key=privateKey, algorithm='RS256')

        self.encoded = True
        return self.jwt

    def decode(self, publicKey: str, verify: bool = True) -> None:
        """ verify signature and expiration date and decode the token  """
        if self.unset:
            raise NSJWTError("JWT not initilaized, unable to decode")

        if not self.encoded:
            raise NSJWTError("Token already in decoded form")

        if publicKey is None:
            self.log.info("Decoding token without verification of origin or date")
            verify = False

        options = {"verify_signature": verify}

        self.claims = jwt.decode(self.jwt, publicKey, verify=verify, algorithms='RS256', options=options)

        if self.claims['ver'] != self.VERSION:
            raise NSJWTError("Version of encoding {self.claims['ver']} doesn't match the code {self.VERSION}")

    def validUntil(self) -> datetime:
        if self.unset:
            raise NSJWTError("Claims not initialized")

        if 'exp' in self.claims:
            return self.getLocalFromUTC(self.claims['exp'])
        else:
            raise NSJWTError("Expiration claim not present")

    def getLocalFromUTC(self, utc: int) -> datetime:
        """ convert UTC in claims (iat and exp) into a python
        datetime object """
        return datetime.fromtimestamp(utc, tz.tzlocal())

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        if self.unset:
            return "JWT not initialized"

        fstring = f"Token for {self.claims['sub']}/{self.claims['name']}:" + \
                  f"\n\tuser set: {self.claims['data-set']}" + \
                  f"\n\tissued by: {self.claims['iss']}/{self.claims['ns-name']}" + \
                  f"\n\tSAFE token: {self.claims['ns-token']}" + \
                  f"\n\tproject: {self.claims['project-id']}"

        if 'iat' in self.claims:
            fstring += f"\n\tIssued on: {self.getLocalFromUTC(self.claims['iat']).strftime('%Y-%m-%d %H:%M:%S')}"
        if 'exp' in self.claims:
            fstring += f"\n\tExpires on: {self.getLocalFromUTC(self.claims['exp']).strftime('%Y-%m-%d %H:%M:%S')}"

        return fstring


class NSJWTError(Exception):
    pass


def main():
    """ simple test harness """
    tok = NSJWT()
    print(tok)
    tok.setClaims(projectId = "project1", dataSet = "data-set",
                  nsToken = "nstok", iss = "ns-dev.cyberimpact.us",
                  nsName = "NS for ImPACT", sub = "subject", name = "Test Subject")
    print(tok)

    with open('private.pem') as f:
        privKey = f.read()

    encodedTokString = tok.encode(privKey, timedelta(days=1))

    print(encodedTokString)

    tok1 = NSJWT()
    with open('public.pem') as f:
        pubKey = f.read()

    tok1.setToken(encodedTokString)
    tok1.decode(pubKey)
    print(tok1)


if __name__ == "__main__":
    main()
