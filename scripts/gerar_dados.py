"""
gerar_dados.py
--------------
Gera dados_sensores_fase2.csv com 100 leituras simuladas dos sensores do
sistema de irrigacao de mudas de Araucaria angustifolia (FarmTech Fase 2/3).

A regra de decisao de irrigacao replica fielmente a logica do firmware
embarcado no ESP32 (src/sketch.ino):

    ph_ok          = (ph >= 5) AND (ph <= 7)
    encharcado     = umidade > 75.0
    solo_seco      = umidade < 60.0
    nutrientes_ok  = (p == 1) AND (n == 1 OR k == 1)
    irrigou        = solo_seco AND ph_ok AND (NOT encharcado) AND nutrientes_ok

O termo (NOT encharcado) e logicamente redundante - solo_seco ja implica
umidade <= 75 - porem e mantido para 100% de fidelidade ao firmware.

Sem dependencias externas: apenas csv, random e datetime.
"""

import csv
import random
from datetime import datetime, timedelta


# ============================================================================
# Constantes
# ============================================================================

# --- Limiares fisicos do firmware (sketch.ino) ---
PH_MIN, PH_MAX = 5, 7
UMID_SECA, UMID_ENCHARCADO = 60.0, 75.0

# --- Configuracao da serie ---
SEMENTE = 20260401
N_LEITURAS = 100
INICIO = datetime(2026, 4, 1, 8, 0, 0)
INTERVALO_MIN, INTERVALO_MAX = 28, 32       # minutos entre leituras

# --- Dominios fisicos / clamping ---
UMID_LIMITE = (30.0, 95.0)
TEMP_LIMITE = (12.0, 28.0)

# --- Ciclo diurno (Curitiba/PR, outono) ---
HORA_TEMP_MIN, HORA_TEMP_MAX = 5.0, 15.0    # h em que ocorre min/max
TEMP_BASE_MIN, TEMP_BASE_MAX = 12.0, 26.0   # amplitude do ciclo (sem ruido)
RUIDO_TEMP_C = 1.5                          # +/- variacao aleatoria

# --- Saida ---
ARQUIVO_SAIDA = "dados_sensores_fase2.csv"
COLUNAS = ["timestamp", "n", "p", "k", "ph", "umidade", "temperatura", "irrigou"]


# ============================================================================
# Helpers numericos
# ============================================================================
def _clamp(x, limites):
    lo, hi = limites
    return max(lo, min(hi, x))


# ============================================================================
# Logica de irrigacao - copia fiel do firmware
# ============================================================================
def calcula_irrigou(n, p, k, ph, umidade):
    """1 se o firmware acionaria a bomba, 0 caso contrario.
    Reproduz EXATAMENTE a regra de decisao do sketch.ino."""
    ph_ok         = PH_MIN <= ph <= PH_MAX
    encharcado    = umidade > UMID_ENCHARCADO
    solo_seco     = umidade < UMID_SECA
    nutrientes_ok = (p == 1) and (n == 1 or k == 1)
    return int(solo_seco and ph_ok and (not encharcado) and nutrientes_ok)


# ============================================================================
# Temperatura com ciclo diurno (curva linear por partes)
# ============================================================================
def temperatura_diurna(dt):
    """Temperatura em C: minima ~12 as 05h, maxima ~26 as 15h,
    com ruido +/- 1.5 C. Arredondada a 1 casa decimal."""
    h = dt.hour + dt.minute / 60.0
    amplitude        = TEMP_BASE_MAX - TEMP_BASE_MIN
    duracao_subida   = HORA_TEMP_MAX - HORA_TEMP_MIN
    duracao_descida  = (HORA_TEMP_MIN + 24) - HORA_TEMP_MAX

    if HORA_TEMP_MIN <= h < HORA_TEMP_MAX:
        temp = TEMP_BASE_MIN + (h - HORA_TEMP_MIN) * amplitude / duracao_subida
    else:
        h_pos_pico = (h - HORA_TEMP_MAX) % 24
        temp = TEMP_BASE_MAX - h_pos_pico * amplitude / duracao_descida

    temp += random.uniform(-RUIDO_TEMP_C, RUIDO_TEMP_C)
    return round(_clamp(temp, TEMP_LIMITE), 1)


# ============================================================================
# Amostradores - cada um produz UMA leitura {n, p, k, ph, umid}
# ----------------------------------------------------------------------------
# IMPORTANTE: a ordem das chamadas a random.* dentro de cada amostrador eh
# deliberada. Mante-la garante que o CSV continue byte-identico para a
# mesma semente, qualquer que seja a refatoracao da estrutura externa.
# ============================================================================

def _amostra_seco_ideal():
    """Solo seco, pH ok, NPK ok (irrigou=1). K oscila."""
    umid = random.uniform(35.0, 55.0)
    ph   = random.randint(5, 7)
    return {"n": 1, "p": 1, "k": random.choice([0, 1]), "ph": ph, "umid": umid}


def _amostra_ph_fora():
    """Solo seco, NPK ok, mas pH fora da faixa (irrigou=0)."""
    umid = random.uniform(35.0, 55.0)
    ph   = random.choice([3, 4, 8, 9, 10])
    return {"n": 1, "p": 1, "k": 1, "ph": ph, "umid": umid}


def _amostra_sem_nk():
    """Solo seco, pH ok, P presente, N e K ausentes (irrigou=0)."""
    umid = random.uniform(35.0, 55.0)
    ph   = random.randint(5, 7)
    return {"n": 0, "p": 1, "k": 0, "ph": ph, "umid": umid}


def _amostra_recuperacao():
    """Solo seco, pH ok, P presente, garantindo N OU K presente (irrigou=1)."""
    umid = random.uniform(35.0, 58.0)
    ph   = random.randint(5, 7)
    n    = random.choice([0, 1])
    k    = 1 if n == 0 else random.choice([0, 1])
    return {"n": n, "p": 1, "k": k, "ph": ph, "umid": umid}


def _amostra_umidade_adequada():
    """Umidade na faixa 60-74 (alerta INFO do firmware, irrigou=0)."""
    umid = random.uniform(60.5, 74.5)
    ph   = random.randint(5, 7)
    return {"n": 1, "p": 1, "k": 1, "ph": ph, "umid": umid}


def _amostra_sem_fosforo():
    """Solo seco, pH ok, NK presentes, P ausente (irrigou=0)."""
    umid = random.uniform(35.0, 55.0)
    ph   = random.randint(5, 7)
    return {"n": 1, "p": 0, "k": 1, "ph": ph, "umid": umid}


def _amostra_tudo_ok():
    """Solo seco, pH ok, NPK = (1, 1, 1) (irrigou=1)."""
    umid = random.uniform(35.0, 55.0)
    ph   = random.randint(5, 7)
    return {"n": 1, "p": 1, "k": 1, "ph": ph, "umid": umid}


class _UmidadeMonotonica:
    """Base de amostradores cuja umidade evolui monotonicamente.

    Encapsula o padrao 'umidade += delta com clamp em um dos lados'.
    Sinal +1 = chuva (umidade sobe ate `umid_limite`),
    sinal -1 = secagem (umidade cai ate `umid_limite`).
    """

    def __init__(self, umid_inicial, umid_limite, delta_range, sinal):
        self.umid        = umid_inicial
        self.umid_limite = umid_limite
        self.delta_range = delta_range
        self.sinal       = sinal

    def _proximo_umid(self):
        novo = self.umid + self.sinal * random.uniform(*self.delta_range)
        self.umid = (min(self.umid_limite, novo) if self.sinal > 0
                     else max(self.umid_limite, novo))
        return self.umid


class _GeradorChuva(_UmidadeMonotonica):
    """Umidade sobe progressivamente ate 92% (irrigou=0)."""

    def __init__(self):
        super().__init__(umid_inicial=62.0, umid_limite=92.0,
                         delta_range=(0.5, 3.5), sinal=+1)

    def __call__(self):
        umid = self._proximo_umid()
        ph   = random.randint(5, 7)
        return {"n": 1, "p": 1, "k": 1, "ph": ph, "umid": umid}


class _GeradorSecagem(_UmidadeMonotonica):
    """Umidade cai progressivamente de 80 a 40; nitrogenio oscila."""

    def __init__(self):
        super().__init__(umid_inicial=80.0, umid_limite=40.0,
                         delta_range=(1.5, 3.5), sinal=-1)

    def __call__(self):
        umid = self._proximo_umid()
        ph   = random.randint(5, 7)
        n    = random.choice([0, 1])
        return {"n": n, "p": 1, "k": 1, "ph": ph, "umid": umid}


# ============================================================================
# Montagem do dataset
# ============================================================================
def _avancar_relogio(ts):
    """Avanca o relogio em 28 a 32 minutos (uniforme)."""
    return ts + timedelta(minutes=random.randint(INTERVALO_MIN, INTERVALO_MAX))


def _montar_linha(ts, n, p, k, ph, umid, temp):
    """Aplica clamp na umidade e calcula 'irrigou' pela regra do firmware."""
    umid = round(_clamp(umid, UMID_LIMITE), 1)
    return {
        "timestamp":   ts.strftime("%Y-%m-%d %H:%M:%S"),
        "n": n, "p": p, "k": k, "ph": ph,
        "umidade": umid, "temperatura": temp,
        "irrigou": calcula_irrigou(n, p, k, ph, umid),
    }


def _linha_sanidade(ts):
    """Reproduz exatamente a primeira leitura do Serial Monitor da Fase 2.
    24 C as 08h e otimista para Curitiba/abril, mas e o valor exibido na
    documentacao do firmware - mantemos identico para servir de referencia."""
    return _montar_linha(ts=ts, n=1, p=1, k=1, ph=5, umid=50.0, temp=24.0)


def gerar():
    """Gera as 100 leituras em blocos tematicos que exercitam todos os
    alertas do firmware. A primeira linha eh sempre a sanidade do Serial."""
    random.seed(SEMENTE)

    # (nome, n_leituras, amostrador). A ordem aqui define a serie temporal.
    blocos = (
        ("seco - condicoes ideais",        12, _amostra_seco_ideal),
        ("chuva chegando (encharcamento)", 17, _GeradorChuva()),
        ("secagem gradual",                15, _GeradorSecagem()),
        ("pH fora da faixa",               10, _amostra_ph_fora),
        ("ausencia de N e K",              10, _amostra_sem_nk),
        ("recuperacao (irriga novamente)", 13, _amostra_recuperacao),
        ("umidade adequada (60-74)",       10, _amostra_umidade_adequada),
        ("ausencia de fosforo",             7, _amostra_sem_fosforo),
        ("normalizacao final",              5, _amostra_tudo_ok),
    )

    ts = INICIO
    linhas = [_linha_sanidade(ts)]
    for _, n_iter, amostrador in blocos:
        for _ in range(n_iter):
            ts = _avancar_relogio(ts)
            amostra = amostrador()
            linhas.append(_montar_linha(ts=ts, temp=temperatura_diurna(ts), **amostra))

    assert len(linhas) == N_LEITURAS, (
        f"Esperado {N_LEITURAS} linhas, gerou {len(linhas)}"
    )
    return linhas


# ============================================================================
# Validacao e persistencia
# ============================================================================
def validar(linhas):
    """Retorna lista de (indice, linha, irrigou_esperado) para inconsistencias.
    Lista vazia significa que todas as linhas batem com a regra do firmware."""
    erros = []
    for i, linha in enumerate(linhas, start=1):
        esperado = calcula_irrigou(linha["n"], linha["p"], linha["k"],
                                   linha["ph"], linha["umidade"])
        if esperado != linha["irrigou"]:
            erros.append((i, linha, esperado))
    return erros


def escrever_csv(linhas, caminho=ARQUIVO_SAIDA):
    """Escreve o CSV em UTF-8, sem BOM, separador virgula."""
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS)
        writer.writeheader()
        writer.writerows(linhas)


# ============================================================================
# Entry point
# ============================================================================
def _relatar_distribuicao(linhas):
    total = len(linhas)
    n_irr = sum(1 for l in linhas if l["irrigou"] == 1)
    pct   = 100.0 * n_irr / total
    print(f"\nArquivo gerado : {ARQUIVO_SAIDA}")
    print(f"Total leituras : {total}")
    print(f"irrigou = 1    : {n_irr} ({pct:.1f}%)")
    print(f"irrigou = 0    : {total - n_irr} ({100.0 - pct:.1f}%)")


def main():
    linhas = gerar()
    erros = validar(linhas)
    if erros:
        print(f"[AVISO] {len(erros)} linha(s) com 'irrigou' inconsistente. Corrigindo...")
        for i, linha, esperado in erros:
            print(f"  linha {i}: {linha} -> esperado {esperado}")
            linha["irrigou"] = esperado
        assert not validar(linhas), "Inconsistencias persistem apos correcao."
    else:
        print(f"[OK] Todas as {N_LEITURAS} linhas tem 'irrigou' consistente com a logica do sketch.")
    escrever_csv(linhas)
    _relatar_distribuicao(linhas)


if __name__ == "__main__":
    main()
