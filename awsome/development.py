from contextlib import contextmanager
from typing import List
import boto3
from mock import patch
from moto import mock_s3

from awsome import s3, fakes


@contextmanager
def debug_environment(buckets: List[str]):
    with mock_s3():
        for bucket in buckets:
            conn = boto3.resource('s3', region_name='eu-west-1')
            conn.create_bucket(Bucket=bucket)

        yield


@contextmanager
def dry_run():
    with mock_s3():
        ls_patcher = patch('awsome.s3.ls')
        ls_mock = ls_patcher.start()
        ls_mock.side_effect = fakes.fake_ls

        cp_patcher = patch('awsome.s3.cp')
        cp_mock = cp_patcher.start()
        cp_mock.side_effect = fakes.fake_cp

        mv_patcher = patch('awsome.s3.mv')
        mv_mock = mv_patcher.start()
        mv_mock.side_effect = fakes.fake_mv

        rm_patcher = patch('awsome.s3.rm')
        rm_mock = rm_patcher.start()
        rm_mock.side_effect = fakes.fake_rm

        yield

        ls_patcher.stop()
        cp_patcher.stop()
        mv_patcher.stop()
        rm_patcher.stop()
