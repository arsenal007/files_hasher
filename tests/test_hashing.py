import io
import tempfile
import os
import pytest
import hashlib

from utils.hash_file import hash_file
from utils.files import LocalFileBackend, FileBackend

class DummySFTPFile(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class DummySFTPBackend(FileBackend):
    def __init__(self, file_content):
        self.file_content = file_content
    def open(self, file_path, mode='rb'):
        return DummySFTPFile(self.file_content)
    def stat(self, file_path):
        return len(self.file_content), 1234567890

def test_hash_file_local_success():
    backend = LocalFileBackend()
    content = b"test content"
    expected_md5 = hashlib.md5(content).hexdigest()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        md5, error = hash_file(backend, tmp_path)
        assert error is None
        assert md5 == expected_md5
    finally:
        os.remove(tmp_path)

def test_hash_file_local_not_found():
    backend = LocalFileBackend()
    md5, error = hash_file(backend, "/non/existent/file.txt")
    assert md5 is None
    assert error is not None

def test_hash_file_sftp_success():
    content = b"remote test"
    expected_md5 = hashlib.md5(content).hexdigest()
    backend = DummySFTPBackend(content)
    md5, error = hash_file(backend, "/dummy/path.txt")
    assert error is None
    assert md5 == expected_md5

def test_hash_file_sftp_error():
    class FailingSFTPBackend(FileBackend):
        def open(self, file_path, mode='rb'):
            raise IOError("SFTP error")
    backend = FailingSFTPBackend()
    md5, error = hash_file(backend, "/dummy/path.txt")
    assert md5 is None
    assert error is not None