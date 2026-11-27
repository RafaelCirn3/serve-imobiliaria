"""Explicit developer dispatch; layout adapters share the extraction pipeline."""
from .document import ExtractionError


def get_parser(profile):
    from .mga import MGATableParser
    from .setai import SetaiTableParser
    from .dwv import IconTableParser

    parsers = {"mga": MGATableParser, "setai": SetaiTableParser, "icon": IconTableParser}
    if profile not in parsers:
        raise ExtractionError("Perfil de extração desconhecido.")
    return parsers[profile]()
