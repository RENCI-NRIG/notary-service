import jwt
import logging
from datetime import datetime, timedelta
from dateutil import tz

class NSJWT:
    """ JWT generation and verification for Notary Service """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.unset = True

    def setToken(self, jwt: str) -> None:
        if not self.unset:
            raise NSJWTException("JWT already initialized")
        self.jwt = jwt
        self.encoded = True
        self.unset = False

    def setFields(self, projectId: str, userSet: str, nsToken: str, iss: str, nsName: str, sub: str, name: str):
        if not self.unset:
            raise NSJWTException("Token or claims already initialized")

        self.claims = {
            'user-set': userSet,
            'project-id': projectId,
            'ns-token': nsToken,
            'ns-name': nsName,
            'iss': iss,
            'sub': sub,
            'name': name,
        }
        self.encoded = False
        self.unset = False

    def encode(self, privateKey: str, validity: timedelta) -> str:
        """ sign and base64 encode the token with validity from now until now + timedelta """
        if self.unset:
            raise NSJWTException("Claims not initialized, unable to encode")

        if self.encoded:
            self.log.info("Returning previously encoded token for project %s user %s" % (self.projectId, self.name))
            return self.jwt

        self.claims['iat'] = int(datetime.now().timestamp())
        self.claims['exp'] = int((datetime.now() + validity).timestamp())
        self.jwt = str(jwt.encode(self.claims, privateKey, algorithm='RS256'), 'utf-8')

        self.encoded = True
        return self.jwt

    def decode(self, publicKey: str, verify: bool = True) -> None:
        """ verify if key is not None and decode the token  """
        if self.unset:
            raise NSJWTException("JWT not initilaized, unable to decode")

        if not self.encoded:
            raise NSJWTException("Token already in decoded form")

        if publicKey is None:
            self.log.info("Decoding token without verification of origin or date")
            verify = False

        self.claims = jwt.decode(self.jwt, publicKey, verify=verify, algorithms='RS256')

    def validUntil(self) ->datetime:
        if self.unset:
            raise NSJWTException("Claims not initialized")

        if 'exp' in self.claims:
            return self.getLocalFromUTC(self.claims['exp'])
        else:
            raise NSJWTException("Expiration claim not present")

    def getLocalFromUTC(self, utc: int) ->datetime:
        """ convert UTC in claims (iat and exp) into a python
        datetime object """
        return datetime.fromtimestamp(utc, tz.tzlocal())

    def __repr__(self) ->str:
        return self.__str__()

    def __str__(self) -> str:
        if self.unset:
            return "JWT not initialized"

        fstring = f"Token for {self.claims['sub']}/{self.claims['name']}:" +\
            f"\n\tuser set: {self.claims['user-set']}" +\
            f"\n\tissued by: {self.claims['iss']}/{self.claims['ns-name']}" +\
            f"\n\tSAFE token: {self.claims['ns-token']}" +\
            f"\n\tproject: {self.claims['project-id']}"

        if 'iat' in self.claims:
            fstring += f"\n\tIssued on: {self.getLocalFromUTC(self.claims['iat']).strftime('%Y-%m-%d %H:%M:%S')}"
        if 'exp' in self.claims:
            fstring += f"\n\tExpires on: {self.getLocalFromUTC(self.claims['exp']).strftime('%Y-%m-%d %H:%M:%S')}"

        return fstring

class NSJWTException(Exception):
    pass

def main():
    """ simple test harness """
    tok = NSJWT()
    print(tok)
    tok.setFields("project1", "user-set",
        "nstok", "ns-dev.cyberimpact.us",
        "NS for ImPACT", "subject", "Test Subject")
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
