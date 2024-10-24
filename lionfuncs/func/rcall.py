# import asyncio
# from collections.abc import Callable
# from typing import Any, TypeVar

# from lionfuncs.func.ucall import ucall
# from lionfuncs.ln_undefined import LN_UNDEFINED
# from lionfuncs.utils import time

# T = TypeVar("T")
# ErrorHandler = Callable[[Exception], Any]

# from lionfuncs.utils import AsyncUtils
# from lionfuncs.func.tcall import tcall


# async def rcall(
#     func: Callable[..., T],
#     /,
#     *args: Any,
#     num_retries: int = 0,
#     initial_delay: float = 0,
#     retry_delay: float = 0,
#     backoff_factor: float = 1,
#     timeout_default: Any = LN_UNDEFINED,        # if have default, will ignore retry
#     error_default: Any = LN_UNDEFINED,          # if have default, will ignore retry
#     retry_timeout: float | None = None,
#     retry_timing: bool = False,
#     verbose_retry: bool = True,
#     error_msg: str | None = None,
#     error_map: dict[type, ErrorHandler] | None = None,
#     **kwargs: Any,
# ) -> T | tuple[T, float]:

#     last_exception = None
#     result = None

#     await asyncio.sleep(initial_delay)


#     attempts = 0
#     remaining_retries = num_retries
#     while (remaining_retries - attempts):


#         num_retries -= 1
#         _delay = _delay * backoff_factor

#         try:
#             return await tcall(
#                 func, *args, timeout=retry_timeout,
#                 initial_delay=_delay - retry_delay,
#                 timeout_default=timeout_default,
#                 error_default=error_default,
#                 error_msg=error_msg,
#                 error_map=error_map,
#                 **kwargs
#             )

#         except Exception as e:
#             last_exception = e
#             if verbose_retry:
#                 print(
#                     f"Attempt {num_retries + 1}/{num_retries + 1} failed: {e},"
#                     " retrying..."
#                 )
#             await asyncio.sleep(retry_delay)


#     for attempt in range(num_retries + 1):
#         try:
#             if num_retries == 0:
#                 if retry_timing:
#                     result, duration = await _rcall(
#                         func,
#                         *args,
#                         retry_timeout=retry_timeout,
#                         retry_timing=True,
#                         **kwargs,
#                     )
#                     return result, duration
#                 result = await _rcall(
#                     func,
#                     *args,
#                     retry_timeout=retry_timeout,
#                     **kwargs,
#                 )
#                 return result
#             err_msg = (
#                 f"Attempt {attempt + 1}/{num_retries + 1}: {error_msg or ''}"
#             )
#             if retry_timing:
#                 result, duration = await _rcall(
#                     func,
#                     *args,
#                     error_msg=err_msg,
#                     retry_timeout=retry_timeout,
#                     retry_timing=True,
#                     **kwargs,
#                 )
#                 return result, duration

#             result = await _rcall(
#                 func,
#                 *args,
#                 error_msg=err_msg,
#                 retry_timeout=retry_timeout,
#                 **kwargs,
#             )
#             return result
#         except Exception as e:
#             last_exception = e
#             if error_map and type(e) in error_map:
#                 error_map[type(e)](e)
#             if attempt < num_retries:
#                 if verbose_retry:
#                     print(
#                         f"Attempt {attempt + 1}/{num_retries + 1} failed: {e},"
#                         " retrying..."
#                     )
#                 await asyncio.sleep(retry_delay)
#                 retry_delay *= backoff_factor
#             else:
#                 break

#     if retry_default is not LN_UNDEFINED:
#         return retry_default

#     if last_exception is not None:
#         if error_map and type(last_exception) in error_map:
#             handler = error_map[type(last_exception)]
#             if asyncio.iscoroutinefunction(handler):
#                 return await handler(last_exception)
#             else:
#                 return handler(last_exception)
#         raise RuntimeError(
#             f"{error_msg or ''} Operation failed after {num_retries + 1} "
#             f"attempts: {last_exception}"
#         ) from last_exception

#     raise RuntimeError(
#         f"{error_msg or ''} Operation failed after {num_retries + 1} attempts"
#     )


# async def _rcall(
#     func: Callable[..., T],
#     *args: Any,
#     retry_timeout: float | None = None,
#     retry_delay: float = 0,
#     timeout_default: Any = LN_UNDEFINED,        # priority 1
#     error_default: Any = LN_UNDEFINED,          # priority 1
#     error_msg: str | None = None,
#     error_map: dict[type, ErrorHandler] | None = None,      # priority 2
#     **kwargs,
# ) -> T | tuple[T, float]:

#     asyncio.sleep(retry_delay)
#     try:
#         result = await tcall(
#             func, *args, timeout=retry_timeout,
#             initial_delay=retry_delay,
#             timeout_default=timeout_default,
#             error_default=error_default,
#             error_msg=error_msg,
#             error_map=error_map
#         )


#     try:
#         await asyncio.sleep(retry_delay)
#         if retry_timeout is not None:
#             result = await asyncio.wait_for(
#                 ucall(func, *args, **kwargs), timeout=retry_timeout
#             )
#         else:
#             result = await ucall(func, *args, **kwargs)
#         duration = _t() - start_time
#         return (result, duration) if retry_timing else result
#     except asyncio.TimeoutError as e:
#         error_msg = (
#             f"{error_msg or ''} Timeout {retry_timeout} seconds exceeded"
#         )
#         if ignore_err:
#             duration = _t() - start_time
#             return (retry_default, duration) if retry_timing else retry_default
#         else:
#             raise asyncio.TimeoutError(error_msg) from e
#     except Exception:
#         if ignore_err:
#             duration = _t() - start_time
#             return (retry_default, duration) if retry_timing else retry_default
#         else:
#             raise
