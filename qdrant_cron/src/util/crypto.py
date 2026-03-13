from typing import Optional
import hashlib

def generate_file_sha256(
    *, file_bytes: Optional[bytes] = None, file_path: Optional[str] = None
):
    """
    Generate sha256 for a given file path or contents.
    Either file_content or file_path must be specified.
    """
    sha256_hash = hashlib.sha256()

    if file_bytes:
        sha256_hash.update(file_bytes)
    elif file_path:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    else:
        raise RuntimeError(
            "Error in generating sha256: either file_content or file_path must be provided"
        )

    return sha256_hash.hexdigest()

