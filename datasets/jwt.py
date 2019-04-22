import os
from datetime import timedelta

from ns_jwt import NSJWT


def encode_ns_jwt(project_uuid, user):
    private_key = os.getenv('NS_PRESIDIO_JWT_PRIVATE_KEY', '')
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
    public_key = os.getenv('NS_PRESIDIO_JWT_PUBLIC_KEY', '')
    tok = NSJWT()
    tok.setToken(encoded_jwt)
    tok.decode(public_key)
    jwt_claims = tok.getClaims()
    return jwt_claims
