from typing import Tuple


PH_MIN, PH_MAX = 5, 7
UMID_SECA, UMID_ENCHARCADO = 60.0, 75.0


def decisao_firmware(n: int, p: int, k: int, ph: int, umidade: float) -> Tuple[bool, str]:
    if ph < PH_MIN or ph > PH_MAX:
        return False, "pH fora da faixa ideal (5 a 7)"
    if umidade > UMID_ENCHARCADO:
        return False, "Solo encharcado — risco de podridao radicular"
    if p == 0:
        return False, "Fosforo ausente — critico para enraizamento"
    if umidade >= UMID_SECA:
        return False, "Umidade adequada — irrigacao desnecessaria"
    if n == 0 and k == 0:
        return False, "Faltam nutrientes secundarios (N e K)"
    return True, "Solo seco com condicoes ideais"


def decisao_final(
    firmware_ok: bool, motivo: str, vai_chover: bool
) -> Tuple[str, str, str]:
    if not firmware_ok:
        return "NAO IRRIGAR", motivo, "negativo"
    if vai_chover:
        return (
            "SUSPENDER",
            "Solo precisaria de irrigacao, mas ha chuva prevista para as proximas 12h. "
            "Suspender economiza agua.",
            "atencao",
        )
    return (
        "IRRIGAR",
        "Solo seco com condicoes agronomicas ideais e sem chuva prevista. Acionar a bomba.",
        "positivo",
    )
