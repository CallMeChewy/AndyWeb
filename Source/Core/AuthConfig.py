# File: AuthConfig.py
# Path: /home/herb/Desktop/AndyWeb/Source/Core/AuthConfig.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-25
# Last Modified: 2025-07-25 09:00AM

"""
Authentication Configuration for BowersWorld.com
Centralized configuration management for authentication and security settings
"""

from datetime import timedelta
from typing import Dict, Any
import os

class AuthConfig:
    """
    Authentication configuration for BowersWorld.com educational platform
    Supports both development and production environments
    """
    
    # ==================== SECURITY SETTINGS ====================
    
    # Password Requirements
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 100
    PASSWORD_REQUIRE_UPPERCASE = False  # Keep accessible for students
    PASSWORD_REQUIRE_LOWERCASE = False
    PASSWORD_REQUIRE_NUMBERS = False
    PASSWORD_REQUIRE_SYMBOLS = False
    
    # Account Lockout Protection
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(hours=1)
    LOCKOUT_RESET_ON_SUCCESS = True
    
    # Session Management
    SESSION_EXPIRY = timedelta(hours=24)  # 24 hour sessions
    REFRESH_TOKEN_EXPIRY = timedelta(days=30)  # 30 day refresh
    ALLOW_CONCURRENT_SESSIONS = True  # Students may use multiple devices
    MAX_SESSIONS_PER_USER = 5
    
    # Token Security
    TOKEN_LENGTH = 32  # bytes for token generation
    TOKEN_ALGORITHM = "HS256"
    SESSION_SECRET_KEY = os.getenv('SESSION_SECRET_KEY', 'dev-secret-change-in-production')
    
    # ==================== SUBSCRIPTION TIER LIMITS ====================
    
    SUBSCRIPTION_LIMITS = {
        'guest': {
            'downloads_per_day': 0,
            'search_results_limit': 10,
            'features': ['browse', 'search_limited'],
            'concurrent_sessions': 1,
            'monthly_cost': 0.00
        },
        'free': {
            'downloads_per_day': 3,
            'search_results_limit': 25,
            'features': ['browse', 'search', 'download_limited'],
            'concurrent_sessions': 2,
            'monthly_cost': 0.00
        },
        'scholar': {
            'downloads_per_day': 10,
            'search_results_limit': 100,
            'features': ['browse', 'search', 'download', 'notes', 'bookmarks'],
            'concurrent_sessions': 3,
            'monthly_cost': 9.99
        },
        'researcher': {
            'downloads_per_day': 50,
            'search_results_limit': 500,
            'features': ['browse', 'search', 'download', 'notes', 'bookmarks', 'advanced_search', 'export', 'citations'],
            'concurrent_sessions': 5,
            'monthly_cost': 19.99
        },
        'institution': {
            'downloads_per_day': -1,  # unlimited
            'search_results_limit': -1,  # unlimited
            'features': ['browse', 'search', 'download', 'notes', 'bookmarks', 'advanced_search', 'export', 'citations', 'bulk_operations', 'admin', 'analytics'],
            'concurrent_sessions': 25,
            'monthly_cost': 99.00
        }
    }
    
    # ==================== RATE LIMITING ====================
    
    RATE_LIMITS = {
        'registration': {
            'requests_per_minute': 3,
            'requests_per_hour': 10,
            'burst_limit': 5
        },
        'login': {
            'requests_per_minute': 10,
            'requests_per_hour': 30,
            'burst_limit': 15
        },
        'api_general': {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'burst_limit': 100
        },
        'download': {
            'requests_per_minute': 5,
            'requests_per_hour': 50,
            'burst_limit': 10
        }
    }
    
    # ==================== EMAIL SETTINGS ====================
    
    EMAIL_CONFIG = {
        'verification_required': True,
        'verification_expiry': timedelta(hours=24),
        'from_address': 'noreply@bowersworld.com',
        'from_name': 'BowersWorld.com Educational Platform',
        'smtp_host': os.getenv('SMTP_HOST'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'smtp_username': os.getenv('SMTP_USERNAME'),
        'smtp_password': os.getenv('SMTP_PASSWORD'),
        'use_tls': True
    }
    
    # ==================== EDUCATIONAL MISSION SETTINGS ====================
    
    EDUCATIONAL_CONFIG = {
        'mission_statement': "Getting education into the hands of people who can least afford it",
        'free_tier_always_available': True,
        'guest_access_enabled': True,
        'student_discount_available': True,
        'developing_nation_pricing': {
            'scholar': 4.99,
            'researcher': 9.99,
            'institution': 49.99
        },
        'accessibility_features_enabled': True
    }
    
    # ==================== ENVIRONMENT-SPECIFIC SETTINGS ====================
    
    @classmethod
    def GetEnvironmentConfig(cls) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        
        if environment == 'production':
            return cls._GetProductionConfig()
        elif environment == 'staging':
            return cls._GetStagingConfig()
        else:
            return cls._GetDevelopmentConfig()
    
    @classmethod
    def _GetDevelopmentConfig(cls) -> Dict[str, Any]:
        """Development environment configuration"""
        return {
            'debug_mode': True,
            'log_level': 'DEBUG',
            'session_expiry': timedelta(hours=48),  # Longer for development
            'rate_limiting_enabled': False,
            'email_verification_required': False,
            'cors_origins': ['*'],
            'database_echo': True
        }
    
    @classmethod
    def _GetStagingConfig(cls) -> Dict[str, Any]:
        """Staging environment configuration"""
        return {
            'debug_mode': False,
            'log_level': 'INFO',
            'session_expiry': cls.SESSION_EXPIRY,
            'rate_limiting_enabled': True,
            'email_verification_required': True,
            'cors_origins': ['https://staging.bowersworld.com'],
            'database_echo': False
        }
    
    @classmethod
    def _GetProductionConfig(cls) -> Dict[str, Any]:
        """Production environment configuration"""
        return {
            'debug_mode': False,
            'log_level': 'WARNING',
            'session_expiry': cls.SESSION_EXPIRY,
            'rate_limiting_enabled': True,
            'email_verification_required': True,
            'cors_origins': ['https://bowersworld.com', 'https://www.bowersworld.com'],
            'database_echo': False,
            'security_headers_enabled': True,
            'session_secure_cookies': True
        }
    
    # ==================== VALIDATION METHODS ====================
    
    @classmethod
    def ValidateSubscriptionTier(cls, tier: str) -> bool:
        """Validate if subscription tier is valid"""
        return tier in cls.SUBSCRIPTION_LIMITS
    
    @classmethod
    def GetSubscriptionFeatures(cls, tier: str) -> list:
        """Get features available for subscription tier"""
        return cls.SUBSCRIPTION_LIMITS.get(tier, {}).get('features', [])
    
    @classmethod
    def GetSubscriptionLimit(cls, tier: str, limit_type: str) -> int:
        """Get specific limit for subscription tier"""
        return cls.SUBSCRIPTION_LIMITS.get(tier, {}).get(limit_type, 0)
    
    @classmethod
    def CanAccessFeature(cls, tier: str, feature: str) -> bool:
        """Check if subscription tier can access specific feature"""
        features = cls.GetSubscriptionFeatures(tier)
        return feature in features
    
    # ==================== SECURITY HELPERS ====================
    
    @classmethod
    def IsPasswordValid(cls, password: str) -> tuple[bool, str]:
        """Validate password against security requirements"""
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters"
        
        if len(password) > cls.PASSWORD_MAX_LENGTH:
            return False, f"Password must be no more than {cls.PASSWORD_MAX_LENGTH} characters"
        
        # Additional checks can be added here based on requirements
        return True, "Password is valid"
    
    @classmethod
    def GetSecurityHeaders(cls) -> Dict[str, str]:
        """Get security headers for web responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        }