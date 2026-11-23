import threading
import time

import requests

DOLAR_API_URL = "https://dolarapi.com/v1/dolares/oficial"

CACHE_SEGUNDOS = 600
REINTENTO_TRAS_ERROR_SEGUNDOS = 60

_lock = threading.Lock()
_cache = {"valor": None, "obtenida_en": 0.0, "fallo_en": None}


def _consultar_api():
    try:
        response = requests.get(DOLAR_API_URL, timeout=5)
        if response.status_code != 200:
            return None
        data = response.json()
        return {
            "buy": float(data["compra"]),
            "sell": float(data["venta"]),
            "updated_at": data.get("fechaActualizacion"),
        }
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return None


def get_dollar_rate():
    with _lock:
        ahora = time.monotonic()
        if _cache["valor"] is not None and ahora - _cache["obtenida_en"] < CACHE_SEGUNDOS:
            return _cache["valor"]
        if _cache["fallo_en"] is not None and ahora - _cache["fallo_en"] < REINTENTO_TRAS_ERROR_SEGUNDOS:
            return _cache["valor"]

        valor = _consultar_api()
        if valor is not None:
            _cache.update(valor=valor, obtenida_en=time.monotonic(), fallo_en=None)
        else:
            _cache["fallo_en"] = time.monotonic()
        return _cache["valor"]


def clear_cache():
    with _lock:
        _cache.update(valor=None, obtenida_en=0.0, fallo_en=None)
