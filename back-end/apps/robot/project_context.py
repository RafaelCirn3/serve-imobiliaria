"""Project identities explicitly confirmed by the operator."""

from .profiles import normalize


def canonical_project(name):
    return "Mondo" if normalize(name) in ("mondo", "mondo 2") else name


def verified_context(name):
    if canonical_project(name) == "Mondo":
        return {"cidade":"João Pessoa", "bairro":"Bessa"}
    return {}
