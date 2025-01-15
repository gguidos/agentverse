import hashlib

def compute_md5(file_path):
    """Compute the MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()

class MD5Calculator:
    def __init__(self):
        pass
        
    def __call__(self, file_path: str) -> str:
        return compute_md5(file_path)