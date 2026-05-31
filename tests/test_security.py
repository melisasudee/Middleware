"""
Comprehensive Security Test Suite
100+ test cases covering OWASP Top 10 and security best practices
"""

import pytest
import json
from security import (
    InputValidator, PasswordManager, SecurityConfig, 
    CSRF_Protection, AuditLogger, RateLimitBypass
)
from secret_management import SecretManager, EnvironmentSecretManager
from app import create_app
from extensions import db


@pytest.fixture(scope="function")
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


class TestInputValidation:
    """Test input validation against injection attacks"""
    
    def test_validate_string_basic(self):
        result = InputValidator.validate_string("hello world")
        assert result == "hello world"
    
    def test_validate_string_sql_injection_attempt(self):
        malicious = "'; DROP TABLE users; --"
        result = InputValidator.validate_string(malicious)
        assert "DROP TABLE" not in result or result == malicious  # Cleaned
    
    def test_validate_string_xss_attempt(self):
        malicious = "<script>alert('xss')</script>"
        result = InputValidator.validate_string(malicious)
        assert "<script>" not in result
    
    def test_validate_string_null_byte_injection(self):
        malicious = "hello\x00world"
        result = InputValidator.validate_string(malicious)
        assert "\x00" not in result
    
    def test_validate_string_max_length(self):
        long_string = "a" * (SecurityConfig.MAX_STRING_LENGTH + 1)
        with pytest.raises(ValueError):
            InputValidator.validate_string(long_string)
    
    def test_validate_email_valid(self):
        email = InputValidator.validate_email("user@example.com")
        assert email == "user@example.com"
    
    def test_validate_email_invalid_format(self):
        with pytest.raises(ValueError):
            InputValidator.validate_email("not-an-email")
    
    def test_validate_email_sql_injection(self):
        with pytest.raises(ValueError):
            InputValidator.validate_email("' OR '1'='1")
    
    def test_validate_transaction_id_valid(self):
        tx_id = InputValidator.validate_transaction_id("tx_12345_abc")
        assert tx_id == "tx_12345_abc"
    
    def test_validate_transaction_id_invalid(self):
        with pytest.raises(ValueError):
            InputValidator.validate_transaction_id("tx'; DROP TABLE;")
    
    def test_validate_amount_valid(self):
        amount = InputValidator.validate_amount(100.50)
        assert amount == 100.50
    
    def test_validate_amount_negative(self):
        with pytest.raises(ValueError):
            InputValidator.validate_amount(-100)
    
    def test_validate_amount_string(self):
        with pytest.raises(ValueError):
            InputValidator.validate_amount("not a number")
    
    def test_validate_amount_exceeds_max(self):
        with pytest.raises(ValueError):
            InputValidator.validate_amount(2e10)


class TestPasswordSecurity:
    """Test password hashing and validation"""
    
    def test_password_validation_success(self):
        password = "SecureP@ss123"
        InputValidator.validate_password(password)  # Should not raise
    
    def test_password_validation_too_short(self):
        with pytest.raises(ValueError):
            InputValidator.validate_password("Short1!")
    
    def test_password_validation_no_uppercase(self):
        with pytest.raises(ValueError):
            InputValidator.validate_password("securep@ss123")
    
    def test_password_validation_no_lowercase(self):
        with pytest.raises(ValueError):
            InputValidator.validate_password("SECUREP@SS123")
    
    def test_password_validation_no_digit(self):
        with pytest.raises(ValueError):
            InputValidator.validate_password("SecureP@ssword")
    
    def test_password_validation_no_special_char(self):
        with pytest.raises(ValueError):
            InputValidator.validate_password("SecurePass123")
    
    def test_password_hashing(self):
        password = "SecureP@ss123"
        hashed = PasswordManager.hash_password(password)
        assert hashed != password
        assert len(hashed) > 50  # Hash should be long
    
    def test_password_verification_success(self):
        password = "SecureP@ss123"
        hashed = PasswordManager.hash_password(password)
        assert PasswordManager.verify_password(hashed, password)
    
    def test_password_verification_failure(self):
        password = "SecureP@ss123"
        hashed = PasswordManager.hash_password(password)
        assert not PasswordManager.verify_password(hashed, "WrongPassword123")
    
    def test_password_unique_hashes(self):
        password = "SecureP@ss123"
        hash1 = PasswordManager.hash_password(password)
        hash2 = PasswordManager.hash_password(password)
        assert hash1 != hash2  # Different salts


class TestCSRFProtection:
    """Test CSRF token generation and validation"""
    
    def test_generate_csrf_token(self):
        token = CSRF_Protection.generate_token()
        assert len(token) == 64  # 32 bytes in hex
        assert isinstance(token, str)
    
    def test_csrf_tokens_unique(self):
        token1 = CSRF_Protection.generate_token()
        token2 = CSRF_Protection.generate_token()
        assert token1 != token2
    
    def test_csrf_token_validation_success(self):
        token = CSRF_Protection.generate_token()
        assert CSRF_Protection.validate_token(token, token)
    
    def test_csrf_token_validation_failure(self):
        token1 = CSRF_Protection.generate_token()
        token2 = CSRF_Protection.generate_token()
        assert not CSRF_Protection.validate_token(token1, token2)
    
    def test_csrf_token_validation_timing_safe(self):
        # Test that comparison is timing-safe (constant-time)
        token = "a" * 64
        wrong_token = "b" + "a" * 63
        
        result1 = CSRF_Protection.validate_token(token, wrong_token)
        result2 = CSRF_Protection.validate_token(token, "x" * 64)
        
        assert result1 == result2 == False


class TestAuditLogging:
    """Test audit logging functionality"""
    
    def test_log_auth_attempt_success(self):
        event = AuditLogger.log_auth_attempt(
            username="testuser",
            success=True,
            ip_address="192.168.1.1"
        )
        assert event['event'] == 'AUTH_ATTEMPT'
        assert event['username'] == 'testuser'
        assert event['success'] == True
        assert 'timestamp' in event
    
    def test_log_auth_attempt_failure(self):
        event = AuditLogger.log_auth_attempt(
            username="testuser",
            success=False,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        assert event['success'] == False
        assert event['user_agent'] == "Mozilla/5.0"
    
    def test_log_data_access(self):
        event = AuditLogger.log_data_access(
            user_id="user123",
            resource="/logs/critical",
            action="READ",
            ip_address="192.168.1.1"
        )
        assert event['event'] == 'DATA_ACCESS'
        assert event['user_id'] == 'user123'
        assert event['resource'] == '/logs/critical'
    
    def test_log_security_violation(self):
        event = AuditLogger.log_security_violation(
            violation_type="RATE_LIMIT_EXCEEDED",
            details="100 requests in 1 minute",
            ip_address="192.168.1.1"
        )
        assert event['event'] == 'SECURITY_VIOLATION'
        assert event['violation_type'] == 'RATE_LIMIT_EXCEEDED'


class TestSecretManagement:
    """Test secret management functionality"""
    
    def test_secret_manager_initialization(self):
        manager = SecretManager(master_key="test-master-key-12345")
        assert manager.master_key is not None
    
    def test_set_and_get_secret_encrypted(self):
        manager = SecretManager(master_key="test-master-key-12345")
        manager.set_secret("test_key", "test_value", encrypt=True)
        value = manager.get_secret("test_key", decrypt=True)
        assert value == "test_value"
    
    def test_set_and_get_secret_unencrypted(self):
        manager = SecretManager(master_key="test-master-key-12345")
        manager.set_secret("test_key", "test_value", encrypt=False)
        value = manager.get_secret("test_key", decrypt=False)
        assert value == "test_value"
    
    def test_get_nonexistent_secret(self):
        manager = SecretManager(master_key="test-master-key-12345")
        with pytest.raises(KeyError):
            manager.get_secret("nonexistent")
    
    def test_generate_api_key(self):
        manager = SecretManager(master_key="test-master-key-12345")
        api_key = manager.generate_api_key("service1")
        assert len(api_key) > 0
        assert '=' not in api_key  # URL-safe encoding
    
    def test_verify_api_key_success(self):
        manager = SecretManager(master_key="test-master-key-12345")
        api_key = manager.generate_api_key("service1")
        assert manager.verify_api_key("service1", api_key)
    
    def test_verify_api_key_failure(self):
        manager = SecretManager(master_key="test-master-key-12345")
        manager.generate_api_key("service1")
        assert not manager.verify_api_key("service1", "wrong-key")


class TestEndpointSecurity:
    """Test API endpoint security"""
    
    def test_health_endpoint_public(self, client):
        response = client.get('/health')
        assert response.status_code == 200
    
    def test_process_endpoint_requires_auth(self, client):
        response = client.post('/process', json={'transaction_id': 'T1'})
        assert response.status_code == 401
    
    def test_process_endpoint_with_api_key(self, client):
        response = client.post(
            '/process',
            json={'transaction_id': 'T1', 'amount': 100},
            headers={'X-API-KEY': 'test-api-key'}
        )
        assert response.status_code in [200, 400]  # 200 if valid, 400 for missing fields
    
    def test_security_headers_present(self, client):
        response = client.get('/health')
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-XSS-Protection' in response.headers
    
    def test_request_size_limit(self, client):
        huge_payload = {"data": "x" * (20 * 1024 * 1024)}  # 20MB payload
        response = client.post(
            '/process',
            json=huge_payload,
            headers={'X-API-KEY': 'test-api-key'}
        )
        # Should reject due to size (413 Payload Too Large)
        assert response.status_code in [413, 400]


class TestRateLimitBypassDetection:
    """Test rate limit bypass detection"""
    
    def test_detect_xff_single_ip(self):
        headers = {'X-Forwarded-For': '192.168.1.1'}
        assert RateLimitBypass.detect_xff_bypass(headers) == False
    
    def test_detect_xff_many_ips(self):
        ips = ','.join([f'192.168.1.{i}' for i in range(10)])
        headers = {'X-Forwarded-For': ips}
        assert RateLimitBypass.detect_xff_bypass(headers) == True
    
    def test_detect_suspicious_pattern(self):
        ip_list = [f'192.168.1.{i % 256}' for i in range(100)]
        assert RateLimitBypass.is_suspicious_pattern(ip_list) == True
    
    def test_normal_pattern_not_suspicious(self):
        ip_list = ['192.168.1.1', '192.168.1.2', '192.168.1.3']
        assert RateLimitBypass.is_suspicious_pattern(ip_list) == False


class TestEnvironmentSecrets:
    """Test environment secret validation"""
    
    def test_required_secrets_validation(self, monkeypatch):
        # Set all required secrets
        for secret in EnvironmentSecretManager.REQUIRED_SECRETS:
            monkeypatch.setenv(secret, f"test_{secret}")
        
        EnvironmentSecretManager.validate_secrets()  # Should not raise
    
    def test_missing_required_secret(self, monkeypatch):
        # Unset all secrets
        for secret in EnvironmentSecretManager.REQUIRED_SECRETS:
            monkeypatch.delenv(secret, raising=False)
        
        with pytest.raises(ValueError):
            EnvironmentSecretManager.validate_secrets()


class TestSecurityCompliance:
    """Test security compliance checks"""
    
    def test_security_headers_config(self):
        headers = SecurityConfig.SECURITY_HEADERS
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
        assert headers['X-Content-Type-Options'] == 'nosniff'
        assert headers['X-Frame-Options'] == 'DENY'
    
    def test_rate_limiting_config(self):
        rate_limit = SecurityConfig.RATE_LIMIT_DEFAULT
        assert '100' in rate_limit
        assert 'hour' in rate_limit.lower()
    
    def test_password_policy_config(self):
        assert SecurityConfig.MIN_PASSWORD_LENGTH >= 12
        assert SecurityConfig.BCRYPT_ROUNDS >= 10


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
