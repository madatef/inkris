import re
import bcrypt


class PasswordPolicy:
    @staticmethod
    def validate(password: str) -> tuple[bool, str | None]:
        """
        Validate password meets common security requirements.
        """
        if len(password) < 8:
            return False, 'Password must be at least 8 characters long'
        
        if not re.search(r'[A-Z]', password):
            return False, 'Password must contain at least one uppercase letter'
        
        if not re.search(r'[a-z]', password):
            return False, 'Password must contain at least one lowercase letter'
        
        if not re.search(r'\d', password):
            return False, 'Password must contain at least one digit'
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', password):
            return False, 'Password must contain at least one special character'
        
        return True, None
        
def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    """
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )