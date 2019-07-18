"""
SAFE post assertions
"""

# mock SAFE calls

import base64
import hashlib
import os

import requests
from Crypto.PublicKey import RSA


def mock_get_id_from_pub(public_key):
    """
    getIdFromPub("$KD/strong-1.pub")
    as WP, DSO, NSV
    :param public_key:
    :return:
    """
    with open(public_key, 'r') as pubkey:
        r = RSA.import_key(pubkey.read(), passphrase='')
    s = hashlib.sha256()
    s.update(r.exportKey(format='DER'))
    encoded = base64.urlsafe_b64encode(s.digest())

    return encoded.decode('utf-8')


# end mock SAFE calls


def get_id_from_pub(public_key):
    """
    getIdFromPub("$KD/strong-1.pub")
    as WP, DSO, NSV
    :param public_key:
    :return:
    """
    with open(public_key, 'r') as pubkey:
        r = RSA.import_key(pubkey.read(), passphrase='')
    s = hashlib.sha256()
    s.update(r.exportKey(format='DER'))
    encoded = base64.urlsafe_b64encode(s.digest())

    return encoded.decode('utf-8')


def post_raw_idset(principal):
    """
    postRawIdSet("strong-2")
    as WP, DSO, NSV
    :param principal:
    :return:
    """
    url = 'http://' + str(os.getenv('SAFE_SERVER', 'safe')) \
          + ':' + str(os.getenv('SAFE_SERVER_PORT', '7777')) + '/postRawIdSet'
    payload = '{ "principal": "' + principal + '", "methodParams": [ "' + principal + '" ] }'
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    req = requests.post(url, data=payload, headers=headers)
    status_code = req.status_code
    req.close()
    return status_code


def post_per_flow_rule(workflow):
    """
    postPerFlowRule($WF1)
    :param workflow:
    :return:
    """
    pass


def post_two_flow_data_owner_policy(dataset, workflow_1, workflow_2):
    """
    postTwoFlowDataOwnerPolicy($DataSet, $WF1, $WF2)
    as DSO
    :param dataset:
    :param workflow_1:
    :param workflow_2:
    :return:
    """
    pass


def post_common_completion_receipt(principal, project, workflow):
    """
    postCommonCompletionReceipt("someProject", $WF1)
    as NSV
    :param project:
    :param workflow:
    :return:
    """
    url = 'http://' + str(os.getenv('SAFE_SERVER', 'safe')) \
          + ':' + str(os.getenv('SAFE_SERVER_PORT', '7777')) + '/postCommonCompletionReceipt'
    payload = '{ "principal": "' + principal + '", "methodParams": [ "' + project + '", "' + workflow + '" ] }'
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    req = requests.post(url, data=payload, headers=headers)
    status_code = req.status_code
    req.close()
    return status_code


def post_user_completion_receipt(principal, user, project, workflow):
    """
    postUserCompletionReceipt("someUser", "someProject", $WF1)
    as NSV
    :param user:
    :param project:
    :param workflow:
    :return:
    """
    url = 'http://' + str(os.getenv('SAFE_SERVER', 'safe')) \
          + ':' + str(os.getenv('SAFE_SERVER_PORT', '7777')) + '/postUserCompletionReceipt'
    payload = '{ "principal": "' + principal + '", "methodParams": [ "' + user + '", "' \
              + project + '", "' + workflow + '" ] }'
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    req = requests.post(url, data=payload, headers=headers)
    status_code = req.status_code
    req.close()
    return status_code


def post_link_receipt_for_dataset(principal, user, project, dataset, workflow):
    """
    postLinkReceiptForDataset("someUser", "someProject", $DataSet, $WF1)
    as NSV
    :param user:
    :param project:
    :param dataset:
    :param workflow:
    :return:
    """
    url = 'http://' + str(os.getenv('SAFE_SERVER', 'safe')) \
          + ':' + str(os.getenv('SAFE_SERVER_PORT', '7777')) + '/postLinkReceiptForDataset'
    payload = '{ "principal": "' + principal + '", "methodParams": [ "' + user + '", "' \
              + project + '", "' + dataset + '", "' + workflow + '" ] }'
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    req = requests.post(url, data=payload, headers=headers)
    status_code = req.status_code
    req.close()
    return status_code
