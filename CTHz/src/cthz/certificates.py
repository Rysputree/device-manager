"""
TLS Certificate Management for CTHz Communication
Handles self-signed certificates for local device communication
"""
import os
import ssl
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)

class CertificateManager:
    """Manages TLS certificates for CTHz communication"""
    
    def __init__(self):
        self.cert_dir = Path("./certs")
        self.cert_path = self.cert_dir / "device.crt"
        self.key_path = self.cert_dir / "device.key"
        self.ca_cert_path = self.cert_dir / "ca.crt"
        
    def ensure_certificates(self) -> bool:
        """Ensure TLS certificates exist, create if missing"""
        try:
            self.cert_dir.mkdir(exist_ok=True)
            
            if not self.cert_path.exists() or not self.key_path.exists():
                logger.info("Creating self-signed certificates for CTHz communication")
                self._generate_self_signed_cert()
                return True
            
            if not self.ca_cert_path.exists():
                logger.info("Creating CA certificate")
                self._generate_ca_cert()
                return True
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure certificates: {e}")
            return False
    
    def _generate_self_signed_cert(self) -> None:
        """Generate self-signed certificate for device communication"""
        try:
            # Generate private key
            subprocess.run([
                "openssl", "genrsa", "-out", str(self.key_path), "2048"
            ], check=True)
            
            # Generate certificate signing request
            csr_path = self.cert_dir / "device.csr"
            subprocess.run([
                "openssl", "req", "-new", "-key", str(self.key_path),
                "-out", str(csr_path), "-subj", "/C=US/ST=CA/L=San Francisco/O=CTHz/CN=localhost"
            ], check=True)
            
            # Generate self-signed certificate
            subprocess.run([
                "openssl", "x509", "-req", "-in", str(csr_path),
                "-signkey", str(self.key_path), "-out", str(self.cert_path),
                "-days", "365"
            ], check=True)
            
            # Clean up CSR
            csr_path.unlink()
            
            logger.info("Self-signed certificate generated successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate self-signed certificate: {e}")
            raise
        except FileNotFoundError:
            logger.error("OpenSSL not found. Please install OpenSSL to generate certificates.")
            raise
    
    def _generate_ca_cert(self) -> None:
        """Generate CA certificate for certificate validation"""
        try:
            # Generate CA private key
            ca_key_path = self.cert_dir / "ca.key"
            subprocess.run([
                "openssl", "genrsa", "-out", str(ca_key_path), "2048"
            ], check=True)
            
            # Generate CA certificate
            subprocess.run([
                "openssl", "req", "-x509", "-new", "-nodes",
                "-key", str(ca_key_path), "-sha256", "-days", "365",
                "-out", str(self.ca_cert_path),
                "-subj", "/C=US/ST=CA/L=San Francisco/O=CTHz/CN=CTHz-CA"
            ], check=True)
            
            logger.info("CA certificate generated successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate CA certificate: {e}")
            raise
        except FileNotFoundError:
            logger.error("OpenSSL not found. Please install OpenSSL to generate certificates.")
            raise
    
    def get_ssl_context(self, verify: bool = True) -> ssl.SSLContext:
        """Get SSL context for HTTPS communication"""
        context = ssl.create_default_context()
        
        if verify and self.ca_cert_path.exists():
            context.load_verify_locations(self.ca_cert_path)
        else:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        return context
    
    def validate_certificate(self, cert_path: Path) -> bool:
        """Validate certificate file"""
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            # Try to load the certificate
            ssl.DER_cert_to_PEM_cert(cert_data)
            return True
            
        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            return False
    
    def get_certificate_info(self) -> dict:
        """Get information about the current certificate"""
        try:
            if not self.cert_path.exists():
                return {"error": "Certificate not found"}
            
            # Get certificate details using OpenSSL
            result = subprocess.run([
                "openssl", "x509", "-in", str(self.cert_path),
                "-text", "-noout"
            ], capture_output=True, text=True, check=True)
            
            return {
                "cert_path": str(self.cert_path),
                "key_path": str(self.key_path),
                "ca_cert_path": str(self.ca_cert_path),
                "details": result.stdout
            }
            
        except Exception as e:
            logger.error(f"Failed to get certificate info: {e}")
            return {"error": str(e)}

# Global certificate manager instance
cert_manager = CertificateManager()
