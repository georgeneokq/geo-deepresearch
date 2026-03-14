import asyncio
from contextlib import asynccontextmanager
from geo_deepresearch.util.logging import get_logger
from geo_deepresearch.config import config

logger = get_logger()


class InternalBrowseManager():
    """
    Takes care of preventing multiple retrievals of the same internal document.
    Provides a shared cache to read and store internal document results.
    Uses per-point-ID locks when parallel_mode is enabled, or a global lock otherwise.
    """

    lock_timeout: float
    parallel_mode: bool

    def __init__(self, parallel_mode: bool = False):
        self.lock_timeout = 60
        self.parallel_mode = parallel_mode

        self.point_id_to_lock_mapping: dict[str, asyncio.Lock] = {}

        # Contents cache for internal documents
        self.contents_cache: dict[str, str] = {}

        # The "master lock" for global locking when parallel_mode is disabled
        self.master_lock = asyncio.Lock()

    async def get_cached_document(self, point_id: str, wait_for_current_retrieval=True) -> str | None:
        """
        Retrieve internal document content from cache.

        Args:
            point_id (str): Point ID to retrieve
            wait_for_current_retrieval (bool): If it is currently being retrieved by another agent,
                                               wait for the cache to be populated.
        """
        if wait_for_current_retrieval:
            # In case point_id is being retrieved, wait for the result to be cached
            await self.wait_for_release(point_id)

        return self.contents_cache.get(point_id)

    def add_to_cache(self, point_id: str, content: str):
        """
        Populate the content cache
        """
        self.contents_cache[point_id] = content

    def is_locked(self, point_id: str):
        """
        Check if an agent is retrieving a point ID

        Args:
            point_id (str): Point ID to check lock status of
        """
        lock = self.point_id_to_lock_mapping.get(point_id)
        if lock:
            return lock.locked()
        return False

    async def wait_for_release(self, point_id: str):
        """
        Wait for a lock to be released.

        Args:
            point_id (str): Point ID to wait for lock release of
        """
        async with self.master_lock:
            lock = self.point_id_to_lock_mapping.get(point_id)

        if lock:
            async with lock:
                pass

    @asynccontextmanager
    async def acquire_retrieval_lock(self, point_id: str):
        """
        To prevent multiple agents from retrieving the same internal document,
        we get them to acquire a lock before trying to retrieve a point ID.
        If the lock is already acquired, they use another function to wait for the lock to be released.
        To prevent deadlocks, we enforce a timeout of 60 seconds.
        """
        # Master lock prevents overwriting of lock onto the same dict key
        # If parallel mode is enabled, we need per-point-ID lock handling.
        if self.parallel_mode:
            async with self.master_lock:
                # Check if the point_id to Lock mapping contains the current point_id.
                lock = self.point_id_to_lock_mapping.get(point_id)
                if not lock:
                    # If there is no lock (not being retrieved), create a lock.
                    lock = asyncio.Lock()
                    self.point_id_to_lock_mapping[point_id] = lock

            try:
                # Acquire lock with timeout to prevent deadlocks
                await asyncio.wait_for(lock.acquire(), timeout=self.lock_timeout)
                try:
                    yield
                finally:
                    logger.debug(f"Released lock for {point_id}")
                    lock.release()

            except asyncio.TimeoutError:
                logger.debug(f"Released lock for {point_id} (timeout after {self.lock_timeout} seconds)")
                lock.release()
        else:
            # Parallel mode is not enabled; we use the master lock as a global lock
            # for all internal document retrievals regardless of point_id.
            # Acquire lock with timeout to prevent deadlocks
            await asyncio.wait_for(self.master_lock.acquire(), timeout=self.lock_timeout)
            try:
                yield
            finally:
                self.master_lock.release()


# Instance to be shared by all agents
internal_browse_manager = InternalBrowseManager(parallel_mode=config.is_parallel_mode_enabled())
