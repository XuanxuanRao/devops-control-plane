import threading
from typing import Dict, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.orm import Session

from app import crud
from app.util.sign_util import load_public_key_from_pem


class PublicKeyStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: Dict[str, Tuple[str, rsa.RSAPublicKey]] = {}

    def get_public_key(self, db: Session, hostname: str) -> Optional[rsa.RSAPublicKey]:
        if not hostname:
            return None
        record = crud.get_client_public_key(db, hostname)
        if not record:
            return None
        pem = record.public_key_pem
        with self._lock:
            cached = self._cache.get(hostname)
            if cached and cached[0] == pem:
                return cached[1]
        public_key = load_public_key_from_pem(pem)
        if public_key:
            with self._lock:
                self._cache[hostname] = (pem, public_key)
        return public_key
