import os
import asyncio
import logging
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.database import TrafficEvent, get_session
from sqlmodel import select

logger = logging.getLogger(__name__)


async def cleanup_old_events():
    """
    Cleans up old events and their snapshot files.
    Runs every minute to delete events older than 1 minute and their associated files.
    Also deletes all snapshot files older than 1 minute, even if events are already deleted.
    """
    while True:
        try:
            # Calculate cutoff time (1 minute ago)
            cutoff_time = datetime.utcnow() - timedelta(minutes=1)
            
            deleted_count = 0
            deleted_files = 0
            
            # First, clean up events and their associated snapshots
            with get_session() as session:
                # Find events older than 1 minute
                query = select(TrafficEvent).where(TrafficEvent.ts < cutoff_time)
                old_events = session.exec(query).all()
                
                for event in old_events:
                    # Delete snapshot file if it exists
                    if event.snapshot_path:
                        # Extract filename from path
                        snapshot_filename = event.snapshot_path.split('/')[-1]
                        snapshot_path = os.path.join(settings.snapshots_dir, snapshot_filename)
                        
                        if os.path.exists(snapshot_path):
                            try:
                                os.remove(snapshot_path)
                                deleted_files += 1
                                logger.debug(f"Deleted snapshot file: {snapshot_filename}")
                            except Exception as e:
                                logger.warning(f"Failed to delete snapshot {snapshot_filename}: {e}")
                    
                    # Delete event from database
                    session.delete(event)
                    deleted_count += 1
                
                if deleted_count > 0:
                    session.commit()
                    logger.info(f"Cleaned up {deleted_count} old events and {deleted_files} snapshot files")
            
            # Second, clean up any remaining snapshot files older than 1 minute
            # This catches files that might have been orphaned or not properly linked to events
            if os.path.exists(settings.snapshots_dir):
                cutoff_timestamp = cutoff_time.timestamp()
                for filename in os.listdir(settings.snapshots_dir):
                    if filename.startswith('snapshot_') and filename.endswith('.jpg'):
                        filepath = os.path.join(settings.snapshots_dir, filename)
                        try:
                            # Get file modification time
                            file_mtime = os.path.getmtime(filepath)
                            if file_mtime < cutoff_timestamp:
                                os.remove(filepath)
                                deleted_files += 1
                                logger.debug(f"Deleted orphaned snapshot file: {filename}")
                        except Exception as e:
                            logger.warning(f"Failed to delete snapshot file {filename}: {e}")
            
            if deleted_files > 0 or deleted_count > 0:
                logger.info(f"Cleanup complete: {deleted_count} events, {deleted_files} snapshot files deleted")
            else:
                logger.debug("No old events or files to clean up")
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
        
        # Wait 1 minute before next cleanup
        await asyncio.sleep(60)


def start_cleanup_task():
    """Starts the cleanup task"""
    logger.info("Starting cleanup task (runs every 1 minute)")
    # Create task without awaiting (runs in background)
    task = asyncio.create_task(cleanup_old_events())
    return task
