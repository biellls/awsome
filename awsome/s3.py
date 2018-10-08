from io import BytesIO
from typing import List

import boto3

from awsome import log
from awsome.uris import peel, parse_s3_uri, uri_type, format_s3_uri


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
    log.ls(uri, recursive, session)

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
    log.rm_key(bucket, key, session)

    session = session or _make_session()
    s3 = session.resource('s3')

    s3.Object(bucket, key).delete()

    return format_s3_uri(bucket, key)


def rm(uri, session=None):
    bucket, key = parse_s3_uri(uri)
    removed = rm_key(bucket, key, session)

    return removed


def copy_key(from_bucket, from_key, to_bucket, to_key=None, session=None):
    session = session or _make_session()
    s3 = session.resource('s3')

    if to_key is None:
        to_key = from_key
    elif to_key.endswith('/'):
        to_key += from_key.split('/')[-1]

    log.copy_key(from_bucket, from_key, to_bucket, to_key, session)

    s3.Object(to_bucket, to_key).copy_from(CopySource=f'{from_bucket}/{from_key}')
    return format_s3_uri(to_bucket, to_key)


def download_key(bucket, key, file_path, session=None):
    log.download_key(bucket, key, file_path, session)

    session = session or _make_session()
    s3 = session.resource('s3')

    s3.Bucket(bucket).download_file(key, file_path)
    return file_path


def read_key(bucket, key, session=None):
    log.read_key(bucket, key, session)

    session = session or _make_session()
    s3 = session.resource('s3')

    obj = s3.Object(bucket, key)
    return obj.get()['Body'].read().decode('utf-8')


def upload_file(file_path, bucket, key, encrypt=False, session=None):
    log.upload_file(file_path, bucket, key, encrypt, session)

    session = session or _make_session()
    s3 = session.client('s3')

    extra_args = {}
    if encrypt:
        extra_args['ServerSideEncryption'] = "AES256"

    s3.upload_file(file_path, bucket, key, ExtraArgs=extra_args)

    return format_s3_uri(bucket, key)


def upload_string(data: str, bucket, key, encrypt=False, session=None, silent=False):
    if not silent:
        log.upload_string(data, bucket, key, encrypt, session)

    session = session or _make_session()
    s3 = session.client('s3')

    buffer = BytesIO(data.encode('utf-8'))

    extra_args = {}
    if encrypt:
        extra_args['ServerSideEncryption'] = "AES256"

    s3.upload_fileobj(buffer, bucket, key, ExtraArgs=extra_args)

    return format_s3_uri(bucket, key)


def cp(from_uri, to_uri, session=None):
    # TODO error control for invalid uris
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
    destination = copy_key(from_bucket, from_key, to_bucket, to_key, session)
    rm_key(from_bucket, from_key, session)

    return destination


def mv(from_uri, to_uri, session=None):
    from_bucket, from_key = parse_s3_uri(from_uri)
    to_bucket, to_key = parse_s3_uri(to_uri)

    move_key(from_bucket, from_key, to_bucket, to_key, session)
