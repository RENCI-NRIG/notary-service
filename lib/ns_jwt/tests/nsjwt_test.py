import logging
import os
import unittest
from datetime import timedelta

from ns_jwt import NSJWT, NSJWTError

global testdir
testdir = os.path.dirname(os.path.dirname(__file__)) + '/tests/'


class TestNSJWT(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestNSJWT, self).__init__(*args, **kwargs)

        self.log = logging.getLogger(__name__)

    def test_encode_decode(self):
        tok = NSJWT()
        tok.setClaims(projectId = "project1", dataSet = "data-set",
                      nsToken = "nstok", iss = "ns-dev.cyberimpact.us",
                      nsName = "NS for ImPACT", sub = "subject", name = "Test Subject")

        with open(testdir + 'private.pem') as f:
            privKey = f.read()

        encodedTokString = tok.encode(privKey, timedelta(days=1))

        tok1 = NSJWT()
        with open(testdir + 'public.pem') as f:
            pubKey = f.read()

        tok1.setToken(encodedTokString)
        tok1.decode(pubKey)

    def test_exceptions(self):
        tok = NSJWT()

        with self.assertRaises(NSJWTError):
            tok.getClaims()

        tok.setClaims(projectId = "project1", dataSet = "data-set",
                      nsToken = "nstok", iss = "ns-dev.cyberimpact.us",
                      nsName = "NS for ImPACT", sub = "subject", name = "Test Subject")

        with self.assertRaises(NSJWTError):
            tok.decode(None)


if __name__ == '__main__':
    unittest.main()
