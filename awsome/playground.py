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

from awsome import fakes, s3


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

    with patch('awsome.s3.cp') as cp_mock, patch('awsome.s3.mv') as mv_mock, patch('awsome.s3.rm_key') as rm_key_mock, \
            patch('awsome.s3.rm') as rm_mock, patch('awsome.s3.copy_key') as copy_key_mock:

        cp_mock.side_effect = fakes.fake_cp
        mv_mock.side_effect = fakes.fake_mv
        rm_key_mock.side_effect = fakes.fake_rm_key
        rm_mock.side_effect = fakes.fake_rm
        copy_key_mock.side_effect = fakes.fake_copy_key

        if patch_ls:
            with patch('awsome.s3.ls') as ls_mock:
                ls_mock.side_effect = fakes.fake_ls
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


def create_mock_keys(bucket: str, keys: List[str]):
    if not inside_sandbox():
        raise UnsupportedEnvironment('Cannot create mock keys outside a sandbox.')

    data = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(10, 24)))
    for key in keys:
        s3.upload_string(data=data, bucket=bucket, key=key)
