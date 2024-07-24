import hashlib

def hash_file(file_path):
    """Compute the MD5 hash of a file."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest(), None
    except Exception as e:
        return None, str(e)
