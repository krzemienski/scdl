"""
Enhanced threading implementation for scdl
This module provides proper multi-threaded downloading for tracks and playlists
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

def download_tracks_parallel(
    client,
    tracks_info: List[Tuple],  # List of (track, kwargs, playlist_info, exit_on_fail)
    num_threads: int = 5
) -> None:
    """
    Downloads multiple tracks in parallel using thread pool.
    
    Args:
        client: SoundCloud client
        tracks_info: List of tuples containing (track, kwargs, playlist_info, exit_on_fail)
        num_threads: Number of concurrent download threads
    """
    from . import scdl  # Import the main module
    
    if not tracks_info:
        return
    
    if num_threads <= 1:
        # Single-threaded mode
        for track, kwargs, playlist_info, exit_on_fail in tracks_info:
            scdl.download_track(client, track, kwargs, playlist_info, exit_on_fail)
    else:
        # Multi-threaded mode
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all tracks to the executor
            futures = []
            for track, kwargs, playlist_info, exit_on_fail in tracks_info:
                future = executor.submit(
                    scdl.download_track,
                    client,
                    track,
                    kwargs,
                    playlist_info,
                    exit_on_fail
                )
                futures.append((future, track))
            
            # Monitor progress with tqdm
            successful = 0
            failed = 0
            with tqdm(total=len(futures), desc="Downloading tracks") as pbar:
                for future, track in futures:
                    try:
                        future.result()
                        successful += 1
                    except Exception as e:
                        failed += 1
                        track_title = getattr(track, 'title', 'Unknown')
                        logger.error(f"Failed to download '{track_title}': {e}")
                        if exit_on_fail:
                            # Cancel remaining futures
                            for f, _ in futures:
                                f.cancel()
                            raise
                    finally:
                        pbar.update(1)
                        pbar.set_postfix({"✅": successful, "❌": failed})
            
            logger.info(f"Download complete: {successful} successful, {failed} failed")


def download_playlist_parallel(client, playlist, kwargs):
    """
    Download an entire playlist using parallel threads.
    
    This function collects all tracks from a playlist and downloads them
    concurrently using the specified number of threads.
    """
    from . import scdl
    
    # Get number of threads from kwargs
    num_threads = kwargs.get("threads", 1)
    if not isinstance(num_threads, int):
        num_threads = 1
    
    playlist_name = playlist.title.encode("utf-8", "ignore").decode("utf-8")
    playlist_name = scdl.sanitize_str(playlist_name)
    
    playlist_info = {
        "author": playlist.user.username,
        "id": playlist.id,
        "title": playlist.title,
        "tracknumber_int": 0,
        "tracknumber": "0",
        "tracknumber_total": playlist.track_count,
    }
    
    # Collect all tracks
    tracks_to_download = []
    offset = int(kwargs.get("offset", 1))
    
    for i, track in enumerate(iterable=playlist.tracks, start=offset):
        playlist_info["tracknumber_int"] = i
        playlist_info["tracknumber"] = str(i).zfill(2)
        
        # Resolve track if needed
        if not isinstance(track, scdl.BasicTrack):
            if playlist.secret_token:
                track = client.get_tracks([track.id], playlist.id, playlist.secret_token)[0]
            else:
                track = client.get_track(track.id)
        
        tracks_to_download.append((
            track,
            kwargs,
            playlist_info.copy(),  # Important: copy the dict so each track has its own
            kwargs.get("strict_playlist", False)
        ))
    
    # Download all tracks in parallel
    logger.info(f"Starting parallel download of {len(tracks_to_download)} tracks with {num_threads} threads")
    download_tracks_parallel(client, tracks_to_download, num_threads)