import time
import functools

def timeit(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        print(f"Async task {func.__name__} took {duration:.2f} seconds")
        return result
    return wrapper
