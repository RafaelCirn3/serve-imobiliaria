import hashlib
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.exceptions import Throttled

from .normalization import canonical_city


class LocationUnavailable(APIException):
    status_code = 503
    default_detail = "Consulta de endereço indisponível. Preencha manualmente ou tente novamente."


def fetch_json(url):
    try:
        request = Request(url, headers={"User-Agent": settings.LOCATION_USER_AGENT, "Accept": "application/json"})
        with urlopen(request, timeout=settings.LOCATION_TIMEOUT) as response:
            raw = response.read(1024 * 1024)
            return json.loads(raw)
    except HTTPError as error:
        if error.code == 400:
            raise ValidationError("Endereço inválido para consulta.") from error
        raise LocationUnavailable() from error
    except (URLError, OSError, ValueError, TimeoutError) as error:
        raise LocationUnavailable() from error


def cached_json(url, seconds=86400):
    key = "location:" + hashlib.sha256(url.encode()).hexdigest()
    result = cache.get(key)
    if result is None:
        result = fetch_json(url)
        cache.set(key, result, seconds)
    return result


def lookup_cep(value):
    cep = str(value).replace("-", "").strip()
    if len(cep) != 8 or not cep.isascii() or not cep.isdigit():
        raise ValidationError({"cep": "Informe um CEP com oito dígitos."})
    data = cached_json(f"https://viacep.com.br/ws/{cep}/json/")
    if not isinstance(data, dict):
        raise LocationUnavailable()
    if data.get("erro"):
        raise NotFound("CEP não encontrado. Preencha o endereço manualmente.")
    return data


def search_address(city, street):
    city = canonical_city(city)
    street = " ".join(str(street).split())
    if not city or len(street) < 3 or len(street) > 255:
        raise ValidationError("Selecione uma cidade atendida e informe ao menos três caracteres da rua.")
    data = cached_json(f"https://viacep.com.br/ws/PB/{quote(city, safe='')}/{quote(street, safe='')}/json/")
    if not isinstance(data, list):
        raise LocationUnavailable()
    return data[:50]


def geocode_address(data):
    city = canonical_city(data.get("cidade", ""))
    street = " ".join(str(data.get("logradouro", "")).split())
    if not city or len(street) < 3 or len(street) > 255:
        raise ValidationError("Informe cidade atendida e rua com ao menos três caracteres.")
    number = str(data.get("numero", "")).strip()[:30]
    query = ", ".join(part for part in (street, number, str(data.get("bairro", "")).strip()[:120], city, "Paraíba", "Brasil") if part)
    key = "geocode:" + hashlib.sha256(query.encode()).hexdigest()
    cached = cache.get(key)
    if cached is not None:
        return cached
    # Keep the lock longer than the timeout to serialize provider requests.
    if not cache.add("geocode:provider-lock", True, settings.LOCATION_TIMEOUT + 1):
        raise Throttled(wait=1, detail="Aguarde antes de consultar outra localização.")
    parameters = urlencode({"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "br", "addressdetails": 1})
    results = fetch_json(settings.GEOCODER_URL + "?" + parameters)
    if not isinstance(results, list):
        raise LocationUnavailable()
    if not results:
        raise NotFound("Localização não encontrada. Informe as coordenadas manualmente.")
    try:
        latitude, longitude = float(results[0]["lat"]), float(results[0]["lon"])
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("Invalid coordinate")
    except (KeyError, ValueError, TypeError) as error:
        raise LocationUnavailable() from error
    result = {"latitude": latitude, "longitude": longitude, "localizacao_exata": False,
              "descricao": results[0].get("display_name", ""), "atribuicao": "© OpenStreetMap contributors"}
    cache.set(key, result, 30 * 86400)
    return result
