import os
import asyncio
from dataclasses import dataclass
import time
from contextlib import asynccontextmanager
from geo_deepresearch.util.logging import get_logger
from geo_deepresearch.config import config

"""
TODO:   Implement a database to store cached webpages, with cache invalidation with each record.
        The cache invalidation can be done dynamically by an LLM which sets it based on whether the webpage
        seems like it will be updated often. Alternatively, an LLM could also decide not to cache it at all,
        which would be useful for live stock prices for example.
"""

logger = get_logger()

@dataclass
class CacheItem:
    content: str
    browsed_timestamp: float
    invalidation_timeout: float  # in seconds

class BrowseManager():
    """
    Takes care of preventing multiple browsing of same webpage.
    Provides a shared cache to read and write webpage results.
    """

    invalidation_timeout: float
    lock_timeout: float
    parallel_mode: bool

    def __init__(self, parallel_mode: bool = False):
        self.invalidation_timeout = 60
        self.lock_timeout = 60
        self.parallel_mode = parallel_mode

        self.url_to_lock_mapping: dict[str, asyncio.Lock] = {}
        
        # Contents cache, 
        self.contents_cache: dict[str, CacheItem] = {}

        # The "master lock", which is used to acquire a lock for a specific URL.
        self.master_lock = asyncio.Lock()
    
    async def get_cached_webpage(self, url: str, wait_for_current_browse=True) -> str | None:
        """
        Retrieve webpage content from cached.
        Handles invalidation as well; if the cached content passes the invalidation timeout,
        it is deleted from the cache and this function returns None.

        Args:
            url (str): URL to browse
            wait_for_current_browse (bool): If it is currently being browsed by another agent,
                                            wait for the cache to be populated.
                                            You can prevent wasting time waiting by implementing a "retry queue"
                                            and setting wait_for_current_browse to false.
        """
        if wait_for_current_browse:
            # In case url is being browsed, wait for the result to be cached
            await self.wait_for_release(url)
            
        cached_item = self.contents_cache.get(url)

        if cached_item:
            # Check invalidation time
            time_diff = time.time() - cached_item.browsed_timestamp

            if time_diff > self.invalidation_timeout:
                # Delete from cache if passed invalidation timeout
                self.contents_cache.pop(url)
                return None
            else:
                return cached_item.content

        return None
    
    def add_to_cache(self, url: str, content: str):
        """
        Populate the content cache
        """
        self.contents_cache[url] = CacheItem(content, time.time(), self.invalidation_timeout)
    
    def is_locked(self, url: str):
        """
        Check if an agent is browsing a URL

        Args:
            url (str): URL to check lock status of
        """
        lock = self.url_to_lock_mapping.get(url)
        if lock:
            return lock.locked()
        return False
    
    async def wait_for_release(self, url: str):
        """
        Wait for a lock to be released.

        Args:
            url (str): URL to wait for lock release of
        """
        async with self.master_lock:
            lock = self.url_to_lock_mapping.get(url)

        if lock:
            async with lock:
                pass

    @asynccontextmanager
    async def acquire_web_search_lock(self, timeout: float):
        """
        Acquire lock for performing web search.
        All agents should use this method as context manager like so:
        `async with acquire_web_search_lock():`

        If parallel mode is enabled, the lock will not be acquired, and code will just be executed as per normal.
        """
        if self.parallel_mode:
            await asyncio.wait_for(self.master_lock.acquire(), timeout)

        yield

        if self.master_lock.locked():
            self.master_lock.release()

    @asynccontextmanager
    async def acquire_browse_lock(self, url: str):
        """
        To prevent multiple agents from browsing same URL, we get them to acquire a lock before trying to browse a URL.
        If the lock is already acquired, they use another function to wait for the lock to be released.
        To prevent deadlocks, we enforce a timeout of 60 seconds.
        No webpage browse should take that long - if it does, just butcher it.
        """
        # Master lock prevents overwriting of lock onto the same dict key
        # If parallel mode is enabled, we need per-URL lock handling.
        if self.parallel_mode:
            async with self.master_lock:
                # Check if the URL to Lock mapping contains the current URL.
                lock = self.url_to_lock_mapping.get(url)
                if not lock:
                    # If there is no lock (not browsed), create a lock.
                    lock = asyncio.Lock()
                    self.url_to_lock_mapping[url] = lock

            try:
                # Acquire lock with timeout to prevent deadlocks
                await asyncio.wait_for(lock.acquire(), timeout=self.lock_timeout)
                try:
                    yield
                finally:
                    logger.debug(f"Released lock for {url}")
                    lock.release()

                # Run actual code
            except asyncio.TimeoutError:
                logger.debug(f"Released lock for {url} (timeout after {self.lock_timeout} seconds)")
                lock.release()
        else:
            # Parallel mode is not enabled; we use the master lock as a global lock
            # for all webpage browsing regardless of URL.
            # Acquire lock with timeout to prevent deadlocks
            await asyncio.wait_for(self.master_lock.acquire(), timeout=self.lock_timeout)
            try:
                yield
            finally:
                self.master_lock.release()

# Instance to be shared to all agents
browse_manager = BrowseManager(parallel_mode=config.is_parallel_mode_enabled())
