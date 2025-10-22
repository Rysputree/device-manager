import re

UPPER = re.compile(r"[A-Z]")
LOWER = re.compile(r"[a-z]")
DIGIT = re.compile(r"[0-9]")
SPECIAL = re.compile(r"[^A-Za-z0-9]")


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for maximum length to prevent bcrypt issues
    if len(password.encode('utf-8')) > 72:
        return False, "Password is too long (maximum 72 characters)"
    
    classes = 0
    classes += 1 if UPPER.search(password) else 0
    classes += 1 if LOWER.search(password) else 0
    classes += 1 if DIGIT.search(password) else 0
    classes += 1 if SPECIAL.search(password) else 0
    if classes < 3:
        return False, "Password must include 3 of: uppercase, lowercase, number, special"
    return True, None 