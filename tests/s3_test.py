import boto3
from moto import mock_s3
from awsome import s3
from awsome.development import dry_run, debug_environment


def create_s3(prod=False):
    bucket = 'production' if prod else 'testing'

    conn = boto3.resource('s3', region_name='eu-west-1')
    conn.create_bucket(Bucket=bucket)

    return bucket


@mock_s3
def test_ls_prefix():
    create_s3()

    s3.upload_string('foo bar', 'testing', 'foo/bar/baz.txt')
    s3.upload_string('foo bam', 'testing', 'foo/bam.txt')

    files = s3.ls('s3://testing/foo')
    assert set(files) == {'foo/bar/', 'foo/bam.txt'}


@mock_s3
def test_ls_bucket():
    create_s3()

    s3.upload_string('foo bar', 'testing', 'foo/bar/baz.txt')
    s3.upload_string('foo bam', 'testing', 'foo/bam.txt')
    s3.upload_string('foo', 'testing', 'baz.txt')

    files = s3.ls('s3://testing')
    assert set(files) == {'foo/', 'baz.txt'}

    files = s3.ls('s3://testing/')
    assert set(files) == {'foo/', 'baz.txt'}


@mock_s3
def test_ls_recursive():
    create_s3()

    s3.upload_string('foo bar', 'testing', 'foo/bar/baz.txt')
    s3.upload_string('foo bam', 'testing', 'foo/bam.txt')
    s3.upload_string('foo baz', 'testing', 'bar/bam.txt')

    files = s3.ls('s3://testing/foo', recursive=True)
    assert set(files) == {'foo/bar/baz.txt', 'foo/bam.txt'}


@mock_s3
def test_rm():
    create_s3()

    s3.upload_string('foo bar', 'testing', 'foo/bar/baz.txt')
    s3.upload_string('foo baz', 'testing', 'foo/bam.txt')

    files = s3.ls('s3://testing/foo', recursive=True)
    assert set(files) == {'foo/bar/baz.txt', 'foo/bam.txt'}

    s3.rm('s3://testing/foo/bar/baz.txt')
    files = s3.ls('s3://testing/foo', recursive=True)
    assert set(files) == {'foo/bam.txt'}


@mock_s3
def test_download_file(tmpdir):
    p = tmpdir.mkdir("sub").join("hello.txt")
    bucket = create_s3()

    s3.upload_string('foo bar', bucket, 'foo/bar/baz.txt')
    s3.download_key(bucket, 'foo/bar/baz.txt', str(p))

    assert p.read() == 'foo bar'


@mock_s3
def test_move_key():
    test_bucket = create_s3()
    prod_bucket = create_s3(prod=True)

    s3.upload_string('foo baz', test_bucket, 'foo/bam.txt')
    s3.move_key(from_bucket=test_bucket, from_key='foo/bam.txt', to_bucket=prod_bucket)

    files = s3.ls(f's3://{prod_bucket}/', recursive=True)
    assert set(files) == {'foo/bam.txt'}
    assert s3.read_key(prod_bucket, 'foo/bam.txt') == 'foo baz'

    s3.upload_string('lorem ipsum', test_bucket, 'foo/bam.txt')
    s3.move_key(from_bucket=test_bucket, from_key='foo/bam.txt', to_bucket=prod_bucket, to_key='a.txt')
    files = s3.ls(f's3://{prod_bucket}/', recursive=True)
    assert set(files) == {'foo/bam.txt', 'a.txt'}
    assert s3.read_key(prod_bucket, 'a.txt') == 'lorem ipsum'


@mock_s3
def test_mv():
    test_bucket = create_s3()

    s3.upload_string('foo baz', test_bucket, 'foo/bam.txt')
    s3.mv(f's3://{test_bucket}/foo/bam.txt', f's3://{test_bucket}/baa.txt')

    files = s3.ls(f's3://{test_bucket}/', recursive=True)
    assert set(files) == {'baa.txt'}

    s3.upload_string('foo baz', test_bucket, 'foo/bam.txt')
    s3.mv(f's3://{test_bucket}/baa.txt', f's3://{test_bucket}/foo/')

    files = s3.ls(f's3://{test_bucket}/', recursive=True)
    assert set(files) == {'foo/baa.txt', 'foo/bam.txt'}


@mock_s3
def test_upload_file(tmpdir):
    p = tmpdir.mkdir("sub").join("hello.txt")
    p.write("content")

    bucket = create_s3()

    s3.upload_file(str(p), bucket, 'foo/bar/baz.txt')
    assert s3.read_key(bucket, 'foo/bar/baz.txt') == 'content'


@mock_s3
def test_cp_local(tmpdir):
    p = tmpdir.mkdir("sub").join("hello.txt")
    p.write("content")

    bucket = create_s3()

    s3.cp(f'file://{str(p)}', f's3://{bucket}/foo/bar/baz.txt')
    assert s3.read_key(bucket, 'foo/bar/baz.txt') == 'content'

    q = tmpdir.mkdir("sub2").join("world.txt")
    s3.cp(f's3://{bucket}/foo/bar/baz.txt', f'file://{str(q)}')
    assert q.read() == 'content'


def test_dry_run(capsys):
    with dry_run():
        s3.ls('s3://b1')
        captured = capsys.readouterr()
        assert captured.out == 'aws s3 ls s3://b1\n'

        s3.ls('s3://b1', recursive=True)
        captured = capsys.readouterr()
        assert captured.out == 'aws s3 ls --recursive s3://b1\n'

        s3.cp('s3://b1/foo', 's3://b2/bar/baz')
        captured = capsys.readouterr()
        assert captured.out == 'aws s3 cp s3://b1/foo s3://b2/bar/baz\n'

        s3.mv('s3://b1/foo', 's3://b2/bar/baz')
        captured = capsys.readouterr()
        assert captured.out == 'aws s3 mv s3://b1/foo s3://b2/bar/baz\n'

        s3.rm('s3://b1/foo')
        captured = capsys.readouterr()
        assert captured.out == 'aws s3 rm s3://b1/foo\n'


def test_debug_environment():
    with debug_environment(['b1']):
        s3.upload_string('foo baz', 'b1', '/bam.txt')
        s3.ls('s3://b1')
    assert True