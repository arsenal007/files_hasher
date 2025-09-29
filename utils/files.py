
import os
import paramiko

class FileBackend:
    def list_files(self, root):
        raise NotImplementedError

    def stat(self, file_path):
        raise NotImplementedError

    def open(self, file_path, mode='rb'):
        raise NotImplementedError

    def get_file_size(self, file_path):
        raise NotImplementedError

    def close(self):
        pass

class LocalFileBackend(FileBackend):
    def __init__(self):
        pass

    def list_files(self, root):
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                yield os.path.join(dirpath, fname)

    def stat(self, file_path):
        st = os.stat(file_path)
        return st.st_size, int(st.st_mtime)

    def open(self, file_path, mode='rb'):
        return open(file_path, mode)

    def get_file_size(self, file_path):
        return os.stat(file_path).st_size

class SFTPFileBackend(FileBackend):
    def __init__(self, config):
        self.config = config
        self.transport = None
        self.sftp = None
        self.transport = paramiko.Transport((self.config.get("SFTP_HOST"), self.config.get("SFTP_PORT")) )
        if self.config.get("SSH_KEY_PATH"):
            key = self._load_private_key(self.config.get("SSH_KEY_PATH"))
            self.transport.connect(username=self.config.get("SFTP_USER"), pkey=key)
        else:
            self.transport.connect(username=self.config.get("SFTP_USER"), password=self.config.get("SFTP_PASS"))
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def __del__(self):
        if hasattr(self, 'sftp') and self.sftp:
            self.sftp.close()
            self.sftp = None
        if hasattr(self, 'transport') and self.transport:
            self.transport.close()
            self.transport = None

    def list_files(self, root):
        import posixpath
        from stat import S_ISDIR
        for entry in self.sftp.listdir_attr(root):
            path = posixpath.join(root, entry.filename)
            if S_ISDIR(entry.st_mode):
                yield from self.list_files(path)
            else:
                yield path

    def stat(self, file_path):
        st = self.sftp.stat(file_path)
        return st.st_size, int(st.st_mtime)

    def open(self, file_path, mode='rb'):
        return self.sftp.open(file_path, mode)

    def get_file_size(self, file_path):
        return self.sftp.stat(file_path).st_size
    
    def _load_private_key(self, path):
        loaders = {
            "RSA": paramiko.RSAKey.from_private_key_file,
            "Ed25519": paramiko.Ed25519Key.from_private_key_file,
            "ECDSA": paramiko.ECDSAKey.from_private_key_file,
        }

        errors = {}
        for name, loader in loaders.items():
            try:
                return loader(path)
            except Exception as e:
                errors[name] = str(e)
                continue

    
        err_text = "\n".join(f"{algo}: {msg}" for algo, msg in errors.items())
        raise ValueError(f"Failed to load private key '{path}' with any supported algorithm.\nTried:\n{err_text}")
