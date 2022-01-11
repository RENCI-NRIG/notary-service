import logging
import os

# import fabric-comanage-api package (uses directory for development purposes)
from comanage_api import ComanageApi

# create a new ComanageApi object and set the connection attributes
api = ComanageApi(
    co_api_url=os.getenv('COMANAGE_API_URL'),
    co_api_user=os.getenv('COMANAGE_API_USER'),
    co_api_pass=os.getenv('COMANAGE_API_PASS'),
    co_api_org_id=os.getenv('COMANAGE_API_CO_ID'),
    co_api_org_name=os.getenv('COMANAGE_API_CO_NAME'),
    co_ssh_key_authenticator_id=os.getenv('COMANAGE_API_SSH_KEY_AUTHENTICATOR_ID')
)

logger = logging.getLogger(__name__)
