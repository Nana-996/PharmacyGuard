"""
PharmacyGuard Demonstration Environment Guardrails.
Provides:
1. In-memory IP-based sliding-window rate limiting (protects against denial of service / script spam).
2. Per-session / per-IP AI agent invocation quotas (protects AWS Bedrock API credits in public demos).
3. Synthetic patient data validation (strictly blocks arbitrary external PHI/PII entry).
"""

import os
import time
import logging
from typing import Dict, List, Tuple, Optional, Set
from fastapi import Request, HTTPException, status

logger = logging.getLogger("pharmacyguard.security")

# -----------------------------------------------------------------------------
# Configuration Flags (Environment-driven with safe demo defaults)
# -----------------------------------------------------------------------------
DEMO_RATE_LIMIT_ENABLED: bool = os.getenv("DEMO_RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
DEMO_MAX_REQ_PER_MINUTE: int = int(os.getenv("DEMO_MAX_REQ_PER_MINUTE", "60"))
DEMO_MAX_AGENT_CALLS_PER_SESSION: int = int(os.getenv("DEMO_MAX_AGENT_CALLS_PER_SESSION", "20"))
DEMO_RESTRICT_ARBITRARY_PATIENTS: bool = os.getenv("DEMO_RESTRICT_ARBITRARY_PATIENTS", "true").lower() in ("true", "1", "yes")


# -----------------------------------------------------------------------------
# Curated Synthetic Patient Registry (PHI Prevention Barrier)
# -----------------------------------------------------------------------------
KNOWN_SYNTHETIC_PATIENT_IDS: Set[str] = {
    "PAT-101",
    "PAT-102",
    "PAT-103",
    "PAT-104",
    "PAT-105",
    "PAT-106",
    "PAT-107",
    "PAT-108",
    "PAT-109",
    "PAT-110",
}

KNOWN_SYNTHETIC_PATIENT_NAMES: Set[str] = {
    "john doe",
    "jane smith",
    "robert taylor",
    "emily davis",
    "michael chen",
    "kwame mensah",
    "abena asante",
    "esi mensah",
    "akua boateng",
    "sarah connor",
    "david brown",
    "maria garcia",
    "alex reed",
}


def is_approved_synthetic_patient(patient_id: Optional[str] = None, patient_name: Optional[str] = None) -> bool:
    """
    Validates whether a patient record corresponds to the known synthetic hospital compendium.
    Returns True if approved, False if arbitrary non-synthetic.
    """
    if not DEMO_RESTRICT_ARBITRARY_PATIENTS:
        return True

    if patient_id and patient_id.strip().upper() in KNOWN_SYNTHETIC_PATIENT_IDS:
        return True

    if patient_name:
        clean_name = patient_name.strip().lower()
        for known in KNOWN_SYNTHETIC_PATIENT_NAMES:
            if known in clean_name or clean_name in known:
                return True

    return False


def get_client_identifier(request: Request) -> str:
    """Extracts a stable client identifier using X-Forwarded-For, client host, or authorization token."""
    # Check for authorization header (user session)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Use token slice as session identifier
        token = auth_header.split(" ", 1)[1].strip()
        if len(token) > 16:
            return f"session:{token[-16:]}"

    # Check for reverse proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return f"ip:{client_ip}"

    # Fall back to client host
    client_host = request.client.host if request.client else "127.0.0.1"
    return f"ip:{client_host}"


# -----------------------------------------------------------------------------
# In-Memory Sliding-Window Rate Limiter
# -----------------------------------------------------------------------------
class DemoRateLimiter:
    def __init__(self, max_requests_per_minute: int = DEMO_MAX_REQ_PER_MINUTE):
        self.max_requests = max_requests_per_minute
        self.window_seconds = 60.0
        self._ip_history: Dict[str, List[float]] = {}

    def check_rate_limit(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Checks if the client is within the allowed request rate.
        Returns: (is_allowed, requests_in_window, remaining_requests)
        """
        if not DEMO_RATE_LIMIT_ENABLED:
            return True, 0, self.max_requests

        now = time.time()
        cutoff = now - self.window_seconds

        history = self._ip_history.get(client_id, [])
        # Purge timestamps outside the 60s sliding window
        valid_history = [t for t in history if t > cutoff]

        if len(valid_history) >= self.max_requests:
            self._ip_history[client_id] = valid_history
            return False, len(valid_history), 0

        valid_history.append(now)
        self._ip_history[client_id] = valid_history
        remaining = max(0, self.max_requests - len(valid_history))
        return True, len(valid_history), remaining

    def reset(self):
        """Clears in-memory history (useful for test isolation)."""
        self._ip_history.clear()


# -----------------------------------------------------------------------------
# Demo AI Agent Invocation Quota Tracker
# -----------------------------------------------------------------------------
class DemoAgentQuotaTracker:
    def __init__(self, max_calls_per_session: int = DEMO_MAX_AGENT_CALLS_PER_SESSION):
        self.max_quota = max_calls_per_session
        self._session_usage: Dict[str, int] = {}

    def get_quota(self, client_id: str) -> Dict[str, int]:
        """Returns the current usage and remaining quota for a client session."""
        used = self._session_usage.get(client_id, 0)
        remaining = max(0, self.max_quota - used)
        return {
            "max_quota": self.max_quota,
            "used": used,
            "remaining": remaining,
            "quota_exhausted": remaining <= 0,
        }

    def check_and_consume(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Checks if an agent invocation is permitted and increments the counter.
        Returns: (is_allowed, used_count, remaining_count)
        """
        if not DEMO_RATE_LIMIT_ENABLED:
            return True, 0, self.max_quota

        used = self._session_usage.get(client_id, 0)
        if used >= self.max_quota:
            return False, used, 0

        used += 1
        self._session_usage[client_id] = used
        remaining = max(0, self.max_quota - used)
        return True, used, remaining

    def reset(self):
        """Clears in-memory quota usage (useful for test isolation)."""
        self._session_usage.clear()


# Global Singleton Instances
demo_rate_limiter = DemoRateLimiter()
demo_quota_tracker = DemoAgentQuotaTracker()
