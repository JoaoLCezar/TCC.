import re


def only_digits(value: str) -> str:
    return re.sub(r"\D+", "", (value or ""))


def is_valid_cpf(cpf: str) -> bool:
    """Valida um CPF (aceita com ou sem formatação). Retorna True se válido."""
    cpf = only_digits(cpf)
    if not cpf or len(cpf) != 11:
        return False

    # Rejeita sequências de mesmos dígitos (ex: 00000000000)
    if cpf == cpf[0] * 11:
        return False

    def calc_digit(cpf_part: str) -> int:
        soma = 0
        peso = len(cpf_part) + 1
        for ch in cpf_part:
            soma += int(ch) * peso
            peso -= 1
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    d1 = calc_digit(cpf[:9])
    d2 = calc_digit(cpf[:9] + str(d1))

    return cpf.endswith(f"{d1}{d2}")


def format_cpf(cpf: str) -> str:
    """Formata CPF como 000.000.000-00"""
    cpf = only_digits(cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"
