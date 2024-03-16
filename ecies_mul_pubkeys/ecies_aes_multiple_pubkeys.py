from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ecies import encrypt, decrypt, utils
import os
from Crypto.Hash import keccak

# Install dependencies:
#
# pip install eciespy cryptography pycryptodome

def generate_keys(n):
    """
    Generate 'n' pairs of Ethereum ECDSA keys (private, public).

    ECDSA (Elliptic Curve Digital Signature Algorithm) is a cryptographic algorithm
    used by Ethereum to ensure that funds can only be spent by their owners.
    A key pair consists of a private key (used for signing transactions and decrypting data)
    and a public key (used to receive transactions and encrypt data).
    """
    keys = [utils.generate_eth_key() for _ in range(n)]
    private_keys = [key.to_hex() for key in keys]
    public_keys = [key.public_key.to_hex() for key in keys]
    return private_keys, public_keys

def ethereum_address_from_public_key_hex(public_key_hex):
    """
    Convert a hex public key to an Ethereum address.

    Ethereum addresses are derived from the public key associated with an Ethereum account.
    This function uses the Keccak-256 hash function to hash the public key, and then
    takes the last 20 bytes of this hash to produce an Ethereum address.
    """
    public_key_bytes = bytes.fromhex(public_key_hex[2:])  # Remove 0x prefix
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(public_key_bytes)
    return "0x" + keccak_hash.hexdigest()[-40:]

def aes_encrypt(data, key):
    """
    Encrypt data using AES.

    AES (Advanced Encryption Standard) is a symmetric encryption algorithm that encrypts
    data in fixed-size blocks. AES-GCM (Galois/Counter Mode) is an authenticated encryption mode
    that not only provides confidentiality but also provides integrity and authenticity.
    This function returns the nonce and the encrypted data.
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # AES-GCM standard nonce size (96 bits)
    return nonce, aesgcm.encrypt(nonce, data, None)

def aes_decrypt(encrypted_data, key, nonce):
    """
    Decrypt data using AES.

    This function decrypts data that was encrypted using AES-GCM, given the encrypted data,
    the AES key, and the nonce used during encryption.
    """
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, encrypted_data, None)

def encrypt_for_multiple_recipients(data, public_keys):
    """
    Encrypt data for multiple recipients using AES for the data and ECIES for the symmetric key.

    This function demonstrates a hybrid encryption approach where the data is encrypted once
    using a symmetric key (AES), and then this key is encrypted for each recipient using their
    public EC key (ECIES). This approach is efficient and secure for sending encrypted data to multiple recipients.
    """
    aes_key = AESGCM.generate_key(bit_length=256)  # Generate a random AES key
    
    nonce, encrypted_data = aes_encrypt(data, aes_key)  # Encrypt the data with AES
    
    encrypted_keys = [encrypt(public_key, aes_key) for public_key in public_keys]  # Encrypt AES key with each recipient's public EC key
    
    return nonce, encrypted_data, encrypted_keys

def main():
    data = b"""
    ECIES encryption for multiple recipients!

    Encrypt data for multiple recipients using AES for the data and ECIES for the symmetric key.

    This function demonstrates a hybrid encryption approach where the data is encrypted once
    using a symmetric key (AES), and then this key is encrypted for each recipient using their
    public EC key (ECIES). This approach is efficient and secure for sending encrypted data to multiple recipients.
    """

    print("Data: \n", data.decode("utf-8"), "\n")

    num_recipients = 3
    
    private_keys, public_keys = generate_keys(num_recipients)
    
    # Print Ethereum addresses for illustrative purposes
    for idx, key in enumerate(public_keys, start=1):
        eth_address = ethereum_address_from_public_key_hex(key)
        print(f"Recipient {idx} Ethereum Address: {eth_address}")
    
    nonce, encrypted_data, encrypted_keys = encrypt_for_multiple_recipients(data, public_keys)

    print("\nEncrypted Data:\n", encrypted_data.hex())
    print("\nNonce:", nonce.hex())
    print("\nEncrypted AES Keys for Each Recipient:")
    for idx, key in enumerate(encrypted_keys, start=1):
        print(f"Recipient {idx}: {key.hex()}")
    
    # Decryption demo for each recipient
    print("\n--- Decryption Demo for Each Recipient ---")
    for idx, private_key in enumerate(private_keys, start=1):
        decrypted_aes_key = decrypt(private_key, encrypted_keys[idx - 1])  # Decrypt AES key with recipient's private EC key
        decrypted_data = aes_decrypt(encrypted_data, decrypted_aes_key, nonce)  # Decrypt data with AES key
        print(f"\nRecipient {idx} Decrypted Data:\n {decrypted_data.decode()}")

if __name__ == "__main__":
    main()

