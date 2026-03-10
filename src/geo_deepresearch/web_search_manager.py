import asyncio
from contextlib import asynccontextmanager
from geo_deepresearch.config import config

class WebSearchManager():
    master_lock: asyncio.Lock
    parallel_mode: bool

    def __init__(self, parallel_mode: bool = False):
        self.master_lock = asyncio.Lock()
        self.parallel_mode = parallel_mode
    
    @asynccontextmanager
    async def acquire_web_search_lock(self, timeout: float = 60.0):
        """
        Acquire lock for performing web search.
        All agents should use this method as context manager like so:
        `async with acquire_web_search_lock():`

        If parallel mode is enabled, the lock will not be acquired, and code will just be executed as per normal.
        """
        if self.parallel_mode:
            await asyncio.wait_for(self.master_lock.acquire(), timeout)
        
        try:
            yield
        finally:
            if self.master_lock.locked():
                self.master_lock.release()


web_search_manager = WebSearchManager(parallel_mode=config.is_parallel_mode_enabled())
