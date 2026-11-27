"""Operator-defined defaults; explicit commercial data always wins."""

from decimal import Decimal, InvalidOperation


class CommercialDefaults:
    @staticmethod
    def apply(fields, *, avulso=False):
        fields = dict(fields)
        decisions = []
        if avulso and not fields.get("finalidade"):
            try:
                value = Decimal(str(fields.get("valor")))
                if value.is_finite() and value > 0:
                    fields["finalidade"] = "aluguel" if value < 100000 else "venda"
                    decisions.append({"rule": "AVULSO_FINALIDADE_POR_VALOR", "value": str(value),
                                      "purpose": fields["finalidade"], "threshold": "100000.00"})
            except (InvalidOperation, ValueError, TypeError):
                pass
        return fields, decisions
