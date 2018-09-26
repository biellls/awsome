import logging
from io import BytesIO
from typing import Set, Union, List

import boto3


def peel(uri):
    if uri.startswith('s3://'):
        return uri[len('s3://'):]
    elif uri.startswith('file://'):
        return uri[len('file://'):]

    raise ValueError(f'Invalid URI format for {uri}')


# TODO: use urlparse from urllib?
def parse_s3_uri(uri):
    if not uri.startswith('s3://'):
        raise ValueError(f'S3 URI must start with s3://: {uri}')

    peeled_uri = peel(uri)
    bucket = peeled_uri.split('/')[0]
    key = peeled_uri[len(bucket + '/'):]

    return bucket, key


def format_s3_uri(bucket, key):
    if bucket.endswith('/'):
        bucket = bucket[:-1]
    if key.startswith('/'):
        key = key[1:]

    return f's3://{bucket}/{key}'


def uri_type(uri):
    if uri.startswith('s3://'):
        return 's3'
    elif uri.startswith('file://'):
        return 'file'

    raise ValueError(f'Invalid URI format for {uri}')


def key_depth(key):
    if key == '':
        return 0

    if key.endswith('/'):
        key = key[:-1]

    return len(key.split('/'))


def get_prefix(key, depth=-1):
    prefix = '/'.join(key.split('/')[:depth])
    if depth != len(key.split('/')):
        prefix = prefix + '/'
    return prefix


def _make_session():
    return boto3


def ls(uri: str=None, recursive: bool=False, session=None) -> List[str]:
    """
    Treats the uri like a directory and lists the keys and 'directories' inside it.
    If recursive is used it lists all the keys with the same prefix

    :param uri: s3 uri
    :param recursive: List all keys with prefix if True, list 'directory' contents if False
    :param session: boto3 session. Creates default one if None given
    :return: List of keys
    """
    print(f"aws s3 ls {'--recursive ' if recursive else ''}{uri}")

    session = session or _make_session()

    if uri is None:
        s3 = session.resource('s3')
        if recursive:
            raise ValueError('List buckets does not support recursive')
        return [bucket.name for bucket in s3.buckets.all()]

    s3 = session.client('s3')

    bucket, key = parse_s3_uri(uri)

    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=key
    )

    if 'Contents' not in response.keys():
        return []

    keys = [x['Key'] for x in response['Contents']]
    if recursive:
        return keys
    else:
        base_depth = key_depth(key)
        return list(set([get_prefix(x, base_depth + 1) for x in keys]))


def rm_key(bucket, key, session=None):
    print(f"aws s3 rm s3://{bucket}/{key}")

    session = session or _make_session()
    s3 = session.resource('s3')

    s3.Object(bucket, key).delete()


def rm(uri, session=None):
    print(f"aws s3 rm {uri}")

    bucket, key = parse_s3_uri(uri)
    rm_key(bucket, key, session)


def copy_key(from_bucket, from_key, to_bucket, to_key=None, session=None):
    session = session or _make_session()
    s3 = session.resource('s3')

    if to_key is not None and to_key.endswith('/'):
        to_key += from_key.split('/')[-1]

    print(f'aws s3 cp s3://{from_bucket}/{from_key} s3://{to_bucket}/{to_key or from_key}')

    s3.Object(to_bucket, to_key or from_key).copy_from(CopySource=f'{from_bucket}/{from_key}')
    return f'{to_bucket}/{to_key or from_key}'


def download_key(bucket, key, file_path, session=None):
    session = session or _make_session()
    s3 = session.resource('s3')

    s3.Bucket(bucket).download_file(key, file_path)
    return file_path


def read_key(bucket, key, session=None):
    session = session or _make_session()
    s3 = session.resource('s3')

    obj = s3.Object(bucket, key)
    return obj.get()['Body'].read().decode('utf-8')


def upload_file(file_path, bucket, key, encrypt=False, session=None):
    session = session or _make_session()
    s3 = session.client('s3')

    extra_args = {}
    if encrypt:
        extra_args['ServerSideEncryption'] = "AES256"

    s3.upload_file(file_path, bucket, key, ExtraArgs=extra_args)
    return f'{bucket}/{key}'


def upload_string(data: str, bucket, key, encrypt=False, session=None):
    session = session or _make_session()
    s3 = session.client('s3')

    buffer = BytesIO(data.encode('utf-8'))

    extra_args = {}
    if encrypt:
        extra_args['ServerSideEncryption'] = "AES256"

    s3.upload_fileobj(buffer, bucket, key, ExtraArgs=extra_args)


def cp(from_uri, to_uri, session=None):
    # TODO error control for invalid uris
    print(f"aws s3 cp {from_uri} {to_uri}")

    if uri_type(from_uri) == 's3':
        from_bucket, from_key = parse_s3_uri(from_uri)

        if uri_type(to_uri) == 's3':
            to_bucket, to_key = parse_s3_uri(to_uri)
            return copy_key(from_bucket, from_key, to_bucket, to_key, session)
        elif uri_type(to_uri) == 'file':
            return download_key(from_bucket, from_key, file_path=peel(to_uri), session=session)

        assert False
    else:
        if uri_type(to_uri) == 's3':
            to_bucket, to_key = parse_s3_uri(to_uri)
            return upload_file(file_path=peel(from_uri), bucket=to_bucket, key=to_key, session=session)
        else:
            raise ValueError('Cannot copy from local file to local file')


def move_key(from_bucket, from_key, to_bucket, to_key=None, session=None):
    copy_key(from_bucket, from_key, to_bucket, to_key, session)
    rm_key(from_bucket, from_key, session)


def mv(from_uri, to_uri, session=None):
    print(f"aws s3 mv {from_uri} {to_uri}")

    from_bucket, from_key = parse_s3_uri(from_uri)
    to_bucket, to_key = parse_s3_uri(to_uri)

    move_key(from_bucket, from_key, to_bucket, to_key, session)
