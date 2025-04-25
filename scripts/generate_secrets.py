#!/usr/bin/env python3
import secrets
import base64

def generate_secret_key(length=32):
    """Generate a secure random string suitable for secret keys."""
    return base64.b64encode(secrets.token_bytes(length)).decode('utf-8')

# Generate different keys for different purposes
secret_key = generate_secret_key(32)
pre_shared_key = generate_secret_key(32)
jwt_secret_key = generate_secret_key(32)

# Create .env content with generated keys
env_content = f"""# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost/aquarium

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security Keys
SECRET_KEY={secret_key}
PRE_SHARED_KEY={pre_shared_key}
JWT_SECRET_KEY={jwt_secret_key}

# JWT Settings
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
"""

# Write to .env file
with open('.env', 'w') as f:
    f.write(env_content)

print("Generated new .env file with secure random keys")
print(f"Pre-shared key for tank registration: {pre_shared_key}")
print("Make sure to save this key as you'll need it to register tanks!") 