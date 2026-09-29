import unicodedata

SERVICE_CITIES = ("João Pessoa", "Cabedelo", "Bananeiras")


def normalized(value):
    text = " ".join(str(value or "").split())
    return "".join(char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)).casefold()


def canonical_city(value):
    return next((city for city in SERVICE_CITIES if normalized(city) == normalized(value)), None)
