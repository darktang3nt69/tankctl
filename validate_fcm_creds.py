#!/usr/bin/env python3
"""
Validate Firebase service account credentials.
Usage: python3 validate_fcm_creds.py [path/to/google-services.json]
"""

import json
import sys
from pathlib import Path

def validate_credentials(json_path: str) -> bool:
    """Validate Firebase service account JSON."""
    path = Path(json_path)
    
    print(f"📋 Validating: {json_path}\n")
    
    # Check file exists
    if not path.exists():
        print(f"❌ File not found: {json_path}")
        return False
    print(f"✅ File exists")
    
    # Check readable
    if not path.is_file():
        print(f"❌ Not a file: {json_path}")
        return False
    print(f"✅ Is a file")
    
    # Parse JSON
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        print(f"✅ Valid JSON")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Check required fields
    required_fields = [
        'type',
        'project_id',
        'private_key_id',
        'private_key',
        'client_email',
        'client_id',
        'auth_uri',
        'token_uri',
    ]
    
    print(f"\n📝 Required fields:")
    missing = []
    for field in required_fields:
        if field in data:
            if field == 'private_key':
                # Show first and last part of key
                pk = data[field]
                if len(pk) > 100:
                    print(f"  ✅ {field}: {len(pk)} chars")
                else:
                    print(f"  ✅ {field}: {pk[:50]}...")
            else:
                print(f"  ✅ {field}: {data[field]}")
        else:
            print(f"  ❌ {field}: MISSING")
            missing.append(field)
    
    if missing:
        print(f"\n❌ Missing fields: {', '.join(missing)}")
        return False
    
    # Validate private_key format
    print(f"\n🔐 Private key validation:")
    pk = data.get('private_key', '')
    
    if not pk.startswith('-----BEGIN'):
        print(f"  ❌ Does not start with '-----BEGIN'")
        return False
    print(f"  ✅ Starts with '-----BEGIN'")
    
    if not pk.rstrip().endswith('-----END'):
        print(f"  ❌ Does not end with '-----END'")
        return False
    print(f"  ✅ Ends with '-----END'")
    
    if '\n' not in pk:
        print(f"  ❌ No newlines found (malformed)")
        return False
    print(f"  ✅ Contains newlines")
    
    # Try to load as credentials (if google-auth available)
    print(f"\n🔑 Attempting to load as service account:")
    try:
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_dict(
            data,
            scopes=['https://www.googleapis.com/auth/firebase.messaging']
        )
        print(f"  ✅ Successfully loaded as service account")
        print(f"  ✅ Project ID: {creds.project_id}")
        print(f"  ✅ Service account email: {creds.service_account_email}")
    except ImportError:
        print(f"  ⚠️  google-auth not installed (cannot fully validate)")
    except Exception as e:
        print(f"  ❌ Error loading credentials: {e}")
        return False
    
    print(f"\n✅ ALL CHECKS PASSED!")
    return True

if __name__ == '__main__':
    json_path = sys.argv[1] if len(sys.argv) > 1 else './google-services.json'
    success = validate_credentials(json_path)
    sys.exit(0 if success else 1)
