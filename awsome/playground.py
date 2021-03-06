import random
import string
from contextlib import contextmanager
from typing import List
import boto3
import requests
from boto3 import Session
from mock import patch
from moto import mock_s3
from requests import ConnectionError

from awsome import log, s3


class UnsupportedEnvironment(Exception):
    pass


@contextmanager
def s3_sandbox(buckets: List[str]):
    with mock_s3():
        conn = boto3.resource('s3', region_name='eu-west-1')
        for bucket in buckets:
            conn.create_bucket(Bucket=bucket)

        yield


def inside_sandbox():
    """
    Checks if we are inside a sandbox by trying to connect to aws. Can cause a fake positive if we have no
     internet connectivity, but if we don't we are still safe. """
    try:
        requests.get('https://aws.amazon.com')
        return False
    except ConnectionError:
        return True


@contextmanager
def dry_run(patch_ls=True, safe=True):
    if safe and not inside_sandbox():
        raise UnsupportedEnvironment('Cannot be executed outside a sandbox in safe mode.')

    with patch('awsome.s3.mv') as mv_mock, patch('awsome.s3.rm_key') as rm_key_mock, \
            patch('awsome.s3.copy_key') as copy_key_mock, patch('awsome.s3.download_key') as download_key_mock, \
            patch('awsome.s3.read_key') as read_key_mock, patch('awsome.s3.upload_file') as upload_file_mock, \
            patch('awsome.s3.upload_string') as upload_string_mock:

        mv_mock.side_effect = log.mv
        rm_key_mock.side_effect = log.rm_key
        copy_key_mock.side_effect = log.copy_key
        download_key_mock.side_effect = log.download_key
        read_key_mock.side_effect = log.read_key
        upload_file_mock.side_effect = log.upload_file
        upload_string_mock.side_effect = log.upload_string

        if patch_ls:
            with patch('awsome.s3.ls') as ls_mock:
                ls_mock.side_effect = log.ls
                yield
        else:
            yield


@contextmanager
def boto3_session(session: Session):
    with patch('awsome.s3._make_session') as get_session_mock:
        get_session_mock.return_value = session
        yield


@contextmanager
def aws_profile(profile: str):
    s = Session(profile_name=profile)
    with boto3_session(s):
        yield


def create_mock_keys(bucket: str, keys: List[str], silent=True):
    if not inside_sandbox():
        raise UnsupportedEnvironment('Cannot create mock keys outside a sandbox.')

    for key in keys:
        data = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(10, 24)))
        s3.upload_string(data=data, bucket=bucket, key=key, silent=silent)
