def fake_ls(uri: str, recursive: bool=False, session=None):
    print(f"aws s3 ls {'--recursive ' if recursive else ''}{uri}")


def fake_cp(from_uri, to_uri, session=None):
    print(f"aws s3 cp {from_uri} {to_uri}")


def fake_mv(from_uri, to_uri, session=None):
    print(f"aws s3 mv {from_uri} {to_uri}")


def fake_rm(uri, session=None):
    print(f"aws s3 rm {uri}")


def fake_rm_key(bucket, key, session=None):
    print(f"aws s3 rm s3://{bucket}/{key}")


def fake_copy_key(from_bucket, from_key, to_bucket, to_key=None, session=None):
    print(f'aws s3 cp s3://{from_bucket}/{from_key} s3://{to_bucket}/{to_key or from_key}')
