import hashlib

def hash_file(backend, file_path, algorithm: str = "md5", chunk_size: int = 4096):
    """Compute a file hash using any backend 
    Args:
        backend: FileBackend instance (LocalFileBackend, SFTPFileBackend, etc.)
        file_path: path to the file (string)
        algorithm: hashing algorithm (md5, sha1, sha256, ...)
        chunk_size: size of chunks to read at once (bytes)
    
    Returns:
        (hex_digest, error_message) 
        If success: (digest_str, None)
        If failure: (None, str(error))
    """
    try:
        hasher = hashlib.new(algorithm)
        with backend.open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest(), None
    except Exception as e:
        return None, str(e)