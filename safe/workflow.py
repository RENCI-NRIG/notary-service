from .post_assertions import mock_get_id_from_pub


def mock_workflow_safe_registration(wf_uuid):
    print('### mock workflow SAFE registration ###')
    wp = mock_get_id_from_pub('ssl/ssl_dev.pubkey')
    uuid = wf_uuid
    wf = str(wp) + ':' + str(uuid)
    return wf


def workflow_safe_registration():
    pass
