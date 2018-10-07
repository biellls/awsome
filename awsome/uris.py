def peel(uri):
    if uri.startswith('s3://'):
        return uri[len('s3://'):]
    elif uri.startswith('file://'):
        return uri[len('file://'):]

    raise ValueError(f'Invalid URI format for {uri}')


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