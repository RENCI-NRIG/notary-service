import os
from datetime import timedelta

from ns_jwt import NSJWT


def encode_ns_jwt(project_uuid, user):
    private_key_path = os.getenv('NS_PRESIDIO_JWT_PRIVATE_KEY_PATH', '')
    if not private_key_path:
        private_key_path = os.path.dirname(os.path.dirname(__file__)) + '/ssl/ssl_dev.key'
    with open(private_key_path) as f:
        private_key = f.read()
    user_set = "USER_WORKFLOW_COMPLETION_SAFE_TOKEN"
    project_id = project_uuid
    ns_token = "SAFE_HASH"
    ns_name = os.getenv('NS_NAME', 'localhost')
    iss = os.getenv('NS_NAME', 'localhost')
    sub = user.cert_subject_dn
    name = user.name
    tok = NSJWT()
    tok.setClaims(
        projectId=project_id,
        userSet=user_set,
        nsToken=ns_token,
        iss=iss,
        nsName=ns_name,
        sub=sub,
        name=name
    )

    encoded_str = tok.encode(private_key, timedelta(days=1))
    return encoded_str


def decode_ns_jwt(encoded_jwt):
    public_key_path = os.getenv('NS_PRESIDIO_JWT_PUBLIC_KEY_PATH', '')
    if not public_key_path:
        public_key_path = os.path.dirname(os.path.dirname(__file__)) + '/ssl/ssl_dev.pubkey'
    with open(public_key_path) as f:
        public_key = f.read()
    tok = NSJWT()
    tok.setToken(encoded_jwt)
    tok.decode(public_key)
    jwt_claims = tok.getClaims()
    return jwt_claims
