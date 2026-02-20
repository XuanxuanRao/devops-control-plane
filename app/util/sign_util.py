import json
import base64
import logging
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RSASigner")


def _build_sorted_json(params: Dict[str, Any]) -> bytes:
    json_str = json.dumps(params, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return json_str.encode("utf-8")


class RSASigner:
    def __init__(self, private_key_path: str = "", public_key_path: str = "", enabled: bool = True):
        self._enabled = enabled
        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._public_key: Optional[rsa.RSAPublicKey] = None

        # 加载私钥
        if private_key_path:
            try:
                with open(private_key_path, "rb") as key_file:
                    self._private_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None,
                    )
            except Exception as e:
                logger.warning(f"Failed to load private key: {e}")

        # 加载公钥
        if public_key_path:
            try:
                with open(public_key_path, "rb") as key_file:
                    self._public_key = serialization.load_pem_public_key(
                        key_file.read()
                    )
            except Exception as e:
                logger.warning(f"Failed to load public key: {e}")

    def sign(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        if not self._enabled or not self._private_key:
            return ""

        # 1. 序列化
        sign_content = _build_sorted_json(params)

        # 2. 签名 (使用 PKCS1v15 填充和 SHA256 算法)
        signature = self._private_key.sign(
            sign_content,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        # 3. Base64 编码
        return base64.b64encode(signature).decode('utf-8')

    def verify(self, params: Dict[str, Any], signature_str: str) -> bool:
        """验证签名"""
        if not self._enabled or not self._public_key:
            return True

        if not signature_str:
            raise ValueError("missing signature")

        try:
            # 1. 序列化
            sign_content = _build_sorted_json(params)

            # 2. 解码签名
            signature_bytes = base64.b64decode(signature_str)

            # 3. 验证
            self._public_key.verify(
                signature_bytes,
                sign_content,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except (InvalidSignature, Exception) as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def enabled(self) -> bool:
        return self._enabled


def load_public_key_from_pem(pem_str: str) -> Optional[rsa.RSAPublicKey]:
    if not pem_str:
        return None
    try:
        key_bytes = pem_str.encode("utf-8")
        return serialization.load_pem_public_key(key_bytes)
    except Exception as e:
        logger.warning(f"Failed to load public key from pem: {e}")
        return None


def verify_with_public_key(
    params: Dict[str, Any],
    signature_str: str,
    public_key: Optional[rsa.RSAPublicKey],
    enabled: bool = True,
) -> bool:
    if not enabled:
        return True
    if not public_key:
        return False
    if not signature_str:
        raise ValueError("missing signature")
    try:
        sign_content = _build_sorted_json(params)
        signature_bytes = base64.b64decode(signature_str)
        public_key.verify(
            signature_bytes,
            sign_content,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except (InvalidSignature, Exception) as e:
        logger.error(f"Signature verification failed: {e}")
        return False

# --- 使用示例 ---
if __name__ == "__main__":
    # 假设你已经有了 pem 文件
    signer = RSASigner(private_key_path="/Users/rcx/code/python/devops-control-plane/private.pem",
                       public_key_path="/Users/rcx/code/python/devops-control-plane/public-server.pem")
    data = {"id": 1, "name": "test", "meta": {"active": True}}
    sig = signer.sign(data)
    is_valid = signer.verify(data, sig)
    pass
