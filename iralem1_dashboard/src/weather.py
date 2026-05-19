import os

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
CIDADE = "Curitiba,BR"
URL_BASE = "https://api.openweathermap.org/data/2.5/forecast"
LIMIAR_POP_PCT = 50
LIMIAR_CHUVA_MM = 1.0


@st.cache_data(ttl=600, show_spinner=False)
def buscar_previsao(horas: int = 12) -> dict | None:
    if not API_KEY:
        return None
    try:
        resposta = requests.get(
            URL_BASE,
            params={
                "q": CIDADE,
                "appid": API_KEY,
                "units": "metric",
                "lang": "pt_br",
            },
            timeout=10,
        )
        resposta.raise_for_status()
        bruto = resposta.json()
    except Exception:
        return None

    qtd = max(1, horas // 3)
    slots = bruto.get("list", [])[:qtd]
    return {
        "cidade": bruto.get("city", {}).get("name", CIDADE),
        "slots": [
            {
                "dt": s["dt"],
                "temperatura": s["main"]["temp"],
                "descricao": s["weather"][0]["description"].capitalize(),
                "pop": s.get("pop", 0) * 100,
                "chuva_mm": s.get("rain", {}).get("3h", 0),
                "icone": s["weather"][0]["icon"],
            }
            for s in slots
        ],
    }


def chuva_prevista(previsao: dict | None) -> bool:
    if not previsao or not previsao.get("slots"):
        return False
    pop_max = max(s["pop"] for s in previsao["slots"])
    mm_total = sum(s["chuva_mm"] for s in previsao["slots"])
    return pop_max >= LIMIAR_POP_PCT or mm_total >= LIMIAR_CHUVA_MM
