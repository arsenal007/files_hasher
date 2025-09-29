import os
import tempfile
import pytest
from utils.files import LocalFileBackend, FileBackend

class DummySFTPFile:
    def __init__(self, content):
        self._content = content
        self._pos = 0
    def read(self, size=-1):
        if size == -1:
            size = len(self._content) - self._pos
        data = self._content[self._pos:self._pos+size]
        self._pos += size
        return data
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class DummySFTPStat:
    def __init__(self, size, mtime):
        self.st_size = size
        self.st_mtime = mtime
        self.st_mode = 0o100644  # regular file

class DummySFTPClient:
    def __init__(self, files):
        self.files = files  # dict: path -> content
    def listdir_attr(self, root):
        class Entry:
            def __init__(self, filename, st_mode):
                self.filename = filename
                self.st_mode = st_mode
        return [Entry(os.path.basename(path), 0o100644) for path in self.files if path.startswith(root)]
    def stat(self, file_path):
        content = self.files[file_path]
        return DummySFTPStat(len(content), 1234567890)
    def open(self, file_path, mode='rb'):
        return DummySFTPFile(self.files[file_path])
    def close(self):
        pass

class DummyConfig:
    sftp_host = "dummy"
    sftp_port = 22
    sftp_user = "user"
    sftp_pass = "pass"
    ssh_key_path = None
    def get(self, key):
        return None

def test_local_file_backend(tmp_path):
    backend = LocalFileBackend()
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")
    files = list(backend.list_files(str(tmp_path)))
    assert str(test_file) in files
    size, mtime = backend.stat(str(test_file))
    assert size == len("hello world")
    with backend.open(str(test_file), "rb") as f:
        data = f.read()
        assert data == b"hello world"
    assert backend.get_file_size(str(test_file)) == len("hello world")

def test_file_backend_interface():
    backend = FileBackend()
    with pytest.raises(NotImplementedError):
        backend.list_files("/tmp")
    with pytest.raises(NotImplementedError):
        backend.stat("/tmp/file")
    with pytest.raises(NotImplementedError):
        backend.open("/tmp/file")
    with pytest.raises(NotImplementedError):
        backend.get_file_size("/tmp/file")
