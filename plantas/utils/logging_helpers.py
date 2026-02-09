"""
Helper functions for logging and audit trail.
"""


def sanitize_for_logging(data, sensitive_fields=None):
    """
    Sanitize sensitive data before logging.
    
    Args:
        data: Dictionary or object to sanitize
        sensitive_fields: List of field names to redact (default: common sensitive fields)
    
    Returns:
        Sanitized copy of data with sensitive fields masked
    """
    if sensitive_fields is None:
        sensitive_fields = [
            'password', 'token', 'access_token', 'refresh_token',
            'secret', 'api_key', 'authorization', 'cookie'
        ]
    
    if not isinstance(data, dict):
        return data
    
    sanitized = data.copy()
    for field in sensitive_fields:
        if field in sanitized:
            # Keep first 8 characters for debugging, mask the rest
            value = str(sanitized[field])
            if len(value) > 8:
                sanitized[field] = value[:8] + '...[REDACTED]'
            else:
                sanitized[field] = '[REDACTED]'
    
    return sanitized


def get_client_ip(request):
    """
    Extract client IP address from request, handling proxies.
    
    Args:
        request: Django request object
    
    Returns:
        IP address as string, or None if unable to determine
    """
    # Check X-Forwarded-For header (set by proxies like Render)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the list (the original client)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # Fallback to REMOTE_ADDR
        ip = request.META.get('REMOTE_ADDR')
    
    return ip


def get_user_agent(request):
    """
    Extract User-Agent from request.
    
    Args:
        request: Django request object
    
    Returns:
        User-Agent string, or empty string if not present
    """
    return request.META.get('HTTP_USER_AGENT', '')
