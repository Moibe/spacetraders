"""Limitador de peticiones para la API de SpaceTraders.

La API publica sus limites en las cabeceras de cada respuesta:

    X-RateLimit-Limit-Per-Second: 2
    X-RateLimit-Limit-Burst: 30

Es decir: 2 req/s sostenidas, con un pozo de rafaga de 30. Eso se modela con un
token bucket: capacidad 30, recarga 2 tokens por segundo. Permite quemar 30
peticiones de golpe (util al arrancar, cuando hay que leer flota + contratos +
mercados) y despues se acomoda al ritmo sostenido.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

DEFAULT_RATE_PER_SECOND = 2.0
DEFAULT_BURST = 30


class RateLimiter:
    """Token bucket seguro entre hilos.

    El reloj y el sleep se inyectan para poder testear sin esperar de verdad.
    """

    def __init__(
        self,
        rate_per_second: float = DEFAULT_RATE_PER_SECOND,
        burst: int = DEFAULT_BURST,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if rate_per_second <= 0:
            raise ValueError("rate_per_second debe ser > 0")
        if burst < 1:
            raise ValueError("burst debe ser >= 1")

        self.rate_per_second = rate_per_second
        self.burst = burst
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._tokens = float(burst)
        self._updated_at = clock()

    def _refill(self) -> None:
        ahora = self._clock()
        transcurrido = ahora - self._updated_at
        if transcurrido > 0:
            self._tokens = min(self.burst, self._tokens + transcurrido * self.rate_per_second)
            self._updated_at = ahora

    @property
    def available(self) -> float:
        """Tokens disponibles ahora mismo (informativo, para logs y tests)."""
        with self._lock:
            self._refill()
            return self._tokens

    def acquire(self) -> float:
        """Consume un token, esperando si hace falta. Devuelve los segundos esperados."""
        esperado = 0.0
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return esperado
                faltante = 1 - self._tokens
                espera = faltante / self.rate_per_second
            # Se espera fuera del lock para no bloquear a los demas hilos.
            self._sleep(espera)
            esperado += espera

    def penalize(self, seconds: float) -> None:
        """Vacia el pozo y atrasa la recarga `seconds`.

        Se usa al recibir un 429: la API ya nos dijo que vamos rapido, asi que no
        alcanza con esperar el `Retry-After`, tambien hay que dejar el bucket seco
        para no volver a dispararle de inmediato.
        """
        if seconds <= 0:
            return
        with self._lock:
            self._tokens = 0.0
            self._updated_at = self._clock() + seconds
