import random
import string
from contextlib import contextmanager
from typing import List
import boto3
from boto3 import Session
from botocore.exceptions import ClientError
from mock import patch
from moto import mock_s3

from awsome import fakes, s3

MARKER_BUCKET = 'awsome_marker_bucket'


@contextmanager
def s3_sandbox(buckets: List[str], create_marker_bucket: bool=False):
    with mock_s3():
        conn = boto3.resource('s3', region_name='eu-west-1')
        for bucket in buckets:
            conn.create_bucket(Bucket=bucket)

        if create_marker_bucket:
            conn.create_bucket(Bucket=MARKER_BUCKET)

        yield


@contextmanager
def dry_run_sandbox(buckets: List[str]=(), patch_ls=True):
    with mock_s3(), dry_run(patch_ls):
        for bucket in buckets:
            conn = boto3.resource('s3', region_name='eu-west-1')
            conn.create_bucket(Bucket=bucket)

        yield


def check_marker_bucket():
    session = boto3.resource('s3')
    try:
        buckets = [bucket.name for bucket in session.buckets.all()]
    except ClientError:
        raise UnsupportedEnvironment(f'Invalid access. Are you sure you are in a sandbox?')
    if MARKER_BUCKET not in buckets:
        raise UnsupportedEnvironment(f'S3 instance needs a bucket called "{MARKER_BUCKET}" to make \
         sure you are in a sandbox')


@contextmanager
def dry_run(patch_ls=True):
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


class UnsupportedEnvironment(Exception):
    pass


def create_mock_keys(bucket: str, keys: List[str]):
    check_marker_bucket()

    data = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(10, 24)))
    for key in keys:
        s3.upload_string(data=data, bucket=bucket, key=key)
