import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class AuditService:
    """Lightweight audit logger that emits structured JSON logs.
    This avoids DB schema changes while still providing useful traceability.
    """

    _logger = logging.getLogger("audit")

    @staticmethod
    def log_action(
        action: str,
        entity_type: str,
        entity_id: str,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            payload = {
                "ts": datetime.now(timezone.utc)().isoformat(),
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "actor_id": actor_id,
                "actor_role": actor_role,
                "metadata": metadata or {},
            }
            AuditService._logger.info(json.dumps(payload))
        except Exception as e:
            # Never raise from audit logging
            logging.getLogger(__name__).warning(f"Audit log failed: {e}")
