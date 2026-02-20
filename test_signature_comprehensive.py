#!/usr/bin/env python3
"""
Comprehensive test script for signature and verification functionality
"""

from app.crypto import RSAMessageSigner
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
import json
import time


def generate_test_keys():
    """Generate test key pair"""
    print('=== Generating test keys ===')
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )

    public_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem


def test_basic_signature_verification():
    """Test basic signature and verification"""
    print('\n=== Test 1: Basic signature and verification ===')
    
    # Generate keys
    private_pem, public_pem = generate_test_keys()
    
    # Create signer
    signer = RSAMessageSigner()
    signer.load_private_key(private_pem)
    signer.load_public_key(public_pem)
    
    # Test message
    test_message = b'{"hostname": "test-server", "status": "online"}'
    print(f"Test message: {test_message.decode('utf-8')}")
    
    # Sign message
    signature, timestamp, sign_error = signer.sign(test_message)
    if sign_error:
        print(f"❌ Sign error: {sign_error}")
        return False
    else:
        print(f"✅ Signature generated: {signature[:50]}...")
        print(f"✅ Timestamp: {timestamp}")
    
    # Verify message
    verified, verify_error = signer.verify(test_message, signature, timestamp)
    if verify_error:
        print(f"❌ Verify error: {verify_error}")
        return False
    else:
        print(f"✅ Verification result: {verified}")
        if verified:
            print("🎉 Basic signature verification successful!")
        else:
            print("❌ Verification failed!")
            return False
    
    return True


def test_no_hostname_message():
    """Test message without hostname"""
    print('\n=== Test 2: Message without hostname ===')
    
    # Generate keys
    private_pem, public_pem = generate_test_keys()
    
    # Create signer
    signer = RSAMessageSigner()
    signer.load_private_key(private_pem)
    signer.load_public_key(public_pem)
    
    # Test message without hostname
    test_message = b'{"status": "online", "cpu_usage": 45.5}'
    print(f"Test message: {test_message.decode('utf-8')}")
    
    # Sign message
    signature, timestamp, sign_error = signer.sign(test_message)
    if sign_error:
        print(f"❌ Sign error: {sign_error}")
        return False
    else:
        print(f"✅ Signature generated: {signature[:50]}...")
        print(f"✅ Timestamp: {timestamp}")
    
    # Verify message
    verified, verify_error = signer.verify(test_message, signature, timestamp)
    if verify_error:
        print(f"❌ Verify error: {verify_error}")
        return False
    else:
        print(f"✅ Verification result: {verified}")
        if verified:
            print("🎉 Message without hostname verification successful!")
        else:
            print("❌ Verification failed!")
            return False
    
    return True


def test_different_content_same_hostname():
    """Test different content with same hostname"""
    print('\n=== Test 3: Different content with same hostname ===')
    
    # Generate keys
    private_pem, public_pem = generate_test_keys()
    
    # Create signer
    signer = RSAMessageSigner()
    signer.load_private_key(private_pem)
    signer.load_public_key(public_pem)
    
    # Test messages with different content but same hostname
    message1 = b'{"hostname": "test-server", "status": "online", "cpu_usage": 45.5}'
    message2 = b'{"hostname": "test-server", "status": "offline", "cpu_usage": 10.0}'
    
    print(f"Message 1: {message1.decode('utf-8')}")
    print(f"Message 2: {message2.decode('utf-8')}")
    
    # Sign both messages
    signature1, timestamp1, sign_error1 = signer.sign(message1)
    signature2, timestamp2, sign_error2 = signer.sign(message2)
    
    if sign_error1 or sign_error2:
        print(f"❌ Sign error: {sign_error1 or sign_error2}")
        return False
    else:
        print(f"✅ Message 1 signature: {signature1[:50]}...")
        print(f"✅ Message 1 timestamp: {timestamp1}")
        print(f"✅ Message 2 signature: {signature2[:50]}...")
        print(f"✅ Message 2 timestamp: {timestamp2}")
    
    # Verify messages
    verified1, verify_error1 = signer.verify(message1, signature1, timestamp1)
    verified2, verify_error2 = signer.verify(message2, signature2, timestamp2)
    
    if verify_error1 or verify_error2:
        print(f"❌ Verify error: {verify_error1 or verify_error2}")
        return False
    else:
        print(f"✅ Message 1 verification: {verified1}")
        print(f"✅ Message 2 verification: {verified2}")
        
        if verified1 and verified2:
            print("🎉 Different content same hostname verification successful!")
        else:
            print("❌ Verification failed!")
            return False
    
    return True


def test_timestamp_mismatch():
    """Test timestamp mismatch"""
    print('\n=== Test 4: Timestamp mismatch ===')
    
    # Generate keys
    private_pem, public_pem = generate_test_keys()
    
    # Create signer
    signer = RSAMessageSigner()
    signer.load_private_key(private_pem)
    signer.load_public_key(public_pem)
    
    # Test message
    test_message = b'{"hostname": "test-server", "status": "online"}'
    print(f"Test message: {test_message.decode('utf-8')}")
    
    # Sign message
    signature, timestamp, sign_error = signer.sign(test_message)
    if sign_error:
        print(f"❌ Sign error: {sign_error}")
        return False
    else:
        print(f"✅ Signature generated: {signature[:50]}...")
        print(f"✅ Original timestamp: {timestamp}")
    
    # Test with different timestamp
    wrong_timestamp = timestamp + 1
    print(f"❌ Testing with wrong timestamp: {wrong_timestamp}")
    
    verified, verify_error = signer.verify(test_message, signature, wrong_timestamp)
    print(f"❌ Verification result: {verified}")
    print(f"❌ Verify error: {verify_error}")
    
    if not verified:
        print("🎉 Timestamp mismatch correctly detected!")
        return True
    else:
        print("❌ Timestamp mismatch not detected!")
        return False


def test_hostname_mismatch():
    """Test hostname mismatch"""
    print('\n=== Test 5: Hostname mismatch ===')
    
    # Generate keys
    private_pem, public_pem = generate_test_keys()
    
    # Create signer
    signer = RSAMessageSigner()
    signer.load_private_key(private_pem)
    signer.load_public_key(public_pem)
    
    # Test message with hostname A
    message_a = b'{"hostname": "server-a", "status": "online"}'
    print(f"Message A (signed): {message_a.decode('utf-8')}")
    
    # Sign message A
    signature, timestamp, sign_error = signer.sign(message_a)
    if sign_error:
        print(f"❌ Sign error: {sign_error}")
        return False
    else:
        print(f"✅ Signature generated: {signature[:50]}...")
        print(f"✅ Timestamp: {timestamp}")
    
    # Test with message B (different hostname)
    message_b = b'{"hostname": "server-b", "status": "online"}'
    print(f"Message B (different hostname): {message_b.decode('utf-8')}")
    
    verified, verify_error = signer.verify(message_b, signature, timestamp)
    print(f"❌ Verification result: {verified}")
    print(f"❌ Verify error: {verify_error}")
    
    if not verified:
        print("🎉 Hostname mismatch correctly detected!")
        return True
    else:
        print("❌ Hostname mismatch not detected!")
        return False


def test_provided_keys():
    """Test with provided keys"""
    print('\n=== Test 6: Testing with provided keys ===')
    
    try:
        # Create signer with provided keys
        signer = RSAMessageSigner.new(
            private_key_path="private.pem",
            public_key_path="public-agent.pem",
            enabled=True
        )
        
        # Test message
        test_message = b'{"hostname": "test-server", "status": "online"}'
        print(f"Test message: {test_message.decode('utf-8')}")
        
        # Sign message
        signature, timestamp, sign_error = signer.sign(test_message)
        if sign_error:
            print(f"❌ Sign error: {sign_error}")
            return False
        else:
            print(f"✅ Signature generated: {signature[:50]}...")
            print(f"✅ Timestamp: {timestamp}")
        
        # Verify message
        verified, verify_error = signer.verify(test_message, signature, timestamp)
        if verify_error:
            print(f"❌ Verify error: {verify_error}")
            print("ℹ️  This is expected if the provided keys are not a matching pair")
            return False
        else:
            print(f"✅ Verification result: {verified}")
            if verified:
                print("🎉 Provided keys verification successful!")
            else:
                print("❌ Verification failed with provided keys!")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing provided keys: {e}")
        print("ℹ️  Make sure private.pem and public-agent.pem files exist")
        return False


def main():
    """Run all tests"""
    print('🔐 Comprehensive signature verification test suite')
    print('=' * 60)
    
    tests = [
        test_basic_signature_verification,
        test_no_hostname_message,
        test_different_content_same_hostname,
        test_timestamp_mismatch,
        test_hostname_mismatch,
        test_provided_keys
    ]
    
    passed = 0
    total = len(tests)
    
    for i, test_func in enumerate(tests, 1):
        print(f"\n{'=' * 60}")
        print(f"Running test {i}/{total}: {test_func.__name__}")
        print('=' * 60)
        
        if test_func():
            passed += 1
            print(f"✅ Test {i} passed!")
        else:
            print(f"❌ Test {i} failed!")
    
    print(f"\n{'=' * 60}")
    print(f"Test summary: {passed}/{total} tests passed")
    print('=' * 60)
    
    if passed == total:
        print('🎉 All tests passed! Signature and verification functionality is working correctly.')
    else:
        print('⚠️  Some tests failed. Please check the output for details.')


if __name__ == "__main__":
    main()
