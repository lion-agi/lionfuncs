"""
Comprehensive asynchronous execution utilities for different calling patterns:
- tcall: Timed execution with error handling
- rcall: Retryable execution with backoff
- ucall: Universal async call with error handling
- pcall: Parallel async execution of multiple functions
- lcall: List-based async execution with batching options
- bcall: Batch processing of inputs with async execution
- mcall: Multiple function execution across inputs
"""

import asyncio
from ast import List
from collections.abc import AsyncGenerator, Callable, Sequence
from typing import Any, Dict, Optional, Tuple, TypeVar, Union

from lionfuncs.func.utils import (
    custom_error_handler,
    force_async,
    is_coroutine_func,
)
from lionfuncs.ln_undefined import LN_UNDEFINED
from lionfuncs.parse.to_list import to_list
from lionfuncs.utils import time as _t

T = TypeVar("T")
ErrorHandler = TypeVar("ErrorHandler", bound=Callable)


async def ucall(
    func: Callable,
    /,
    *args: Any,
    error_map: Optional[Union[Dict, None]] = None,
    **kwargs: Any,
) -> T:
    """
    Execute a function asynchronously with error handling.

    Ensures asynchronous execution of both coroutine and regular functions,
    managing event loops and applying custom error handling.

    Args:
        func: The function to be executed (coroutine or regular).
        *args: Positional arguments for the function.
        error_map: Dict mapping exception types to error handlers.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function call.

    Raises:
        Exception: Any unhandled exception from the function execution.

    Example:
        >>> async def example_func(x):
        ...     return x * 2
        >>> await ucall(example_func, 5)
        10
    """
    try:
        if not is_coroutine_func(func):
            func = force_async(func)

        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                return await func(*args, **kwargs)
            else:
                return await asyncio.run(func(*args, **kwargs))

        except RuntimeError:  # No running event loop
            loop = asyncio.new_event_loop()
            result = await func(*args, **kwargs)
            loop.close()
            return result

    except Exception as e:
        if error_map:
            return await custom_error_handler(e, error_map)
        raise e


async def pcall(
    funcs: Sequence,
    /,
    num_retries: int = 0,
    initial_delay: float = 0,
    retry_delay: float = 0,
    backoff_factor: float = 1,
    retry_default: Any = LN_UNDEFINED,
    retry_timeout: Optional[float] = None,
    retry_timing: bool = False,
    verbose_retry: bool = True,
    error_msg: Optional[str] = None,
    error_map: Optional[Union[Dict, None]] = None,
    max_concurrent: Optional[int] = None,
    throttle_period: Optional[float] = None,
    **kwargs: Any,
) -> List:
    """
    Execute multiple functions asynchronously in parallel with options.

    Args:
        funcs: Sequence of functions to execute in parallel.
        num_retries: Number of retry attempts for each function.
        initial_delay: Delay before starting execution.
        retry_delay: Initial delay between retry attempts.
        backoff_factor: Factor to increase delay after each retry.
        retry_default: Value to return if all attempts fail.
        retry_timeout: Timeout for each function execution.
        retry_timing: If True, return execution duration.
        verbose_retry: If True, print retry messages.
        error_msg: Custom error message prefix.
        error_map: Dict mapping exception types to error handlers.
        max_concurrent: Maximum number of concurrent executions.
        throttle_period: Minimum time between function starts.
        **kwargs: Additional keyword arguments for functions.

    Returns:
        List of results, optionally with execution times if retry_timing.

    Example:
        >>> async def func1(x): return x * 2
        >>> async def func2(x): return x + 10
        >>> results = await pcall([func1, func2], x=5)
        >>> print(results)  # [10, 15]
    """
    if initial_delay:
        await asyncio.sleep(initial_delay)

    semaphore = asyncio.Semaphore(max_concurrent) if max_concurrent else None
    throttle_delay = throttle_period if throttle_period else 0

    async def _task(func: Callable, index: int) -> Any:
        if semaphore:
            async with semaphore:
                return await _execute_task(func, index)
        else:
            return await _execute_task(func, index)

    async def _execute_task(func: Callable, index: int) -> Any:
        attempts = 0
        current_delay = retry_delay
        while True:
            try:
                if retry_timing:
                    start_time = asyncio.get_event_loop().time()
                    result = await asyncio.wait_for(
                        ucall(func, **kwargs), retry_timeout
                    )
                    end_time = asyncio.get_event_loop().time()
                    return index, result, end_time - start_time
                else:
                    result = await asyncio.wait_for(
                        ucall(func, **kwargs), retry_timeout
                    )
                    return index, result
            except asyncio.TimeoutError as e:
                raise asyncio.TimeoutError(
                    f"{error_msg or ''} Timeout {retry_timeout}s exceeded"
                ) from e
            except Exception as e:
                if error_map and type(e) in error_map:
                    handler = error_map[type(e)]
                    if is_coroutine_func(handler):
                        return index, await handler(e)
                    else:
                        return index, handler(e)
                attempts += 1
                if attempts <= num_retries:
                    if verbose_retry:
                        print(
                            f"Attempt {attempts}/{num_retries} failed: {e}"
                            ", retrying..."
                        )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
                else:
                    if retry_default is not LN_UNDEFINED:
                        return index, retry_default
                    raise e

    tasks = [_task(func, index) for index, func in enumerate(funcs)]
    results = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        await asyncio.sleep(throttle_delay)

    results.sort(key=lambda x: x[0])

    if retry_timing:
        return [(result[1], result[2]) for result in results]
    else:
        return [result[1] for result in results]


async def lcall(
    input_: Any,
    func: Callable,
    /,
    num_retries: int = 0,
    initial_delay: float = 0,
    retry_delay: float = 0,
    backoff_factor: float = 1,
    retry_default: Any = LN_UNDEFINED,
    retry_timeout: Optional[float] = None,
    retry_timing: bool = False,
    verbose_retry: bool = True,
    error_msg: Optional[str] = None,
    error_map: Optional[Union[Dict, None]] = None,
    max_concurrent: Optional[int] = None,
    throttle_period: Optional[float] = None,
    flatten: bool = False,
    dropna: bool = False,
    unique: bool = False,
    **kwargs: Any,
) -> List:
    """
    Apply a function to each element of a list asynchronously with options.

    Args:
        input_: List of inputs to be processed.
        func: Async or sync function to apply to each input element.
        num_retries: Number of retry attempts for each function call.
        initial_delay: Initial delay before starting execution.
        retry_delay: Delay between retry attempts.
        backoff_factor: Factor to increase delay after each retry.
        retry_default: Default value if all attempts fail.
        retry_timeout: Timeout for each function execution.
        retry_timing: If True, return execution duration.
        verbose_retry: If True, print retry messages.
        error_msg: Custom error message prefix.
        error_map: Dict mapping exception types to error handlers.
        max_concurrent: Maximum number of concurrent executions.
        throttle_period: Minimum time between executions.
        flatten: If True, flatten the resulting list.
        dropna: If True, remove None values from results.
        unique: If True, return only unique values.
        **kwargs: Additional keyword arguments for func.

    Returns:
        List of results, optionally with execution times.

    Example:
        >>> async def square(x): return x * x
        >>> await lcall([1, 2, 3], square)
        [1, 4, 9]
    """
    input_ = to_list(input_, flatten=False, dropna=False)

    if initial_delay:
        await asyncio.sleep(initial_delay)

    semaphore = asyncio.Semaphore(max_concurrent) if max_concurrent else None
    throttle_delay = throttle_period if throttle_period else 0

    async def _task(i: Any, index: int) -> Any:
        if semaphore:
            async with semaphore:
                return await _execute_task(i, index)
        else:
            return await _execute_task(i, index)

    async def _execute_task(i: Any, index: int) -> Any:
        attempts = 0
        current_delay = retry_delay
        while True:
            try:
                if retry_timing:
                    start_time = asyncio.get_event_loop().time()
                    result = await asyncio.wait_for(
                        ucall(func, i, **kwargs), retry_timeout
                    )
                    end_time = asyncio.get_event_loop().time()
                    return index, result, end_time - start_time
                else:
                    result = await asyncio.wait_for(
                        ucall(func, i, **kwargs), retry_timeout
                    )
                    return index, result
            except asyncio.TimeoutError as e:
                raise asyncio.TimeoutError(
                    f"{error_msg or ''} Timeout {retry_timeout}s exceeded"
                ) from e
            except Exception as e:
                if error_map and type(e) in error_map:
                    handler = error_map[type(e)]
                    if is_coroutine_func(handler):
                        return index, await handler(e)
                    else:
                        return index, handler(e)
                attempts += 1
                if attempts <= num_retries:
                    if verbose_retry:
                        print(
                            f"Attempt {attempts}/{num_retries} failed: {e}"
                            ", retrying..."
                        )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
                else:
                    if retry_default is not LN_UNDEFINED:
                        return index, retry_default
                    raise e

    tasks = [_task(i, index) for index, i in enumerate(input_)]
    results = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        await asyncio.sleep(throttle_delay)

    results.sort(key=lambda x: x[0])

    if retry_timing:
        if dropna:
            return [
                (result[1], result[2])
                for result in results
                if result[1] is not None
            ]
        return [(result[1], result[2]) for result in results]
    else:
        return to_list(
            [result[1] for result in results],
            flatten=flatten,
            dropna=dropna,
            unique=unique,
        )


async def bcall(
    input_: Any,
    func: Callable,
    /,
    batch_size: int,
    num_retries: int = 0,
    initial_delay: float = 0,
    retry_delay: float = 0,
    backoff_factor: float = 1,
    retry_default: Any = None,
    retry_timeout: Optional[float] = None,
    retry_timing: bool = False,
    verbose_retry: bool = True,
    error_msg: Optional[str] = None,
    error_map: Optional[Union[Dict, None]] = None,
    max_concurrent: Optional[int] = None,
    throttle_period: Optional[float] = None,
    **kwargs: Any,
) -> AsyncGenerator:
    """
    Asynchronously call a function in batches with retry and timing options.

    Args:
        input_: The input data to process.
        func: The function to call.
        batch_size: The size of each batch.
        num_retries: Number of retries per call.
        initial_delay: Initial delay before first attempt.
        retry_delay: Delay between retry attempts.
        backoff_factor: Factor to increase delay after each retry.
        retry_default: Default value for failed calls.
        retry_timeout: Timeout for function execution.
        retry_timing: If True, return execution time.
        verbose_retry: If True, print retry messages.
        error_msg: Custom error message prefix.
        error_map: Dict mapping exception types to handlers.
        max_concurrent: Maximum concurrent executions.
        throttle_period: Minimum time between calls.
        **kwargs: Additional function arguments.

    Yields:
        List of results for each batch.

    Example:
        >>> async def square(x): return x * 2
        >>> async for batch in bcall([1,2,3,4], square, batch_size=2):
        ...     print(batch)  # [2,4] then [6,8]
    """
    input_ = to_list(input_, flatten=True, dropna=True)

    for i in range(0, len(input_), batch_size):
        batch = input_[i : i + batch_size]  # noqa: E203
        batch_results = await lcall(
            batch,
            func,
            num_retries=num_retries,
            initial_delay=initial_delay,
            retry_delay=retry_delay,
            backoff_factor=backoff_factor,
            retry_default=retry_default,
            retry_timeout=retry_timeout,
            retry_timing=retry_timing,
            verbose_retry=verbose_retry,
            error_msg=error_msg,
            error_map=error_map,
            max_concurrent=max_concurrent,
            throttle_period=throttle_period,
            **kwargs,
        )
        yield batch_results


async def mcall(
    input_: Any,
    func: Union[Callable, Sequence],
    /,
    *,
    explode: bool = False,
    num_retries: int = 0,
    initial_delay: float = 0,
    retry_delay: float = 0,
    backoff_factor: float = 1,
    retry_default: Any = LN_UNDEFINED,
    retry_timeout: Optional[float] = None,
    retry_timing: bool = False,
    verbose_retry: bool = True,
    error_msg: Optional[str] = None,
    error_map: Optional[Union[Dict, None]] = None,
    max_concurrent: Optional[int] = None,
    throttle_period: Optional[float] = None,
    dropna: bool = False,
    **kwargs: Any,
) -> List:
    """
    Apply functions over inputs asynchronously with customizable options.

    Args:
        input_: The input data to process.
        func: Function or sequence of functions to apply.
        explode: If True, apply each function to all inputs.
        num_retries: Number of retry attempts.
        initial_delay: Initial execution delay.
        retry_delay: Delay between retries.
        backoff_factor: Retry delay increase factor.
        retry_default: Default value for failed calls.
        retry_timeout: Function execution timeout.
        retry_timing: If True, return execution time.
        verbose_retry: If True, print retry messages.
        error_msg: Custom error message prefix.
        error_map: Dict mapping exception types to handlers.
        max_concurrent: Maximum concurrent executions.
        throttle_period: Minimum time between calls.
        dropna: If True, remove None results.
        **kwargs: Additional function arguments.

    Returns:
        List of results, optionally with timing.

    Raises:
        ValueError: If input/function lengths mismatch.

    Example:
        >>> async def double(x): return x * 2
        >>> async def triple(x): return x * 3
        >>> await mcall([1, 2], [double, triple])  # [2, 6]
        >>> await mcall(1, [double, triple], explode=True)  # [2, 3]
    """
    input_ = to_list(input_, flatten=False, dropna=False)
    functions = to_list(func, flatten=False, dropna=False)

    if explode:
        tasks = [
            lcall(
                input_,
                f,
                num_retries=num_retries,
                initial_delay=initial_delay,
                retry_delay=retry_delay,
                backoff_factor=backoff_factor,
                retry_default=retry_default,
                retry_timeout=retry_timeout,
                retry_timing=retry_timing,
                verbose_retry=verbose_retry,
                error_msg=error_msg,
                error_map=error_map,
                max_concurrent=max_concurrent,
                throttle_period=throttle_period,
                dropna=dropna,
                **kwargs,
            )
            for f in functions
        ]
        return await asyncio.gather(*tasks)

    elif len(functions) == 1:
        tasks = [
            ucall(
                functions[0],
                inp,
                error_map=error_map,
                **kwargs,
            )
            for inp in input_
        ]
        return await asyncio.gather(*tasks)

    elif len(input_) == len(functions):
        tasks = [
            ucall(
                f,
                inp,
                error_map=error_map,
                **kwargs,
            )
            for inp, f in zip(input_, functions)
        ]
        return await asyncio.gather(*tasks)

    else:
        raise ValueError(
            "Input and function lengths must match when not using explode=True"
        )


async def tcall(
    func: Callable,
    /,
    *args: Any,
    initial_delay: float = 0,
    error_msg: Optional[str] = None,
    suppress_err: bool = False,
    retry_timing: bool = False,
    retry_timeout: Optional[float] = None,
    retry_default: Any = None,
    error_map: Optional[Union[Dict, None]] = None,
    **kwargs: Any,
) -> Union[T, Tuple]:
    """
    Execute a function asynchronously with timing and error handling.

    Args:
        func: The function to execute (coroutine or regular).
        *args: Positional arguments for the function.
        initial_delay: Delay before execution (seconds).
        error_msg: Custom error message prefix.
        suppress_err: If True, return default on error.
        retry_timing: If True, return execution duration.
        retry_timeout: Timeout for function execution.
        retry_default: Value to return if error occurs.
        error_map: Dict mapping exception types to handlers.
        **kwargs: Additional function arguments.

    Returns:
        Result or (result, duration) if timing enabled.

    Example:
        >>> async def slow_func(x):
        ...     await asyncio.sleep(1)
        ...     return x * 2
        >>> result, duration = await tcall(
        ...     slow_func, 5, retry_timing=True
        ... )
    """
    start = asyncio.get_event_loop().time()

    try:
        await asyncio.sleep(initial_delay)
        result = None

        if asyncio.iscoroutinefunction(func):
            if retry_timeout is None:
                result = await func(*args, **kwargs)
            else:
                result = await asyncio.wait_for(
                    func(*args, **kwargs), timeout=retry_timeout
                )
        else:
            if retry_timeout is None:
                result = func(*args, **kwargs)
            else:
                result = await asyncio.wait_for(
                    asyncio.shield(asyncio.to_thread(func, *args, **kwargs)),
                    timeout=retry_timeout,
                )

        duration = asyncio.get_event_loop().time() - start
        return (result, duration) if retry_timing else result

    except asyncio.TimeoutError as e:
        error_msg = f"{error_msg or ''} Timeout {retry_timeout}s exceeded"
        if suppress_err:
            duration = asyncio.get_event_loop().time() - start
            return (retry_default, duration) if retry_timing else retry_default
        raise asyncio.TimeoutError(error_msg) from e

    except Exception as e:
        if error_map and type(e) in error_map:
            error_map[type(e)](e)
            duration = asyncio.get_event_loop().time() - start
            return (None, duration) if retry_timing else None

        error_msg = (
            f"{error_msg} Error: {e}" if error_msg else f"Execution error: {e}"
        )
        if suppress_err:
            duration = asyncio.get_event_loop().time() - start
            return (retry_default, duration) if retry_timing else retry_default
        raise RuntimeError(error_msg) from e


async def rcall(
    func: Callable,
    /,
    *args: Any,
    num_retries: int = 0,
    initial_delay: float = 0,
    retry_delay: float = 0,
    backoff_factor: float = 1,
    retry_default: Any = LN_UNDEFINED,
    retry_timeout: Optional[float] = None,
    retry_timing: bool = False,
    verbose_retry: bool = True,
    error_msg: Optional[str] = None,
    error_map: Optional[Union[Dict, None]] = None,
    **kwargs: Any,
) -> Union[T, Tuple]:
    """
    Retry a function asynchronously with customizable options.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        num_retries: Number of retry attempts.
        initial_delay: Delay before first attempt.
        retry_delay: Delay between retry attempts.
        backoff_factor: Factor to increase delay after each retry.
        retry_default: Value to return if all attempts fail.
        retry_timeout: Timeout for each function execution.
        retry_timing: If True, return execution duration.
        verbose_retry: If True, print retry messages.
        error_msg: Custom error message prefix.
        error_map: Dict mapping exception types to handlers.
        **kwargs: Additional function arguments.

    Returns:
        Result or (result, duration) if timing enabled.

    Example:
        >>> async def flaky_func(x):
        ...     if random.random() < 0.5:
        ...         raise ValueError("Random failure")
        ...     return x * 2
        >>> result = await rcall(
        ...     flaky_func, 5, num_retries=3
        ... )
    """
    last_exception = None

    await asyncio.sleep(initial_delay)
    for attempt in range(num_retries + 1):
        try:
            if num_retries == 0:
                return await tcall(
                    func,
                    *args,
                    retry_timeout=retry_timeout,
                    retry_timing=retry_timing,
                    **kwargs,
                )

            err_msg = (
                f"Attempt {attempt + 1}/{num_retries + 1}: {error_msg or ''}"
            )
            if retry_timing:
                start_time = _t()
                result = await tcall(
                    func,
                    *args,
                    error_msg=err_msg,
                    retry_timeout=retry_timeout,
                    **kwargs,
                )
                duration = _t() - start_time
                return result, duration

            return await tcall(
                func,
                *args,
                error_msg=err_msg,
                retry_timeout=retry_timeout,
                **kwargs,
            )

        except Exception as e:
            last_exception = e
            if error_map and type(e) in error_map:
                error_map[type(e)](e)
            if attempt < num_retries:
                if verbose_retry:
                    print(
                        f"Attempt {attempt + 1}/{num_retries + 1} "
                        f"failed: {e}, retrying..."
                    )
                await asyncio.sleep(retry_delay)
                retry_delay *= backoff_factor
            else:
                break

    if retry_default is not LN_UNDEFINED:
        return retry_default

    if last_exception is not None:
        if error_map and type(last_exception) in error_map:
            handler = error_map[type(last_exception)]
            if asyncio.iscoroutinefunction(handler):
                return await handler(last_exception)
            return handler(last_exception)

        raise RuntimeError(
            f"{error_msg or ''} Failed after {num_retries + 1} "
            f"attempts: {last_exception}"
        ) from last_exception

    raise RuntimeError(
        f"{error_msg or ''} Failed after {num_retries + 1} attempts"
    )


async def alcall(
    input_: List,
    func: Callable,
    /,
    num_retries: int = 0,
    initial_delay: float = 0,
    retry_delay: float = 0,
    backoff_factor: float = 1,
    retry_default: Any = LN_UNDEFINED,
    retry_timeout: float = None,
    retry_timing: bool = False,
    verbose_retry: bool = True,
    error_msg: str = None,
    error_map: Dict = None,
    max_concurrent: Optional[int] = None,
    throttle_period: Optional[float] = None,
    flatten: bool = False,
    dropna: bool = False,
    unique: bool = False,
    **kwargs: Any,
) -> list:
    """Apply a function to each element of a list asynchronously with options.

    Args:
        input_: List of inputs to be processed.
        func: Async or sync function to apply to each input element.
        num_retries: Number of retry attempts for each function call.
        initial_delay: Initial delay before starting execution (seconds).
        retry_delay: Delay between retry attempts (seconds).
        backoff_factor: Factor by which delay increases after each attempt.
        retry_default: Default value to return if all attempts fail.
        retry_timeout: Timeout for each function execution (seconds).
        retry_timing: If True, return execution duration for each call.
        verbose_retry: If True, print retry messages.
        error_msg: Custom error message prefix for exceptions.
        error_map: Dict mapping exception types to error handlers.
        max_concurrent: Maximum number of concurrent executions.
        throttle_period: Minimum time between function executions (seconds).
        flatten: If True, flatten the resulting list.
        dropna: If True, remove None values from the result.
        **kwargs: Additional keyword arguments passed to func.

    Returns:
        list[T] | list[tuple[T, float]]: List of results, optionally with
        execution times if retry_timing is True.

    Raises:
        asyncio.TimeoutError: If execution exceeds retry_timeout.
        Exception: Any exception raised by func if not handled by error_map.

    Examples:
        >>> async def square(x):
        ...     return x * x
        >>> await alcall([1, 2, 3], square)
        [1, 4, 9]
        >>> await alcall([1, 2, 3], square, retry_timing=True)
        [(1, 0.001), (4, 0.001), (9, 0.001)]

    Note:
        - Uses semaphores for concurrency control if max_concurrent is set.
        - Supports both synchronous and asynchronous functions for `func`.
        - Results are returned in the original input order.
    """
    if initial_delay:
        await asyncio.sleep(initial_delay)

    semaphore = asyncio.Semaphore(max_concurrent) if max_concurrent else None
    throttle_delay = throttle_period if throttle_period else 0

    async def _task(i: Any, index: int) -> Any:
        if semaphore:
            async with semaphore:
                return await _execute_task(i, index)
        else:
            return await _execute_task(i, index)

    async def _execute_task(i: Any, index: int) -> Any:
        attempts = 0
        current_delay = retry_delay
        while True:
            try:
                if retry_timing:
                    start_time = asyncio.get_event_loop().time()
                    result = await asyncio.wait_for(
                        ucall(func, i, **kwargs), retry_timeout
                    )
                    end_time = asyncio.get_event_loop().time()
                    return index, result, end_time - start_time
                else:
                    result = await asyncio.wait_for(
                        ucall(func, i, **kwargs), retry_timeout
                    )
                    return index, result
            except asyncio.TimeoutError as e:
                raise asyncio.TimeoutError(
                    f"{error_msg or ''} Timeout {retry_timeout} seconds "
                    "exceeded"
                ) from e
            except Exception as e:
                if error_map and type(e) in error_map:
                    handler = error_map[type(e)]
                    if asyncio.iscoroutinefunction(handler):
                        return index, await handler(e)
                    else:
                        return index, handler(e)
                attempts += 1
                if attempts <= num_retries:
                    if verbose_retry:
                        print(
                            f"Attempt {attempts}/{num_retries} failed: {e}"
                            ", retrying..."
                        )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
                else:
                    if retry_default is not LN_UNDEFINED:
                        return index, retry_default
                    raise e

    tasks = [_task(i, index) for index, i in enumerate(input_)]
    results = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        await asyncio.sleep(throttle_delay)

    results.sort(
        key=lambda x: x[0]
    )  # Sort results based on the original index

    if retry_timing:
        if dropna:
            return [
                (result[1], result[2])
                for result in results
                if result[1] is not None
            ]
        else:
            return [(result[1], result[2]) for result in results]
    else:
        return to_list(
            [result[1] for result in results],
            flatten=flatten,
            dropna=dropna,
            unique=unique,
        )


__all__ = [
    "tcall",
    "rcall",
    "ucall",
    "pcall",
    "lcall",
    "bcall",
    "mcall",
]
