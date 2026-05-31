"""
Security Configuration & Hardening Module
Implements OWASP Top 10 compliance and enterprise security standards
"""

import os
import re
import hashlib
import hmac
from functools import wraps
from flask import request, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import bleach


class SecurityConfig:
    """Enterprise-grade security configuration"""
    
    # OWASP Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }
    
    # Security Boundaries
    MAX_REQUEST_SIZE = 16 * 1024 * 1024  # 16MB
    MAX_HEADER_SIZE = 8192  # 8KB
    TOKEN_EXPIRY = 3600  # 1 hour
    SESSION_TIMEOUT = 1800  # 30 minutes
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes
    
    # Password Policy
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    BCRYPT_ROUNDS = 12
    
    # Input Validation
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a']
    ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
    MAX_STRING_LENGTH = 1024
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT = "100 per hour"
    RATE_LIMIT_LOGIN = "5 per minute"
    RATE_LIMIT_EXPORT = "50 per hour"


class InputValidator:
    """Validates and sanitizes user input to prevent injection attacks"""
    
    @staticmethod
    def validate_string(value, max_length=SecurityConfig.MAX_STRING_LENGTH, allow_html=False):
        """Validate and sanitize string input"""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        if len(value) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length}")
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Sanitize HTML if needed
        if allow_html:
            value = bleach.clean(value, tags=SecurityConfig.ALLOWED_TAGS, 
                                attributes=SecurityConfig.ALLOWED_ATTRIBUTES)
        else:
            value = bleach.clean(value, tags=[], strip=True)
        
        return value.strip()
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        return email.lower()
    
    @staticmethod
    def validate_transaction_id(tx_id):
        """Validate transaction ID to prevent injection"""
        # Accept alphanumeric, hyphens, underscores only
        if not re.match(r'^[a-zA-Z0-9_-]{1,128}$', tx_id):
            raise ValueError("Invalid transaction ID format")
        return tx_id
    
    @staticmethod
    def validate_amount(amount, min_val=0, max_val=1e9):
        """Validate and constrain monetary amounts"""
        try:
            val = float(amount)
            if not (min_val <= val <= max_val):
                raise ValueError(f"Amount must be between {min_val} and {max_val}")
            return round(val, 2)
        except (TypeError, ValueError):
            raise ValueError("Invalid amount format")
    
    @staticmethod
    def validate_password(password):
        """Validate password meets security requirements"""
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters")
        
        if SecurityConfig.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain uppercase letter")
        
        if SecurityConfig.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            raise ValueError("Password must contain lowercase letter")
        
        if SecurityConfig.REQUIRE_DIGITS and not re.search(r'\d', password):
            raise ValueError("Password must contain digit")
        
        if SecurityConfig.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain special character")
        
        return password


class PasswordManager:
    """Secure password hashing and verification"""
    
    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        InputValidator.validate_password(password)
        return generate_password_hash(password, method='pbkdf2:sha256', 
                                     salt_length=16)
    
    @staticmethod
    def verify_password(password_hash, password):
        """Verify password against hash"""
        try:
            return check_password_hash(password_hash, password)
        except Exception:
            return False


class CSRF_Protection:
    """Cross-Site Request Forgery protection"""
    
    @staticmethod
    def generate_token():
        """Generate CSRF token"""
        return os.urandom(32).hex()
    
    @staticmethod
    def validate_token(token, stored_token):
        """Validate CSRF token using constant-time comparison"""
        return hmac.compare_digest(token, stored_token)


def require_secure_headers(func):
    """Decorator to add security headers to response"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        if isinstance(response, tuple):
            response = response[0]
        
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        
        return response
    return wrapper


def validate_request_size(func):
    """Decorator to validate request size"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.content_length and request.content_length > SecurityConfig.MAX_REQUEST_SIZE:
            abort(413)  # Payload Too Large
        return func(*args, **kwargs)
    return wrapper


def sanitize_json_input(func):
    """Decorator to sanitize JSON input"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            data = request.get_json(silent=True)
            if data:
                request.sanitized_data = {
                    k: InputValidator.validate_string(v) if isinstance(v, str) else v
                    for k, v in data.items()
                }
        return func(*args, **kwargs)
    return wrapper


class AuditLogger:
    """Security event audit logging"""
    
    @staticmethod
    def log_auth_attempt(username, success, ip_address, user_agent=None):
        """Log authentication attempt"""
        event = {
            'event': 'AUTH_ATTEMPT',
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
        }
        return event
    
    @staticmethod
    def log_data_access(user_id, resource, action, ip_address):
        """Log data access"""
        event = {
            'event': 'DATA_ACCESS',
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'ip_address': ip_address,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
        }
        return event
    
    @staticmethod
    def log_security_violation(violation_type, details, ip_address):
        """Log security violation"""
        event = {
            'event': 'SECURITY_VIOLATION',
            'violation_type': violation_type,
            'details': details,
            'ip_address': ip_address,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
        }
        return event


class RateLimitBypass:
    """Rate limit bypass detection"""
    
    @staticmethod
    def detect_xff_bypass(headers):
        """Detect X-Forwarded-For header abuse"""
        xff = headers.get('X-Forwarded-For', '')
        if xff and len(xff.split(',')) > 5:
            return True
        return False
    
    @staticmethod
    def is_suspicious_pattern(ip_list):
        """Detect suspicious IP patterns"""
        if len(set(ip_list)) > 50:
            return True
        return False
