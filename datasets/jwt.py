import os
from datetime import timedelta

from ns_jwt import NSJWT

from safe.post_assertions import get_id_from_pub


def encode_ns_jwt(project_uuid, dataset_scid, user):
    private_key_path = os.getenv('NS_PRESIDIO_JWT_PRIVATE_KEY_PATH', '')
    if not private_key_path:
        private_key_path = os.path.dirname(os.path.dirname(__file__)) + '/ssl/privkey.pem'
    with open(private_key_path) as f:
        private_key = f.read()
    data_set = dataset_scid
    project_id = project_uuid
    ns_token = get_id_from_pub(os.getenv('SAFE_PRINCIPAL_PUBKEY', 'safe/keys/ns.pub'))
    ns_name = os.getenv('NS_NAME', 'localhost')
    iss = os.getenv('NS_NAME', 'localhost')
    sub = user.cert_subject_dn
    name = user.name
    tok = NSJWT()
    tok.setClaims(
        projectId=project_id,
        dataSet=data_set,
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
        public_key_path = os.path.dirname(os.path.dirname(__file__)) + '/ssl/pubkey.pem'
    with open(public_key_path) as f:
        public_key = f.read()
    tok = NSJWT()
    tok.setToken(encoded_jwt)
    tok.decode(public_key)
    jwt_claims = tok.getClaims()
    return jwt_claims
