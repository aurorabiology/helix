import heapq
import itertools
import time
import logging
import asyncio
from typing import Callable, Any, Optional, Tuple

logger = logging.getLogger("helixlang.simulation.scheduler")

class Scheduler:
    """
    HelixLang core scheduler for multi-scale biological simulations.

    Supports:
    - Discrete event scheduling with precise time ordering.
    - Time-stepped simulation mode for continuous updates.
    - Concurrent execution of independent events.
    """

    def __init__(self, time_unit: float = 1e-3):
        """
        Args:
            time_unit (float): Base simulation time unit in seconds (default 1ms).
        """
        self._time_unit = time_unit
        self._current_time = 0.0
        self._event_queue = []  # Priority queue for discrete events
        self._counter = itertools.count()  # Unique sequence count for event ordering
        self._running = False
        self._paused = False
        self._loop = None  # asyncio event loop for concurrency support
        self._scheduled_tasks = set()
        logger.info(f"Scheduler initialized with time_unit={time_unit}s")

    @property
    def current_time(self) -> float:
        return self._current_time

    def schedule_event(self, delay: float, callback: Callable, *args, **kwargs) -> int:
        """
        Schedule a discrete event to occur after `delay` seconds.

        Args:
            delay (float): Time delay from current time in seconds.
            callback (Callable): Function to invoke when event fires.
            *args, **kwargs: Arguments for callback.

        Returns:
            int: Unique event ID.
        """
        event_time = self._current_time + delay
        event_id = next(self._counter)
        heapq.heappush(self._event_queue, (event_time, event_id, callback, args, kwargs))
        logger.debug(f"Event scheduled at t={event_time:.6f}s id={event_id} callback={callback.__name__}")
        return event_id

    def cancel_event(self, event_id: int) -> bool:
        """
        Cancel an event by event_id.

        Args:
            event_id (int): ID of event to cancel.

        Returns:
            bool: True if event was found and cancelled, False otherwise.
        """
        # Cancellation by event_id requires scanning the queue (inefficient).
        # Alternative: Maintain a separate dict or use a cancellation flag in callbacks.
        found = False
        new_queue = []
        while self._event_queue:
            evt = heapq.heappop(self._event_queue)
            if evt[1] == event_id:
                found = True
                logger.info(f"Event id={event_id} cancelled.")
                continue
            new_queue.append(evt)
        for evt in new_queue:
            heapq.heappush(self._event_queue, evt)
        return found

    def _pop_next_event(self) -> Optional[Tuple[float, int, Callable, tuple, dict]]:
        if not self._event_queue:
            return None
        return heapq.heappop(self._event_queue)

    def step(self, timestep: Optional[float] = None):
        """
        Advance simulation time by timestep (for time-stepped scheduling),
        and process all discrete events scheduled up to the new time.

        Args:
            timestep (float): Time increment to advance, defaults to base time_unit.
        """
        if timestep is None:
            timestep = self._time_unit

        target_time = self._current_time + timestep
        logger.debug(f"Simulation stepping from {self._current_time:.6f}s to {target_time:.6f}s")

        # Process all discrete events scheduled <= target_time
        while self._event_queue and self._event_queue[0][0] <= target_time:
            event_time, event_id, callback, args, kwargs = self._pop_next_event()
            self._current_time = event_time
            try:
                logger.debug(f"Processing event id={event_id} at t={event_time:.6f}s callback={callback.__name__}")
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception during event id={event_id} at t={event_time:.6f}s: {e}")

        # Advance current time to target if no earlier event
        self._current_time = target_time

    async def _async_run_event(self, callback: Callable, *args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Async event exception: {e}")

    async def run_async(self, max_time: Optional[float] = None):
        """
        Async simulation runner processing events and time steps.

        Args:
            max_time (float): Simulation stop time in seconds.
        """
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        self._running = True
        logger.info("Async simulation run started")

        while self._running:
            if self._paused:
                await asyncio.sleep(0.01)
                continue

            if max_time is not None and self._current_time >= max_time:
                logger.info(f"Reached max simulation time {max_time}s, stopping.")
                break

            # Process discrete events due now or in the past
            while self._event_queue and self._event_queue[0][0] <= self._current_time:
                event_time, event_id, callback, args, kwargs = self._pop_next_event()
                self._current_time = event_time
                task = self._loop.create_task(self._async_run_event(callback, *args, **kwargs))
                self._scheduled_tasks.add(task)
                task.add_done_callback(self._scheduled_tasks.discard)

            # Advance time by base time unit if no immediate event
            self._current_time += self._time_unit
            await asyncio.sleep(0)  # Yield control

        logger.info("Async simulation run stopped")

    def run(self, duration: float, timestep: Optional[float] = None):
        """
        Run simulation synchronously for a given duration in seconds.

        Args:
            duration (float): Total time to run simulation.
            timestep (float): Optional timestep for time-stepped mode.
        """
        logger.info(f"Running simulation synchronously for {duration}s")
        end_time = self._current_time + duration
        while self._current_time < end_time:
            self.step(timestep)

    def pause(self):
        self._paused = True
        logger.info("Simulation paused")

    def resume(self):
        self._paused = False
        logger.info("Simulation resumed")

    def stop(self):
        self._running = False
        logger.info("Simulation stopped")

    def reset(self):
        """
        Reset scheduler time and clear events.
        """
        self._current_time = 0.0
        self._event_queue.clear()
        self._counter = itertools.count()
        logger.info("Scheduler reset")

