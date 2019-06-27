from .post_assertions import mock_get_id_from_pub


def mock_dataset_safe_registration(ds_uuid):
    print('### mock dataset SAFE registration ###')
    dso = mock_get_id_from_pub('ssl/ssl_dev.pubkey')
    uuid = ds_uuid
    dataset = str(dso) + ':' + str(uuid)
    return dataset


def dataset_safe_registration():
    return '$DSO:$UUID'
