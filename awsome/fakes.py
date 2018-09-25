
def fake_ls(uri: str, recursive: bool=False, session=None):
    print(f"aws s3 ls {'--recursive ' if recursive else ''}{uri}")


def fake_cp(from_uri, to_uri, session=None):
    print(f"aws s3 cp {from_uri} {to_uri}")


def fake_mv(from_uri, to_uri, session=None):
    print(f"aws s3 mv {from_uri} {to_uri}")


def fake_rm(uri, session=None):
    print(f"aws s3 rm {uri}")
