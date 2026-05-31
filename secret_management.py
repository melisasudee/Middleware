"""
Secret Management Module
Secure handling of secrets, API keys, and sensitive credentials
"""

import os
import json
import hashlib
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecretManager:
    """Centralized secret management"""
    
    def __init__(self, master_key=None, secrets_file=None):
        """Initialize secret manager"""
        self.master_key = master_key or os.getenv('MASTER_SECRET_KEY')
        self.secrets_file = secrets_file or Path('.secrets.json')
        self.secrets = self._load_secrets()
        self._cipher_suite = None
    
    @property
    def cipher_suite(self):
        """Get or create cipher suite"""
        if self._cipher_suite is None:
            if not self.master_key:
                raise ValueError("Master key not set for encryption")
            
            # Derive encryption key from master key
            key = self._derive_key(self.master_key)
            self._cipher_suite = Fernet(key)
        
        return self._cipher_suite
    
    @staticmethod
    def _derive_key(master_key):
        """Derive encryption key from master key"""
        # Use PBKDF2HMAC to derive a Fernet-compatible key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ceng302_middleware_salt',
            iterations=480000,
        )
        key_bytes = kdf.derive(master_key.encode() if isinstance(master_key, str) else master_key)
        return base64.urlsafe_b64encode(key_bytes)
    
    def _load_secrets(self):
        """Load secrets from file"""
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_secrets(self):
        """Save secrets to file"""
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.secrets_file, 'w') as f:
            json.dump(self.secrets, f)
        
        # Restrict file permissions
        os.chmod(self.secrets_file, 0o600)
    
    def set_secret(self, key, value, encrypt=True):
        """Store a secret"""
        if encrypt and self.master_key:
            encrypted = self.cipher_suite.encrypt(
                value.encode() if isinstance(value, str) else value
            ).decode()
            self.secrets[key] = {'encrypted': True, 'value': encrypted}
        else:
            self.secrets[key] = {'encrypted': False, 'value': value}
        
        self._save_secrets()
    
    def get_secret(self, key, decrypt=True):
        """Retrieve a secret"""
        if key not in self.secrets:
            raise KeyError(f"Secret '{key}' not found")
        
        secret_data = self.secrets[key]
        value = secret_data.get('value')
        is_encrypted = secret_data.get('encrypted', False)
        
        if is_encrypted and decrypt and self.master_key:
            try:
                decrypted = self.cipher_suite.decrypt(value.encode()).decode()
                return decrypted
            except Exception as e:
                raise ValueError(f"Failed to decrypt secret: {e}")
        
        return value
    
    def rotate_key(self, new_master_key):
        """Rotate master key and re-encrypt all secrets"""
        old_secrets = self.secrets.copy()
        old_cipher = self._cipher_suite
        
        # Switch to new key
        self.master_key = new_master_key
        self._cipher_suite = None
        self.secrets = {}
        
        # Re-encrypt all secrets
        for key, secret_data in old_secrets.items():
            if secret_data.get('encrypted'):
                try:
                    decrypted = old_cipher.decrypt(
                        secret_data['value'].encode()
                    ).decode()
                    self.set_secret(key, decrypted, encrypt=True)
                except Exception as e:
                    print(f"Warning: Could not rotate key for '{key}': {e}")
            else:
                self.set_secret(key, secret_data['value'], encrypt=False)
        
        self._save_secrets()
    
    def generate_api_key(self, name, length=32):
        """Generate a secure API key"""
        api_key = base64.urlsafe_b64encode(os.urandom(length)).decode().rstrip('=')
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        self.set_secret(f'api_key_{name}', api_key, encrypt=True)
        self.set_secret(f'api_key_hash_{name}', key_hash, encrypt=False)
        
        return api_key
    
    def verify_api_key(self, name, provided_key):
        """Verify API key"""
        try:
            stored_key_hash = self.get_secret(f'api_key_hash_{name}', decrypt=False)
            provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
            return stored_key_hash == provided_hash
        except KeyError:
            return False
    
    def list_secrets(self, decrypt=False):
        """List all stored secrets"""
        result = {}
        for key, secret_data in self.secrets.items():
            if decrypt and secret_data.get('encrypted') and self.master_key:
                try:
                    result[key] = self.get_secret(key, decrypt=True)
                except Exception:
                    result[key] = '[DECRYPTION FAILED]'
            else:
                result[key] = '[ENCRYPTED]' if secret_data.get('encrypted') else secret_data.get('value')
        
        return result
    
    def delete_secret(self, key):
        """Delete a secret"""
        if key in self.secrets:
            del self.secrets[key]
            self._save_secrets()


class EnvironmentSecretManager:
    """Manage secrets from environment variables"""
    
    REQUIRED_SECRETS = [
        'JWT_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'ADMIN_PASSWORD',
    ]
    
    OPTIONAL_SECRETS = [
        'API_KEYS',
        'ENCRYPTION_KEY',
    ]
    
    @staticmethod
    def validate_secrets():
        """Validate all required secrets are set"""
        missing = []
        for secret in EnvironmentSecretManager.REQUIRED_SECRETS:
            if not os.getenv(secret):
                missing.append(secret)
        
        if missing:
            raise ValueError(f"Missing required secrets: {', '.join(missing)}")
    
    @staticmethod
    def get_secrets():
        """Get all secrets from environment"""
        secrets = {}
        for secret in (EnvironmentSecretManager.REQUIRED_SECRETS + 
                      EnvironmentSecretManager.OPTIONAL_SECRETS):
            value = os.getenv(secret)
            if value:
                secrets[secret] = value
        
        return secrets
    
    @staticmethod
    def mask_secret(secret_value, show_chars=4):
        """Mask secret for logging"""
        if len(secret_value) <= show_chars:
            return '*' * len(secret_value)
        
        return secret_value[:show_chars] + '*' * (len(secret_value) - show_chars)


class SecureConfigLoader:
    """Securely load configuration from environment and secrets"""
    
    @staticmethod
    def load_from_env(config_dict):
        """Load configuration from environment variables"""
        for key, default_value in config_dict.items():
            env_value = os.getenv(key)
            if env_value:
                # Handle boolean values
                if isinstance(default_value, bool):
                    config_dict[key] = env_value.lower() in ('true', '1', 'yes')
                # Handle integer values
                elif isinstance(default_value, int):
                    config_dict[key] = int(env_value)
                else:
                    config_dict[key] = env_value
        
        return config_dict
    
    @staticmethod
    def validate_config(config_dict, required_keys):
        """Validate configuration has required keys"""
        missing = [key for key in required_keys if key not in config_dict]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")


class APIKeyManager:
    """Manage API keys securely"""
    
    def __init__(self, secret_manager=None):
        self.secret_manager = secret_manager or SecretManager()
        self.api_keys = {}
    
    def generate_key(self, service_name, permissions=None):
        """Generate new API key for service"""
        api_key = self.secret_manager.generate_api_key(service_name)
        
        key_info = {
            'service': service_name,
            'permissions': permissions or [],
            'created': __import__('datetime').datetime.utcnow().isoformat(),
            'active': True,
        }
        
        self.api_keys[api_key] = key_info
        return api_key
    
    def revoke_key(self, api_key):
        """Revoke API key"""
        if api_key in self.api_keys:
            self.api_keys[api_key]['active'] = False
            self.api_keys[api_key]['revoked'] = __import__('datetime').datetime.utcnow().isoformat()
    
    def validate_key(self, api_key):
        """Validate API key"""
        if api_key not in self.api_keys:
            return False
        
        key_info = self.api_keys[api_key]
        return key_info.get('active', False)
    
    def get_key_permissions(self, api_key):
        """Get key permissions"""
        if api_key in self.api_keys:
            return self.api_keys[api_key].get('permissions', [])
        return []
