from pathlib import Path

import pandas as pd
import streamlit as st


CAMINHO_CSV = (
    Path(__file__).resolve().parent.parent.parent
    / "dados"
    / "dados_sensores_fase2.csv"
)


@st.cache_data
def carregar_leituras() -> pd.DataFrame:
    df = pd.read_csv(CAMINHO_CSV)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


def classificar_condicao(linha: pd.Series) -> str:
    if linha["ph"] < 5 or linha["ph"] > 7:
        return "pH fora da faixa"
    if linha["umidade"] > 75:
        return "Solo encharcado"
    if linha["p"] == 0:
        return "Fosforo ausente"
    if linha["umidade"] < 60:
        return "Solo seco - irrigar"
    return "Umidade adequada"
