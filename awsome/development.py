from contextlib import contextmanager, ExitStack
from typing import List
import boto3
from mock import patch
from moto import mock_s3
from awsome import fakes


@contextmanager
def s3_sandbox(buckets: List[str]):
    with mock_s3():
        for bucket in buckets:
            conn = boto3.resource('s3', region_name='eu-west-1')
            conn.create_bucket(Bucket=bucket)

        yield


@contextmanager
def dry_run(buckets: List[str]=(), patch_ls=True):
    with mock_s3(), patch('awsome.s3.cp') as cp_mock, patch('awsome.s3.mv') as mv_mock, \
            patch('awsome.s3.rm') as rm_mock, patch('awsome.s3.move_key') as move_key_mock:
        for bucket in buckets:
            conn = boto3.resource('s3', region_name='eu-west-1')
            conn.create_bucket(Bucket=bucket)

        cp_mock.side_effect = fakes.fake_cp
        mv_mock.side_effect = fakes.fake_mv
        rm_mock.side_effect = fakes.fake_rm
        move_key_mock.side_effect = fakes.fake_move_key

        if patch_ls:
            with patch('awsome.s3.ls') as ls_mock:
                ls_mock.side_effect = fakes.fake_ls
                yield
        else:
            yield
