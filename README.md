
# AWSome
A clean wrapper over boto3 inspired by the user friendly aws cli.

## Sessions
All actions take an optional session parameter. If none is specified it will create one with whatever default configuration you have in ~/.aws/ directory.

Since AWSome encourages writing your script once and running it in different environments, it isn't advisable to have a default session because there is the risk that you might run your script accidentally in your real S3. On the other hand it's not too clean or practical to give every action a session and you would have to remember to create new sessions and give your script the right ones.

The recommended way is to write your script without worrying about sessions and use one of our context managers to provide it explicitly without changing your code.


```python
from awsome import s3
# Default session
buckets = s3.ls()

# Explicitly defined session
session = boto3.session.Session(
        aws_access_key_id='XXXXXX',
        aws_secret_access_key='XXXXXX',
        region_name='eu-west-1'
    )
keys = s3.ls('s3://bucket/key', session=session)

# Explicitly defined session with context manager
from awsome.playground import boto3_session

session = boto3.session.Session(
        aws_access_key_id='XXXXXX',
        aws_secret_access_key='XXXXXX',
        region_name='eu-west-1'
    )

with boto3_session(session):
    buckets = s3.ls()
    
# Profile defined in ~/.aws/credentials
from awsome.playground import aws_profile

with aws_profile(profile='myprofile'):
    buckets = s3.ls()
```

# Example usage of AWSome

We will rename all the files from a bucket with a foo/bar/ prefix and copy them to another bucket.


```python
import pprint
from awsome import s3
from awsome.playground import s3_sandbox, dry_run, aws_profile, create_mock_keys

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
        s3.copy_key(from_bucket='testbucket', from_key=new_key, to_bucket='prodbucket')
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
    print('\nTest bucket:')
    pp.pprint(s3.ls('s3://testbucket/', recursive=True))
    print('\nProd bucket:')
    pp.pprint(s3.ls('s3://prodbucket/', recursive=True))
```

    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_1.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_1.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_2.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_2.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_3.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_3.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_4.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_4.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_5.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_5.csv
    
    Test bucket:
    aws s3 ls --recursive s3://testbucket/
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
    aws s3 ls --recursive s3://prodbucket/
    []


We can see that the sample data has been created correctly.

### Checking the intervention script

To make sure that the script does what we want it to we will execute it with a dry run. This means that we won't actually execute the commands, just print the equivalent aws cli commands so we can visually inspect them.

One exception is that we don't want to patch the ls function (it doesn't change S3 so it is reasonable not to patch it) because we depend on its output to generate the rest of the commands. We will need set patch_ls to false.

The dry_run can only be executed inside a sandbox unless you provide the argument safe=False.


```python
with s3_sandbox(['testbucket', 'prodbucket']):
    create_test_data()
    print('\n')
    with dry_run(patch_ls=False):
        intervention()
```

    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_1.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_1.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_2.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_2.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_3.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_3.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_4.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_4.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_5.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_5.csv
    
    
    aws s3 ls s3://testbucket/foo/bar/
    aws s3 cp s3://testbucket/foo/bar/customers_2.csv s3://testbucket/foo/bar/clients_2.csv
    aws s3 rm s3://testbucket/foo/bar/customers_2.csv
    aws s3 cp s3://testbucket/foo/bar/clients_2.csv s3://prodbucket/foo/bar/clients_2.csv
    aws s3 cp s3://testbucket/foo/bar/customers_4.csv s3://testbucket/foo/bar/clients_4.csv
    aws s3 rm s3://testbucket/foo/bar/customers_4.csv
    aws s3 cp s3://testbucket/foo/bar/clients_4.csv s3://prodbucket/foo/bar/clients_4.csv
    aws s3 cp s3://testbucket/foo/bar/customers_3.csv s3://testbucket/foo/bar/clients_3.csv
    aws s3 rm s3://testbucket/foo/bar/customers_3.csv
    aws s3 cp s3://testbucket/foo/bar/clients_3.csv s3://prodbucket/foo/bar/clients_3.csv
    aws s3 cp s3://testbucket/foo/bar/customers_5.csv s3://testbucket/foo/bar/clients_5.csv
    aws s3 rm s3://testbucket/foo/bar/customers_5.csv
    aws s3 cp s3://testbucket/foo/bar/clients_5.csv s3://prodbucket/foo/bar/clients_5.csv
    aws s3 cp s3://testbucket/foo/bar/customers_1.csv s3://testbucket/foo/bar/clients_1.csv
    aws s3 rm s3://testbucket/foo/bar/customers_1.csv
    aws s3 cp s3://testbucket/foo/bar/clients_1.csv s3://prodbucket/foo/bar/clients_1.csv


### Executing the intervention script in a sandbox

This is where it gets interesting. We have inspected the dry run and everything looks reasonable, but you can never be too careful. To make sure we get it right we will execute the real script inside a moto S3 sandbox.


```python
with s3_sandbox(['testbucket', 'prodbucket']):
    create_test_data()
    print('\nTest bucket before:')
    pp.pprint(s3.ls('s3://testbucket/', recursive=True))
    print('\nProd bucket before:')
    pp.pprint(s3.ls('s3://prodbucket/', recursive=True))
    
    print('\n\nStarting intervention:')
    intervention()
    print('Ending intervention:')
    
    print('\n\nTest bucket after:')
    pp.pprint(s3.ls('s3://testbucket/', recursive=True))
    print('\nProd bucket after:')
    pp.pprint(s3.ls('s3://prodbucket/', recursive=True))
```

    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_1.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_1.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_2.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_2.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_3.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_3.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_4.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_4.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/bar/customers_5.csv
    echo 'some data' | aws s3 cp - s3://testbucket/foo/baz/companies_5.csv
    
    Test bucket before:
    aws s3 ls --recursive s3://testbucket/
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
    aws s3 ls --recursive s3://prodbucket/
    []
    
    
    Starting intervention:
    aws s3 ls s3://testbucket/foo/bar/
    aws s3 cp s3://testbucket/foo/bar/customers_2.csv s3://testbucket/foo/bar/clients_2.csv
    aws s3 rm s3://testbucket/foo/bar/customers_2.csv
    aws s3 cp s3://testbucket/foo/bar/clients_2.csv s3://prodbucket/foo/bar/clients_2.csv
    aws s3 cp s3://testbucket/foo/bar/customers_4.csv s3://testbucket/foo/bar/clients_4.csv
    aws s3 rm s3://testbucket/foo/bar/customers_4.csv
    aws s3 cp s3://testbucket/foo/bar/clients_4.csv s3://prodbucket/foo/bar/clients_4.csv
    aws s3 cp s3://testbucket/foo/bar/customers_3.csv s3://testbucket/foo/bar/clients_3.csv
    aws s3 rm s3://testbucket/foo/bar/customers_3.csv
    aws s3 cp s3://testbucket/foo/bar/clients_3.csv s3://prodbucket/foo/bar/clients_3.csv
    aws s3 cp s3://testbucket/foo/bar/customers_5.csv s3://testbucket/foo/bar/clients_5.csv
    aws s3 rm s3://testbucket/foo/bar/customers_5.csv
    aws s3 cp s3://testbucket/foo/bar/clients_5.csv s3://prodbucket/foo/bar/clients_5.csv
    aws s3 cp s3://testbucket/foo/bar/customers_1.csv s3://testbucket/foo/bar/clients_1.csv
    aws s3 rm s3://testbucket/foo/bar/customers_1.csv
    aws s3 cp s3://testbucket/foo/bar/clients_1.csv s3://prodbucket/foo/bar/clients_1.csv
    Ending intervention:
    
    
    Test bucket after:
    aws s3 ls --recursive s3://testbucket/
    [   'foo/bar/clients_1.csv',
        'foo/bar/clients_2.csv',
        'foo/bar/clients_3.csv',
        'foo/bar/clients_4.csv',
        'foo/bar/clients_5.csv',
        'foo/baz/companies_1.csv',
        'foo/baz/companies_2.csv',
        'foo/baz/companies_3.csv',
        'foo/baz/companies_4.csv',
        'foo/baz/companies_5.csv']
    
    Prod bucket after:
    aws s3 ls --recursive s3://prodbucket/
    [   'foo/bar/clients_1.csv',
        'foo/bar/clients_2.csv',
        'foo/bar/clients_3.csv',
        'foo/bar/clients_4.csv',
        'foo/bar/clients_5.csv']


Finally we have succesfully validated our script, and we can rest assured that it will do what we intend it to.

### Creating mock keys
Say you want to replicate your keys from your real bucket into your sandbox. There is an easy way to do that.

First we need to read the keys from your buckets:


```python
with aws_profile(profile='myprofile'):
    test_keys = s3.ls('s3://test-bucket/', recursive=True)
    prod_keys = s3.ls('s3://production-bucket/', recursive=True)
```

Next we can use the function create_mock_keys to populate those keys with random (short) data, therefore recreating the same keys that we have in our real buckets. This can help us be even more sure that the script runs correctly.

We can rest assured that create_mock_keys will not write any data to our real S3 because it only works inside a sandbox.


```python
from awsome.playground import s3_sandbox

with s3_sandbox(buckets=['test-bucket', 'production-bucket']):
    create_mock_keys('test-bucket', test_keys)
    create_mock_keys('production-bucket', prod_keys)
    
    intervention()
    
    pp.pprint(s3.ls('s3://test-bucket/.../', recursive=True))
    print('\n')
    pp.pprint(s3.ls('s3://prod-bucket/.../', recursive=True))
```
