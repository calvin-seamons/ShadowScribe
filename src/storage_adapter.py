"""
Storage Adapter for Cloud Storage (GCS) and Local Filesystem.

Provides a unified interface for reading and writing data to either:
- Local filesystem (for development)
- Google Cloud Storage (for Cloud Run deployment)

Configuration is controlled via the STORAGE_BACKEND environment variable.
"""
import os
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Union
import json


class StorageAdapter(ABC):
    """Abstract base class for storage adapters."""
    
    @abstractmethod
    def save(self, path: str, data: Any, binary: bool = True) -> bool:
        """Save data to the storage backend."""
        pass
    
    @abstractmethod
    def load(self, path: str, binary: bool = True) -> Optional[Any]:
        """Load data from the storage backend."""
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a path exists in the storage backend."""
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete a path from the storage backend."""
        pass
    
    @abstractmethod
    def list_dir(self, path: str) -> list[str]:
        """List contents of a directory."""
        pass


class LocalStorageAdapter(StorageAdapter):
    """Storage adapter for local filesystem."""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
    
    def _full_path(self, path: str) -> Path:
        return self.base_path / path
    
    def save(self, path: str, data: Any, binary: bool = True) -> bool:
        """Save data to local filesystem."""
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if binary:
                with open(full_path, 'wb') as f:
                    pickle.dump(data, f)
            else:
                with open(full_path, 'w') as f:
                    if isinstance(data, (dict, list)):
                        json.dump(data, f, indent=2, default=str)
                    else:
                        f.write(str(data))
            return True
        except Exception as e:
            print(f"[LocalStorage] Error saving {path}: {e}")
            return False
    
    def load(self, path: str, binary: bool = True) -> Optional[Any]:
        """Load data from local filesystem."""
        full_path = self._full_path(path)
        
        if not full_path.exists():
            return None
        
        try:
            if binary:
                with open(full_path, 'rb') as f:
                    return pickle.load(f)
            else:
                with open(full_path, 'r') as f:
                    content = f.read()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return content
        except Exception as e:
            print(f"[LocalStorage] Error loading {path}: {e}")
            return None
    
    def exists(self, path: str) -> bool:
        """Check if path exists locally."""
        return self._full_path(path).exists()
    
    def delete(self, path: str) -> bool:
        """Delete a local file or directory."""
        full_path = self._full_path(path)
        
        try:
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                import shutil
                shutil.rmtree(full_path)
            return True
        except Exception as e:
            print(f"[LocalStorage] Error deleting {path}: {e}")
            return False
    
    def list_dir(self, path: str) -> list[str]:
        """List contents of a local directory."""
        full_path = self._full_path(path)
        
        if not full_path.is_dir():
            return []
        
        return [item.name for item in full_path.iterdir()]


class GCSStorageAdapter(StorageAdapter):
    """Storage adapter for Google Cloud Storage."""
    
    def __init__(self, bucket_name: str, prefix: str = ""):
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self._client = None
        self._bucket = None
    
    @property
    def client(self):
        """Lazy-load the GCS client."""
        if self._client is None:
            try:
                from google.cloud import storage
                self._client = storage.Client()
            except ImportError:
                raise ImportError(
                    "google-cloud-storage is required for GCS storage. "
                    "Install with: pip install google-cloud-storage"
                )
        return self._client
    
    @property
    def bucket(self):
        """Get the GCS bucket."""
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket
    
    def _full_path(self, path: str) -> str:
        if self.prefix:
            return f"{self.prefix}/{path}"
        return path
    
    def save(self, path: str, data: Any, binary: bool = True) -> bool:
        """Save data to GCS."""
        blob_path = self._full_path(path)
        blob = self.bucket.blob(blob_path)
        
        try:
            if binary:
                content = pickle.dumps(data)
                blob.upload_from_string(content, content_type='application/octet-stream')
            else:
                if isinstance(data, (dict, list)):
                    content = json.dumps(data, indent=2, default=str)
                else:
                    content = str(data)
                blob.upload_from_string(content, content_type='application/json')
            return True
        except Exception as e:
            print(f"[GCSStorage] Error saving {path}: {e}")
            return False
    
    def load(self, path: str, binary: bool = True) -> Optional[Any]:
        """Load data from GCS."""
        blob_path = self._full_path(path)
        blob = self.bucket.blob(blob_path)
        
        try:
            if not blob.exists():
                return None
            
            content = blob.download_as_bytes()
            
            if binary:
                return pickle.loads(content)
            else:
                text = content.decode('utf-8')
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        except Exception as e:
            print(f"[GCSStorage] Error loading {path}: {e}")
            return None
    
    def exists(self, path: str) -> bool:
        """Check if blob exists in GCS."""
        blob_path = self._full_path(path)
        blob = self.bucket.blob(blob_path)
        return blob.exists()
    
    def delete(self, path: str) -> bool:
        """Delete a blob from GCS."""
        blob_path = self._full_path(path)
        
        try:
            # Check if it's a "directory" (prefix)
            blobs = list(self.bucket.list_blobs(prefix=blob_path))
            if blobs:
                for blob in blobs:
                    blob.delete()
            else:
                blob = self.bucket.blob(blob_path)
                if blob.exists():
                    blob.delete()
            return True
        except Exception as e:
            print(f"[GCSStorage] Error deleting {path}: {e}")
            return False
    
    def list_dir(self, path: str) -> list[str]:
        """List 'directory' contents in GCS (uses prefix listing)."""
        prefix = self._full_path(path)
        if not prefix.endswith('/'):
            prefix += '/'
        
        try:
            # Use delimiter to get "directory-like" listing
            blobs = self.bucket.list_blobs(prefix=prefix, delimiter='/')
            
            items = []
            # Files directly in this "directory"
            for blob in blobs:
                name = blob.name[len(prefix):]
                if name:
                    items.append(name)
            
            # "Subdirectories"
            for prefix_path in blobs.prefixes:
                name = prefix_path[len(prefix):].rstrip('/')
                if name:
                    items.append(name)
            
            return items
        except Exception as e:
            print(f"[GCSStorage] Error listing {path}: {e}")
            return []


def get_storage_adapter() -> StorageAdapter:
    """
    Factory function to get the appropriate storage adapter.
    
    Configuration via environment variables:
    - STORAGE_BACKEND: 'local' (default) or 'gcs'
    - GCS_BUCKET_NAME: Required when STORAGE_BACKEND is 'gcs'
    - GCS_PREFIX: Optional prefix for all GCS paths
    - LOCAL_STORAGE_PATH: Base path for local storage (default: current directory)
    """
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    
    if backend == "gcs":
        bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is required for GCS storage")
        
        prefix = os.getenv("GCS_PREFIX", "")
        return GCSStorageAdapter(bucket_name, prefix)
    
    else:
        base_path = os.getenv("LOCAL_STORAGE_PATH", ".")
        return LocalStorageAdapter(base_path)


# Singleton instance for convenience
_storage_adapter: Optional[StorageAdapter] = None


def storage() -> StorageAdapter:
    """Get the global storage adapter instance."""
    global _storage_adapter
    if _storage_adapter is None:
        _storage_adapter = get_storage_adapter()
    return _storage_adapter
