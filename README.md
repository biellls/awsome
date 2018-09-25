# AWSome
A clean wrapper over boto3 inspired by the user friendly aws cli.

## Sessions
All actions take an optional session parameter. If none is specified it will create one with whatever default configuration you have in ~/.aws/ directory.

```python
from awsome import s3
# Default session
keys = s3.ls('s3://bucket/key')

# Explicitly defined session
session = boto3.session.Session(
        aws_access_key_id='XXXXXX',
        aws_secret_access_key='XXXXXX',
        region_name='eu-west-1'
    )
keys = s3.ls('s3://bucket/key', session=session)
```

## S3
### List keys

```python
# List keys and prefixes with the prefix key
keys = s3.ls('s3://bucket/key')

# List all keys with the prefix key
keys = s3.ls('s3://bucket/key', recursive=True)
```
