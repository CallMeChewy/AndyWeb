# File: RateLimiter.py
# Path: /home/herb/Desktop/AndyWeb/Source/Core/RateLimiter.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-25
# Last Modified: 2025-07-25 09:10AM

"""
Rate Limiting for BowersWorld.com API endpoints
Implements token bucket algorithm for API rate limiting
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import threading
from .AuthConfig import AuthConfig

class RateLimiter:
    """
    Token bucket rate limiter for BowersWorld.com
    Protects authentication endpoints from abuse while preserving educational access
    """
    
    def __init__(self):
        """Initialize rate limiter with educational mission focus"""
        self.buckets: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.cleanup_lock = threading.Lock()
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
    def _get_bucket_key(self, identifier: str, endpoint: str) -> str:
        """Generate bucket key for rate limiting"""
        return f"{endpoint}:{identifier}"
    
    def _cleanup_expired_buckets(self):
        """Clean up expired rate limit buckets"""
        with self.cleanup_lock:
            current_time = time.time()
            
            # Only cleanup every 5 minutes
            if current_time - self.last_cleanup < self.cleanup_interval:
                return
            
            expired_keys = []
            for key, bucket in self.buckets.items():
                if current_time - bucket.get('last_refill', 0) > 3600:  # 1 hour
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.buckets[key]
            
            self.last_cleanup = current_time
    
    def _refill_bucket(self, bucket: Dict[str, Any], rate_config: Dict[str, int]):
        """Refill token bucket based on time elapsed"""
        current_time = time.time()
        last_refill = bucket.get('last_refill', current_time)
        time_elapsed = current_time - last_refill
        
        # Refill tokens based on requests per minute
        tokens_to_add = int(time_elapsed * rate_config['requests_per_minute'] / 60.0)
        
        if tokens_to_add > 0:
            bucket['tokens'] = min(
                rate_config['burst_limit'],
                bucket.get('tokens', 0) + tokens_to_add
            )
            bucket['last_refill'] = current_time
    
    def is_allowed(self, identifier: str, endpoint: str, request_count: int = 1) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed under rate limits
        
        Args:
            identifier: IP address or user ID for rate limiting
            endpoint: API endpoint being accessed
            request_count: Number of tokens to consume (default 1)
            
        Returns:
            (allowed, rate_limit_info)
        """
        # Clean up old buckets periodically
        self._cleanup_expired_buckets()
        
        # Get rate configuration for endpoint
        rate_config = self._get_rate_config(endpoint)
        if not rate_config:
            return True, {}  # No rate limiting configured
        
        # Get or create bucket
        bucket_key = self._get_bucket_key(identifier, endpoint)
        bucket = self.buckets[bucket_key]
        
        # Initialize bucket if new
        if 'tokens' not in bucket:
            bucket['tokens'] = rate_config['burst_limit']
            bucket['last_refill'] = time.time()
        
        # Refill bucket
        self._refill_bucket(bucket, rate_config)
        
        # Check if request is allowed
        if bucket['tokens'] >= request_count:
            bucket['tokens'] -= request_count
            return True, {
                'remaining': bucket['tokens'],
                'reset_time': bucket['last_refill'] + 60,  # Next minute
                'limit': rate_config['requests_per_minute']
            }
        else:
            # Calculate retry after time
            retry_after = 60 - (time.time() - bucket['last_refill'])
            return False, {
                'remaining': 0,
                'reset_time': bucket['last_refill'] + 60,
                'limit': rate_config['requests_per_minute'],
                'retry_after': max(1, int(retry_after))
            }
    
    def _get_rate_config(self, endpoint: str) -> Optional[Dict[str, int]]:
        """Get rate configuration for specific endpoint"""
        endpoint_mapping = {
            '/api/auth/register': 'registration',
            '/api/auth/login': 'login',
            '/api/books': 'api_general',
            '/api/books/search': 'api_general',
            '/api/books/filter': 'api_general',
            '/api/books/*/pdf': 'download',
            '/api/books/*/thumbnail': 'api_general'
        }
        
        # Find matching endpoint pattern
        rate_limit_type = None
        for pattern, limit_type in endpoint_mapping.items():
            if '*' in pattern:
                # Simple wildcard matching
                pattern_parts = pattern.split('*')
                if len(pattern_parts) == 2:
                    if endpoint.startswith(pattern_parts[0]) and endpoint.endswith(pattern_parts[1]):
                        rate_limit_type = limit_type
                        break
            else:
                if endpoint == pattern:
                    rate_limit_type = limit_type
                    break
        
        if not rate_limit_type:
            rate_limit_type = 'api_general'  # Default
        
        return AuthConfig.RATE_LIMITS.get(rate_limit_type)
    
    def get_usage_stats(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit usage statistics for identifier"""
        stats = {}
        current_time = time.time()
        
        for bucket_key, bucket in self.buckets.items():
            if bucket_key.endswith(f":{identifier}"):
                endpoint = bucket_key.split(':')[0]
                rate_config = self._get_rate_config(endpoint)
                
                if rate_config:
                    # Refill bucket to get current state
                    self._refill_bucket(bucket, rate_config)
                    
                    stats[endpoint] = {
                        'remaining': bucket['tokens'],
                        'limit': rate_config['requests_per_minute'],
                        'reset_time': bucket['last_refill'] + 60
                    }
        
        return stats

# Global rate limiter instance
_rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _rate_limiter