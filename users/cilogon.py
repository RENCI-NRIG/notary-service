# ref: https://github.com/UoM-ResPlat-DevOps/cilogon-hpc-integration-demo
import os
import subprocess
# from pprint import pprint
from typing import Optional
from uuid import uuid4

import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization.pkcs12 import serialize_key_and_certificates
from cryptography.x509.oid import NameOID
from django.http import HttpResponse, Http404
from requests_oauthlib import OAuth2Session

from base.settings import MEDIA_ROOT
from users.models import CilogonCertificate

client_id = os.getenv('OIDC_RP_CLIENT_ID', None)
client_secret = os.getenv('OIDC_RP_CLIENT_SECRET', None)
redirect_uri = os.getenv('OIDC_RP_CALLBACK', None)
scope = ['openid', 'email', 'profile', 'org.cilogon.userinfo', 'edu.uiuc.ncsa.myproxy.getcert']
auth_url = 'https://cilogon.org/authorize'


def x509_generate_private_key() -> rsa.RSAPrivateKey:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    return private_key


def x509_generate_csr(private_key: rsa.RSAPrivateKey) -> x509.CertificateSigningRequest:
    builder = x509.CertificateSigningRequestBuilder()
    builder = builder.subject_name(
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u'ignore'),
                   ]))
    csr = builder.sign(
        private_key,
        hashes.SHA256()
    )

    return csr


def x509_generate_p12(cilogon_cert: CilogonCertificate, p12_password: str) -> bytes:
    private_key = serialization.load_pem_private_key(
        data=str.encode(cilogon_cert.privkey),
        password=None,
        backend=default_backend())

    public_key = x509.load_pem_x509_certificate(data=str.encode(cilogon_cert.pubkey), backend=default_backend())

    p12 = serialize_key_and_certificates(
        name=b'cilogon.p12',
        key=private_key,
        cert=public_key,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(str.encode(p12_password))
    )

    return p12


def x509_generate_cilogon_certificate(cilogon_access_token: str, p12_password: str) -> Optional[CilogonCertificate]:
    response = None
    # generate private key
    private_key = x509_generate_private_key()
    # pprint(private_key.private_bytes(
    #     encoding=serialization.Encoding.PEM,
    #     format=serialization.PrivateFormat.TraditionalOpenSSL,
    #     encryption_algorithm=serialization.NoEncryption()
    # ).decode('UTF-8'))
    # generate csr
    csr = x509_generate_csr(private_key=private_key)
    # pprint(csr.public_bytes(
    #     encoding=serialization.Encoding.PEM
    # ).decode('UTF-8'))
    csr_str = str(csr.public_bytes(encoding=serialization.Encoding.PEM), 'utf-8').lstrip(
        '-----BEGIN CERTIFICATE REQUEST-----\n').rstrip('-----END CERTIFICATE REQUEST-----\n')
    csr_str = csr_str.replace('\n', '')
    # request new certificate
    s = requests.Session()
    s.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    s.params = {
        'access_token': cilogon_access_token,
        'client_id': os.getenv('OIDC_RP_CLIENT_ID'),
        'client_secret': os.getenv('OIDC_RP_CLIENT_SECRET'),
        'certreq': csr_str
    }
    public_key = s.get(
        url='https://cilogon.org/oauth2/getcert'
    )
    # pprint(public_key.content.decode('UTF-8'))
    s.close()

    # save certificate
    if public_key.status_code == 200:
        cilogon_cert = CilogonCertificate()
        cilogon_cert.uuid = uuid4()
        cilogon_cert.pubkey = public_key.content.decode('UTF-8')
        cilogon_cert.privkey = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('UTF-8')
        cilogon_cert.csr = csr.public_bytes(
            encoding=serialization.Encoding.PEM
        ).decode('UTF-8')
        cilogon_cert.save()
        try:
            cilogon_cert.p12 = x509_generate_p12(cilogon_cert=cilogon_cert, p12_password=p12_password)
            cilogon_cert.save()
            # pprint(cilogon_cert.p12)
        except Exception as e:
            cilogon_cert.delete()
            raise Exception('"key values mismatch"\r\n {0}\r\n ' +
                            'This can occur if trying to generate a certificate more than once per session ...'.format(
                                e))

        response = cilogon_cert
    else:
        raise Exception('{0}\r\nReset your "oidc_access_code" by logging out and sign-in again'.format(
            public_key.content.decode('UTF-8')))

    return response


def user_cilogon_certificates_directory_path(instance):
    """
    Return full path to filename based on User UUID value
    :param instance:
    :param filename:
    :return:
    """
    # file will be uploaded to MEDIA_ROOT/cilogon_certificates/user_<uuid>/<filename>
    return os.path.join(MEDIA_ROOT, 'cilogon_certificates/user_{0}'.format(instance.uuid))


def get_authorization_url():
    """
    return Authorization URL for CILogon
    :return:
    """
    oauth = OAuth2Session(
        client_id,
        redirect_uri=redirect_uri,
        scope=scope
    )
    authorization_url, state = oauth.authorization_url(
        auth_url
    )
    oauth.close()
    return authorization_url


def get_csr():
    """
    Create certificate signing request (CSR) that is accepted by CILogon
    """

    # Generate private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Generate a CSR and sign it. Subject doesn't matter, will be replaced by CILogon service.
    csr = x509.CertificateSigningRequestBuilder() \
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, u"AU"), ])) \
        .sign(key, hashes.SHA256(), default_backend()) \
        .public_bytes(serialization.Encoding.PEM)

    # CILogon wants clean request, with no header/footer or newlines.
    csr = str(csr, 'utf-8').lstrip('-----BEGIN CERTIFICATE REQUEST-----\n').rstrip(
        '-----END CERTIFICATE REQUEST-----\n')
    csr = csr.replace('\n', '')

    # Return plain text key
    key = key.private_bytes(encoding=serialization.Encoding.PEM,
                            format=serialization.PrivateFormat.TraditionalOpenSSL,
                            encryption_algorithm=serialization.NoEncryption())
    return key, csr


def generate_cilogon_certificates(user, authorization_response, p12_password):
    """
    Generate CILogon certificate pair and pcks12 file
    :param user:
    :param authorization_response:
    :param p12_password:
    :return:
    """
    oauth = OAuth2Session(
        client_id,
        redirect_uri=redirect_uri,
        scope=scope
    )
    token = oauth.fetch_token(
        'https://cilogon.org/oauth2/token',
        client_secret=client_secret,
        code=authorization_response,
    )
    key, csr = get_csr()
    cilogon_cert = oauth.post(
        'https://cilogon.org/oauth2/getcert',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        params={
            'access_token': token,
            'client_id': client_id,
            'client_secret': client_secret,
            'certreq': csr
        }
    )
    oauth.close()
    file_path = os.path.dirname(user_cilogon_certificates_directory_path(user, 'cilogon.crt'))
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    open(user_cilogon_certificates_directory_path(user, 'cilogon.crt'), 'wb').write(cilogon_cert.content)
    open(user_cilogon_certificates_directory_path(user, 'cilogon.key'), 'wb').write(key)
    cmd = [
        "openssl",
        "pkcs12",
        "-export",
        "-inkey",
        str(user_cilogon_certificates_directory_path(user, 'cilogon.key')),
        "-in",
        str(user_cilogon_certificates_directory_path(user, 'cilogon.crt')),
        "-password",
        "pass:" + str(p12_password)
    ]
    p12_out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p12_stdout, p12_stderr = p12_out.communicate()
    open(user_cilogon_certificates_directory_path(user, 'cilogon.p12'), 'wb').write(p12_stdout)
    certificate_files = []
    certificate_files.append({"name": "cilogon.crt",
                              "description": "cilogon public certificate file",
                              "path": str(user_cilogon_certificates_directory_path(user, 'cilogon.crt'))})
    certificate_files.append({"name": "cilogon.key",
                              "description": "cilogon private key file",
                              "path": str(user_cilogon_certificates_directory_path(user, 'cilogon.key'))})
    certificate_files.append({"name": "cilogon.p12",
                              "description": "cilogon pcks12 file - for browsers",
                              "path": str(user_cilogon_certificates_directory_path(user, 'cilogon.p12'))})
    return certificate_files


def download(request, path):
    """
    Create download response for requested file
    :param request:
    :param path:
    :return:
    """
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(path)
            return response
    raise Http404
