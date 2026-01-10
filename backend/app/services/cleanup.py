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
    """
    while True:
        try:
            # Calculate cutoff time (1 minute ago)
            cutoff_time = datetime.utcnow() - timedelta(minutes=1)
            
            with get_session() as session:
                # Find events older than 1 minute
                query = select(TrafficEvent).where(TrafficEvent.ts < cutoff_time)
                old_events = session.exec(query).all()
                
                deleted_count = 0
                deleted_files = 0
                
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
                else:
                    logger.debug("No old events to clean up")
                    
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
