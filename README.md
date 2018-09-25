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

# Example usage of AWSome

We will rename all the files from a bucket with a foo/bar/ prefix and copy them to another bucket.


```python
import pprint
from awsome import s3
from awsome.development import s3_sandbox, dry_run

pp = pprint.PrettyPrinter(indent=4)
```

## Intervention script

We create the function that will do the renaming/copy intervention.


```python
def intervention():
    keys = s3.ls('s3://testbucket/foo/bar/')
    for key in keys:
        new_key = key.replace('customers', 'clients')
        # Rename all objects with the same key
        s3.move_key(from_bucket='testbucket', from_key=key, to_bucket='testbucket', to_key=new_key)
        # Move all objects to the production bucket with the same key
        s3.move_key(from_bucket='testbucket', from_key=new_key, to_bucket='prodbucket')
```

## Testing the script

Before running the script in production we should do a few tests to make sure it's doing what we think it is.

### Creating test data

We will create some dummy files that mimic the structure of the files in our real aws instance to test the intervention on them.


```python
def create_test_data():
    for i in range(1, 6):
        # Files we will be changing
        key = f'foo/bar/customers_{i}.csv'
        s3.upload_string(data='some data', bucket='testbucket', key=key)
        
        # Files we want untouched
        key = f'foo/baz/companies_{i}.csv'
        s3.upload_string(data='some data', bucket='testbucket', key=key)
```

### Checking the test data

Let's check that the test data is created correctly. Of course we don't want to actually create those dummy files in aws. 

Instead we use the s3_sandbox context manager that provides a moto s3 instance where we can run our tests as they would run in a real S3 instance. We just need to pass it the name of the buckets it needs to create.


```python
with s3_sandbox(['testbucket', 'prodbucket']):
    create_test_data()
    print('Test bucket:')
    pp.pprint(s3.ls('s3://testbucket/', recursive=True))
    print('\nProd bucket:')
    pp.pprint(s3.ls('s3://prodbucket/', recursive=True))
```

    Test bucket:
    [   'foo/bar/customers_1.csv',
        'foo/bar/customers_2.csv',
        'foo/bar/customers_3.csv',
        'foo/bar/customers_4.csv',
        'foo/bar/customers_5.csv',
        'foo/baz/companies_1.csv',
        'foo/baz/companies_2.csv',
        'foo/baz/companies_3.csv',
        'foo/baz/companies_4.csv',
        'foo/baz/companies_5.csv']
    
    Prod bucket:
    []


We can see that the sample data has been created correctly.

### Checking the intervention script

To make sure that the script does what we want it to we will execute it with a dry run. This means that we won't actually execute the commands, just print the equivalent aws cli commands so we can visually inspect them.

One exception is that we don't want to patch the ls function (it doesn't change S3 so it is reasonable not to patch it) because we depend on its output to generate the rest of the commands. We will need set patch_ls to false.

The dry run context manager also creates a moto instance of S3 so we can rest assured that everything will execute in a sandbox and won't affect our real S3 instance.


```python
with dry_run(['testbucket', 'prodbucket'], patch_ls=False):
    create_test_data()
    intervention()
```

    aws s3 mv s3://testbucket/foo/bar/customers_3.csv s3://testbucket/foo/bar/clients_3.csv
    aws s3 mv s3://testbucket/foo/bar/clients_3.csv s3://prodbucket/foo/bar/clients_3.csv
    aws s3 mv s3://testbucket/foo/bar/customers_2.csv s3://testbucket/foo/bar/clients_2.csv
    aws s3 mv s3://testbucket/foo/bar/clients_2.csv s3://prodbucket/foo/bar/clients_2.csv
    aws s3 mv s3://testbucket/foo/bar/customers_5.csv s3://testbucket/foo/bar/clients_5.csv
    aws s3 mv s3://testbucket/foo/bar/clients_5.csv s3://prodbucket/foo/bar/clients_5.csv
    aws s3 mv s3://testbucket/foo/bar/customers_4.csv s3://testbucket/foo/bar/clients_4.csv
    aws s3 mv s3://testbucket/foo/bar/clients_4.csv s3://prodbucket/foo/bar/clients_4.csv
    aws s3 mv s3://testbucket/foo/bar/customers_1.csv s3://testbucket/foo/bar/clients_1.csv
    aws s3 mv s3://testbucket/foo/bar/clients_1.csv s3://prodbucket/foo/bar/clients_1.csv


### Executing the intervention script in a sandbox

This is where it gets interesting. We have inspected the dry run and everything looks reasonable, but you can never be too careful. To make sure we get it right we will execute the real script inside a moto S3 sandbox.


```python
with s3_sandbox(['testbucket', 'prodbucket']):
    create_test_data()
    print('Test bucket before:')
    pp.pprint(s3.ls('s3://testbucket/', recursive=True))
    print('\nProd bucket before:')
    pp.pprint(s3.ls('s3://prodbucket/', recursive=True))
    
    intervention()
    
    print('\n\nTest bucket after:')
    pp.pprint(s3.ls('s3://testbucket/', recursive=True))
    print('\nProd bucket after:')
    pp.pprint(s3.ls('s3://prodbucket/', recursive=True))
```

    Test bucket before:
    [   'foo/bar/customers_1.csv',
        'foo/bar/customers_2.csv',
        'foo/bar/customers_3.csv',
        'foo/bar/customers_4.csv',
        'foo/bar/customers_5.csv',
        'foo/baz/companies_1.csv',
        'foo/baz/companies_2.csv',
        'foo/baz/companies_3.csv',
        'foo/baz/companies_4.csv',
        'foo/baz/companies_5.csv']
    
    Prod bucket before:
    []
    
    
    Test bucket after:
    [   'foo/baz/companies_1.csv',
        'foo/baz/companies_2.csv',
        'foo/baz/companies_3.csv',
        'foo/baz/companies_4.csv',
        'foo/baz/companies_5.csv']
    
    Prod bucket after:
    [   'foo/bar/clients_1.csv',
        'foo/bar/clients_2.csv',
        'foo/bar/clients_3.csv',
        'foo/bar/clients_4.csv',
        'foo/bar/clients_5.csv']


Finally we have succesfully validated our script, and we can rest assured that it will do what we intend it to.
