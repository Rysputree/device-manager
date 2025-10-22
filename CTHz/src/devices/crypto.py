from __future__ import annotations

from typing import Tuple
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


def generate_key_and_csr(common_name: str, device_id: str, cluster_id: str) -> Tuple[bytes, bytes]:
    """Generate ECDSA key and CSR with CN and SANs for device/cluster.

    Returns: (private_key_pem, csr_pem)
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name)
    ])
    builder = x509.CertificateSigningRequestBuilder().subject_name(subject)
    san = x509.SubjectAlternativeName([
        x509.DNSName(f"device:{device_id}"),
        x509.DNSName(f"cluster:{cluster_id}"),
    ])
    builder = builder.add_extension(san, critical=False)
    csr = builder.sign(private_key, hashes.SHA256())
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    csr_pem = csr.public_bytes(serialization.Encoding.PEM)
    return key_pem, csr_pem


