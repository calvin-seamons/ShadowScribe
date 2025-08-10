"""
Backup Service for Knowledge Base Files

This module provides automatic backup functionality for knowledge base files
before modifications, with restoration capabilities and cleanup management.
"""

import os
import json
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BackupInfo:
    """Information about a backup file."""
    backup_id: str
    filename: str
    created_at: datetime
    size: int
    backup_path: str


class BackupService:
    """
    Manages automatic backups of knowledge base files.
    
    Features:
    - Automatic backup creation before file modifications
    - Backup restoration capabilities
    - Automatic cleanup of old backups
    - Backup metadata tracking
    """
    
    def __init__(self, backup_path: str, max_backups_per_file: int = 10):
        """
        Initialize the backup service.
        
        Args:
            backup_path: Directory to store backup files
            max_backups_per_file: Maximum number of backups to keep per file
        """
        self.backup_path = Path(backup_path)
        self.max_backups_per_file = max_backups_per_file
        
        # Ensure backup directory exists
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BackupService initialized with path: {self.backup_path}")
    
    async def create_backup(self, filename: str, content: Dict[str, Any]) -> str:
        """
        Create a backup of file content.
        
        Args:
            filename: Original filename being backed up (can include character path like "character_name/file.json")
            content: Dictionary content to backup
            
        Returns:
            Backup ID for the created backup
            
        Raises:
            Exception: If backup creation fails
        """
        try:
            # Sanitize filename for backup ID (replace path separators)
            safe_filename = filename.replace('/', '_').replace('\\', '_')
            
            # Generate unique backup ID
            backup_id = f"{safe_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            backup_file_path = self.backup_path / f"{backup_id}.json"
            
            # Ensure backup directory exists
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup metadata
            backup_metadata = {
                "backup_id": backup_id,
                "original_filename": filename,
                "created_at": datetime.now().isoformat(),
                "content": content
            }
            
            # Write backup file
            with open(backup_file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_metadata, f, indent=2, ensure_ascii=False)
            
            # Clean up old backups for this file
            await self._cleanup_old_backups(filename)
            
            logger.info(f"Created backup {backup_id} for {filename}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Error creating backup for {filename}: {e}")
            raise
    
    async def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Restore content from a backup.
        
        Args:
            backup_id: ID of the backup to restore
            
        Returns:
            Dictionary content from the backup
            
        Raises:
            FileNotFoundError: If backup doesn't exist
            ValueError: If backup is corrupted
        """
        backup_file_path = self.backup_path / f"{backup_id}.json"
        
        if not backup_file_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")
        
        try:
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                backup_metadata = json.load(f)
            
            if "content" not in backup_metadata:
                raise ValueError(f"Corrupted backup: {backup_id}")
            
            logger.info(f"Restored backup {backup_id}")
            return backup_metadata["content"]
            
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted backup file {backup_id}: {e}")
            raise ValueError(f"Corrupted backup file: {backup_id}")
        except Exception as e:
            logger.error(f"Error restoring backup {backup_id}: {e}")
            raise
    
    async def list_backups(self, filename: Optional[str] = None) -> List[BackupInfo]:
        """
        List available backups, optionally filtered by filename.
        
        Args:
            filename: Optional filename to filter backups
            
        Returns:
            List of BackupInfo objects
        """
        backups = []
        
        try:
            for backup_file in self.backup_path.glob("*.json"):
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_metadata = json.load(f)
                    
                    # Skip if filtering by filename and doesn't match
                    if filename and backup_metadata.get("original_filename") != filename:
                        continue
                    
                    # Parse creation time
                    created_at_str = backup_metadata.get("created_at", "")
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                    except ValueError:
                        created_at = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    
                    backups.append(BackupInfo(
                        backup_id=backup_metadata.get("backup_id", backup_file.stem),
                        filename=backup_metadata.get("original_filename", "unknown"),
                        created_at=created_at,
                        size=backup_file.stat().st_size,
                        backup_path=str(backup_file)
                    ))
                    
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Skipping corrupted backup file {backup_file}: {e}")
                    continue
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x.created_at, reverse=True)
            
            logger.info(f"Listed {len(backups)} backups" + (f" for {filename}" if filename else ""))
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            raise
    
    async def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a specific backup.
        
        Args:
            backup_id: ID of the backup to delete
            
        Returns:
            True if successful
            
        Raises:
            FileNotFoundError: If backup doesn't exist
        """
        backup_file_path = self.backup_path / f"{backup_id}.json"
        
        if not backup_file_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")
        
        try:
            backup_file_path.unlink()
            logger.info(f"Deleted backup {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}")
            raise
    
    async def _cleanup_old_backups(self, filename: str) -> None:
        """
        Clean up old backups for a specific file, keeping only the most recent ones.
        
        Args:
            filename: Filename to clean up backups for
        """
        try:
            # Get all backups for this file
            backups = await self.list_backups(filename)
            
            # If we have more than the maximum allowed, delete the oldest ones
            if len(backups) > self.max_backups_per_file:
                backups_to_delete = backups[self.max_backups_per_file:]
                
                for backup in backups_to_delete:
                    try:
                        await self.delete_backup(backup.backup_id)
                        logger.info(f"Cleaned up old backup {backup.backup_id}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up backup {backup.backup_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error during backup cleanup for {filename}: {e}")
    
    async def cleanup_old_backups(self, max_age_days: int = 30) -> int:
        """
        Clean up backups older than the specified number of days.
        
        Args:
            max_age_days: Maximum age in days for backups to keep
            
        Returns:
            Number of backups deleted
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        try:
            all_backups = await self.list_backups()
            
            for backup in all_backups:
                if backup.created_at < cutoff_date:
                    try:
                        await self.delete_backup(backup.backup_id)
                        deleted_count += 1
                        logger.info(f"Cleaned up old backup {backup.backup_id} (age: {backup.created_at})")
                    except Exception as e:
                        logger.warning(f"Failed to clean up old backup {backup.backup_id}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} old backups (older than {max_age_days} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during old backup cleanup: {e}")
            return deleted_count
    
    async def get_backup_info(self, backup_id: str) -> BackupInfo:
        """
        Get information about a specific backup.
        
        Args:
            backup_id: ID of the backup to get info for
            
        Returns:
            BackupInfo object
            
        Raises:
            FileNotFoundError: If backup doesn't exist
        """
        backup_file_path = self.backup_path / f"{backup_id}.json"
        
        if not backup_file_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")
        
        try:
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                backup_metadata = json.load(f)
            
            # Parse creation time
            created_at_str = backup_metadata.get("created_at", "")
            try:
                created_at = datetime.fromisoformat(created_at_str)
            except ValueError:
                created_at = datetime.fromtimestamp(backup_file_path.stat().st_mtime)
            
            return BackupInfo(
                backup_id=backup_metadata.get("backup_id", backup_id),
                filename=backup_metadata.get("original_filename", "unknown"),
                created_at=created_at,
                size=backup_file_path.stat().st_size,
                backup_path=str(backup_file_path)
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted backup file {backup_id}: {e}")
            raise ValueError(f"Corrupted backup file: {backup_id}")
        except Exception as e:
            logger.error(f"Error getting backup info for {backup_id}: {e}")
            raise
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the backup system.
        
        Returns:
            Dictionary with backup statistics
        """
        try:
            backup_files = list(self.backup_path.glob("*.json"))
            total_backups = len(backup_files)
            total_size = sum(f.stat().st_size for f in backup_files)
            
            # Calculate size by file type
            file_stats = {}
            for backup_file in backup_files:
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_metadata = json.load(f)
                    
                    filename = backup_metadata.get("original_filename", "unknown")
                    if filename not in file_stats:
                        file_stats[filename] = {"count": 0, "size": 0}
                    
                    file_stats[filename]["count"] += 1
                    file_stats[filename]["size"] += backup_file.stat().st_size
                    
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return {
                "total_backups": total_backups,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "backup_path": str(self.backup_path),
                "max_backups_per_file": self.max_backups_per_file,
                "file_statistics": file_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting backup stats: {e}")
            return {
                "error": str(e),
                "total_backups": 0,
                "total_size_bytes": 0,
                "backup_path": str(self.backup_path)
            }