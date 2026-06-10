# backend/app/api/rate_limit.py
"""Rate limiting utilities using slowapi.
We expose a `limiter` instance that can be imported by route modules.
The limit policy is set to 5 requests per minute per client IP for
chat‑related endpoints. Adjust the rule as needed.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# 5 requests per minute per IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])

# Exported so FastAPI can register the global exception handler
rate_limit_exceeded_handler = _rate_limit_exceeded_handler
