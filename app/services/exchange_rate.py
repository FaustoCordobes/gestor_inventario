import requests

DOLAR_API_URL = "https://dolarapi.com/v1/dolares/oficial"


def get_dollar_rate():
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
