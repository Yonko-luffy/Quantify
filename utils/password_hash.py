# utils/password_hash.py - Ultra-simple Argon2-only password hashing
"""
Simple and secure password hashing using Argon2 exclusively.
No fallbacks, no complexity - just the best security available.
"""

# Import argon2 - this is required, no fallbacks
try:
    import argon2
    from argon2.exceptions import VerifyMismatchError, InvalidHash
except ImportError:
    raise ImportError(
        "argon2-cffi is required for password hashing. "
        "Install it with: pip install argon2-cffi"
    )

# Create password hasher with secure defaults
# These settings provide excellent security with reasonable performance
password_hasher = argon2.PasswordHasher(
    time_cost=3,        # Number of iterations (default: 3)
    memory_cost=65536,  # Memory usage in KiB (default: 65536 = 64MB)
    parallelism=4,      # Number of parallel threads (default: 4)
    hash_len=32,        # Length of hash in bytes (default: 32)
    salt_len=16         # Length of salt in bytes (default: 16)
)


def generate_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.
    
    Args:
        password (str): The password to hash
    
    Returns:
        str: The Argon2 hashed password
    
    Raises:
        RuntimeError: If hashing fails
    """
    try:
        return password_hasher.hash(password)
    except Exception as e:
        raise RuntimeError(f"Password hashing failed: {e}")


def check_password_hash(hash_value: str, password: str) -> bool:
    """
    Verify a password against an Argon2 hash.
    
    Args:
        hash_value (str): The stored Argon2 hash
        password (str): The password to verify
    
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        password_hasher.verify(hash_value, password)
        return True
    except VerifyMismatchError:
        # Wrong password
        return False
    except (InvalidHash, Exception):
        # Invalid hash format or other error
        return False


# Simple aliases for backward compatibility
def secure_hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return generate_password_hash(password)


def verify_password(hash_value: str, password: str) -> bool:
    """Verify a password against an Argon2 hash."""
    return check_password_hash(hash_value, password)