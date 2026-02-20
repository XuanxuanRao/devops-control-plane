#!/usr/bin/env python3
"""
Test script to verify sign_util integration with mq.py
"""

from app.util.sign_util import RSASigner
import json
from datetime import datetime, timezone


def test_sign_util_basic():
    """Test basic sign_util functionality"""
    print('=== Testing sign_util basic functionality ===')
    
    # Create signer
    signer = RSASigner(
        private_key_path="/Users/rcx/code/python/devops-control-plane/private.pem",
        public_key_path="/Users/rcx/code/python/devops-control-plane/public-server.pem",
        enabled=True
    )
    
    # Test message data
    timestamp = int(datetime.now(timezone.utc).timestamp())
    hostname = "test-server"
    
    # Prepare sign data
    sign_data = {
        "hostname": hostname,
        "timestamp": timestamp
    }
    
    print(f"Sign data: {sign_data}")
    
    # Sign the data
    signature = signer.sign(sign_data)
    print(f"Signature: {signature[:50]}...")
    
    if not signature:
        print("❌ Failed to generate signature")
        return False
    
    # Verify the signature
    verified = signer.verify(sign_data, signature)
    print(f"Verification result: {verified}")
    
    if verified:
        print("🎉 Signature verification successful!")
        return True
    else:
        print("❌ Signature verification failed")
        return False


def test_sign_util_with_message():
    """Test sign_util with actual message format"""
    print('\n=== Testing sign_util with message format ===')
    
    # Create signer
    signer = RSASigner(
        private_key_path="/Users/rcx/code/python/devops-control-plane/private.pem",
        public_key_path="/Users/rcx/code/python/devops-control-plane/public-server.pem",
        enabled=True
    )
    
    # Test message
    test_message = {
        "hostname": "test-server",
        "status": "online",
        "cpu_usage": 45.5,
        "mem_usage": 60.2
    }
    
    # Generate timestamp
    timestamp = int(datetime.now(timezone.utc).timestamp())
    
    # Prepare sign data (same as mq.py does)
    hostname = test_message.get('hostname', '')
    sign_data = {
        "hostname": hostname,
        "timestamp": timestamp
    }
    
    print(f"Message: {test_message}")
    print(f"Sign data: {sign_data}")
    
    # Sign the data
    signature = signer.sign(sign_data)
    print(f"Signature: {signature[:50]}...")
    
    if not signature:
        print("❌ Failed to generate signature")
        return False
    
    # Verify the signature
    verified = signer.verify(sign_data, signature)
    print(f"Verification result: {verified}")
    
    if verified:
        print("🎉 Message signature verification successful!")
        return True
    else:
        print("❌ Message signature verification failed")
        return False


def test_sign_util_timestamp_mismatch():
    """Test timestamp mismatch detection"""
    print('\n=== Testing sign_util timestamp mismatch ===')
    
    # Create signer
    signer = RSASigner(
        private_key_path="/Users/rcx/code/python/devops-control-plane/private.pem",
        public_key_path="/Users/rcx/code/python/devops-control-plane/public-agent.pem",
        enabled=True
    )
    
    # Test data
    hostname = "test-server"
    timestamp = int(datetime.now(timezone.utc).timestamp())
    
    # Sign with original timestamp
    sign_data = {
        "hostname": hostname,
        "timestamp": timestamp
    }
    
    signature = signer.sign(sign_data)
    print(f"Original timestamp: {timestamp}")
    print(f"Signature: {signature[:50]}...")
    
    # Verify with different timestamp
    wrong_sign_data = {
        "hostname": hostname,
        "timestamp": timestamp + 1
    }
    
    verified = signer.verify(wrong_sign_data, signature)
    print(f"Verification with wrong timestamp: {verified}")
    
    if not verified:
        print("🎉 Timestamp mismatch correctly detected!")
        return True
    else:
        print("❌ Timestamp mismatch not detected")
        return False


def test_sign_util_hostname_mismatch():
    """Test hostname mismatch detection"""
    print('\n=== Testing sign_util hostname mismatch ===')
    
    # Create signer
    signer = RSASigner(
        private_key_path="/Users/rcx/code/python/devops-control-plane/private.pem",
        public_key_path="/Users/rcx/code/python/devops-control-plane/public-agent.pem",
        enabled=True
    )
    
    # Test data
    hostname = "server-a"
    timestamp = int(datetime.now(timezone.utc).timestamp())
    
    # Sign with original hostname
    sign_data = {
        "hostname": hostname,
        "timestamp": timestamp
    }
    
    signature = signer.sign(sign_data)
    print(f"Original hostname: {hostname}")
    print(f"Signature: {signature[:50]}...")
    
    # Verify with different hostname
    wrong_sign_data = {
        "hostname": "server-b",
        "timestamp": timestamp
    }
    
    verified = signer.verify(wrong_sign_data, signature)
    print(f"Verification with wrong hostname: {verified}")
    
    if not verified:
        print("🎉 Hostname mismatch correctly detected!")
        return True
    else:
        print("❌ Hostname mismatch not detected")
        return False


if __name__ == '__main__':
    test_sign_util_basic()
