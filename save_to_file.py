from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def generate_vapid_keys():
    # Generate ECDSA private key (SECP256R1 = prime256v1)
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # Export PEM formats (for your backup/debugging)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()

    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    # Export raw public key bytes (for frontend Push API)
    public_numbers = public_key.public_numbers()
    public_key_bytes = b'\x04' + \
        public_numbers.x.to_bytes(32, 'big') + \
        public_numbers.y.to_bytes(32, 'big')
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode().rstrip("=")

    # Export private key bytes (for backend pywebpush)
    private_numbers = private_key.private_numbers()
    private_key_bytes = private_numbers.private_value.to_bytes(32, 'big')
    private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode().rstrip("=")

    print("===== BACKEND PRIVATE KEY (store securely) =====")
    print(private_key_b64)
    print()
    print("===== FRONTEND PUBLIC KEY (use in pushManager.subscribe) =====")
    print(public_key_b64)
    print()
    print("===== PEM KEYS (optional backup) =====")
    print("Private Key PEM:")
    print(private_key_pem)
    print()
    print("Public Key PEM:")
    print(public_key_pem)

if __name__ == "__main__":
    generate_vapid_keys()
