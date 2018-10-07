from awsome.uris import format_s3_uri


def ls(uri: str, recursive: bool=False, session=None):
    print(f"aws s3 ls {'--recursive ' if recursive else ''}{uri}")


def cp(from_uri, to_uri, session=None):
    print(f"aws s3 cp {from_uri} {to_uri}")


def mv(from_uri, to_uri, session=None):
    print(f"aws s3 mv {from_uri} {to_uri}")


def rm(uri, session=None):
    print(f"aws s3 rm {uri}")


def rm_key(bucket, key, session=None):
    s3_uri = format_s3_uri(bucket, key)

    print(f"aws s3 rm {s3_uri}")


def copy_key(from_bucket, from_key, to_bucket, to_key=None, session=None):
    from_uri = format_s3_uri(from_bucket, from_key)
    to_uri = format_s3_uri(to_bucket, to_key or from_key)

    cp(from_uri, to_uri, session)


def download_key(bucket, key, file_path, session=None):
    s3_uri = format_s3_uri(bucket, key)
    file_uri = 'file://' + file_path

    cp(s3_uri, file_uri, session)


def read_key(bucket, key, session=None):
    s3_uri = format_s3_uri(bucket, key)

    cp(s3_uri, '-', session)


def upload_file(file_path, bucket, key, encrypt=False, session=None):
    file_uri = 'file://' +  file_path
    s3_uri = format_s3_uri(bucket, key)

    cp(file_uri, s3_uri, session)


def upload_string(data: str, bucket, key, encrypt=False, session=None):
    s3_uri = format_s3_uri(bucket, key)

    print(f"echo '{data}' | aws s3 cp - {s3_uri}")
