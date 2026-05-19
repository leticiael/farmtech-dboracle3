from datetime import datetime

import streamlit as st

from src.data_loader import carregar_leituras, classificar_condicao
from src.charts import (
    serie_umidade_temperatura,
    timeline_bomba,
    serie_ph,
    heatmap_npk,
    donut_distribuicao,
    timeline_alertas,
)
from src.weather import API_KEY, buscar_previsao, chuva_prevista
from src.decisao import decisao_firmware, decisao_final


st.set_page_config(
    page_title="FarmTech - Painel da Araucaria",
    layout="wide",
    initial_sidebar_state="auto",
)


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 18% 0%, rgba(126, 188, 90, 0.10), transparent 45%),
        radial-gradient(circle at 95% 100%, rgba(59, 197, 221, 0.07), transparent 50%),
        radial-gradient(circle at 70% 30%, rgba(176, 147, 255, 0.04), transparent 40%),
        #0A0F0D;
    background-attachment: fixed;
}

.main .block-container {
    padding-top: 2.5rem;
    padding-bottom: 5rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1500px;
    animation: fadeInUp 0.6s cubic-bezier(.2,.7,.3,1) both;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0);   }
}

section[data-testid="stSidebar"] {
    background: rgba(20, 26, 23, 0.7) !important;
    backdrop-filter: blur(24px) saturate(140%);
    -webkit-backdrop-filter: blur(24px) saturate(140%);
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}
section[data-testid="stSidebar"] > div { background: transparent !important; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #F0F2EE; }
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #8B928D !important; }

[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.025);
    backdrop-filter: blur(20px) saturate(160%);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 22px 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
    transition: transform 0.25s cubic-bezier(.4,0,.2,1), box-shadow 0.25s, border-color 0.25s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(126, 188, 90, 0.12);
    border-color: rgba(126, 188, 90, 0.25);
}
[data-testid="stMetricLabel"] {
    color: #8B928D;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    white-space: normal !important;
    overflow: visible !important;
}
[data-testid="stMetricLabel"] > div {
    white-space: normal !important;
    overflow: visible !important;
}
[data-testid="stMetricValue"] {
    color: #F0F2EE;
    font-weight: 600;
    font-size: 2rem !important;
}

div[data-testid="stPlotlyChart"] {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(20px) saturate(160%);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 14px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
    transition: transform 0.25s cubic-bezier(.4,0,.2,1), border-color 0.25s, box-shadow 0.25s;
}
div[data-testid="stPlotlyChart"]:hover {
    transform: translateY(-1px);
    border-color: rgba(255, 255, 255, 0.10);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.4);
}

h1, h2, h3, h4 { color: #F0F2EE; font-weight: 600; }
h1 {
    letter-spacing: -0.02em;
    margin-bottom: 0.4rem;
    font-size: 2.1rem;
    background: linear-gradient(120deg, #F0F2EE 0%, #7EBC5A 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
h3 { font-size: 1.05rem; margin-top: 0.4rem; color: #F0F2EE; }

.stTabs [data-baseweb="tab-list"] {
    gap: 28px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.stTabs [data-baseweb="tab"] {
    padding: 12px 4px;
    color: #8B928D;
    font-weight: 500;
    transition: color 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: #F0F2EE; }
.stTabs [aria-selected="true"] { color: #7EBC5A !important; font-weight: 600; }
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #7EBC5A !important;
    height: 2px;
    box-shadow: 0 0 8px rgba(126, 188, 90, 0.6);
}

hr { border-color: rgba(255, 255, 255, 0.06); }

div[data-testid="stAlert"] {
    background: rgba(255, 255, 255, 0.025);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    color: #F0F2EE;
}

.stSlider > div > div > div > div { background: #7EBC5A !important; }
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: #7EBC5A !important;
    border-color: #7EBC5A !important;
    box-shadow: 0 0 0 4px rgba(126, 188, 90, 0.25) !important;
}

[data-testid="stCaptionContainer"], .stCaption { color: #8B928D; }

.stDataFrame { border-radius: 12px; overflow: hidden; }

.weather-card {
    background: rgba(255, 255, 255, 0.025);
    backdrop-filter: blur(20px) saturate(160%);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
    transition: transform 0.25s cubic-bezier(.4,0,.2,1), border-color 0.25s, box-shadow 0.25s;
}
.weather-card:hover {
    transform: translateY(-2px);
    border-color: rgba(126, 188, 90, 0.25);
    box-shadow: 0 12px 32px rgba(126, 188, 90, 0.12);
}
.weather-card .hora {
    color: #8B928D;
    font-size: 0.76rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.weather-card .temp {
    color: #F0F2EE;
    font-size: 1.9rem;
    font-weight: 600;
    line-height: 1.1;
    margin-bottom: 4px;
    background: linear-gradient(120deg, #F0F2EE 0%, #FF9844 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.weather-card .desc {
    color: #8B928D;
    font-size: 0.78rem;
    margin-bottom: 12px;
    min-height: 2.4em;
}
.weather-card .pop { color: #3BC5DD; font-size: 0.85rem; font-weight: 500; }
.weather-card.chovendo {
    border-color: rgba(59, 197, 221, 0.4);
    box-shadow: 0 0 24px rgba(59, 197, 221, 0.15), 0 2px 12px rgba(0, 0, 0, 0.25);
}
.weather-card.chovendo .pop { color: #FF6B6B; font-weight: 600; }

.decisao-card {
    background: rgba(255, 255, 255, 0.025);
    backdrop-filter: blur(20px) saturate(160%);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-left-width: 3px;
    border-radius: 14px;
    padding: 24px 26px;
    margin-top: 8px;
    transition: box-shadow 0.25s ease;
}
.decisao-card.positivo {
    border-left-color: #7EBC5A;
    box-shadow: 0 0 32px rgba(126, 188, 90, 0.18), 0 2px 12px rgba(0, 0, 0, 0.25);
}
.decisao-card.atencao  {
    border-left-color: #FF9844;
    box-shadow: 0 0 32px rgba(255, 152, 68, 0.16), 0 2px 12px rgba(0, 0, 0, 0.25);
}
.decisao-card.negativo {
    border-left-color: #FF6B6B;
    box-shadow: 0 0 32px rgba(255, 107, 107, 0.16), 0 2px 12px rgba(0, 0, 0, 0.25);
}
.decisao-card .rotulo {
    font-size: 1.55rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    margin-bottom: 6px;
}
.decisao-card.positivo .rotulo { color: #7EBC5A; }
.decisao-card.atencao .rotulo  { color: #FF9844; }
.decisao-card.negativo .rotulo { color: #FF6B6B; }
.decisao-card .mensagem { color: #8B928D; font-size: 0.92rem; line-height: 1.5; }

@media (max-width: 1024px) {
    .main .block-container {
        padding-left: 1.2rem;
        padding-right: 1.2rem;
        padding-top: 1.8rem;
    }
    h1 { font-size: 1.7rem; }
    [data-testid="stMetricValue"] { font-size: 1.7rem !important; }
}

@media (max-width: 768px) {
    .main .block-container {
        padding-left: 0.8rem;
        padding-right: 0.8rem;
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }
    h1 { font-size: 1.5rem; }
    h3 { font-size: 1rem; }
    [data-testid="stMetric"] { padding: 16px 18px; }
    [data-testid="stMetricValue"] { font-size: 1.55rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.74rem; }
    div[data-testid="stPlotlyChart"] { padding: 10px; border-radius: 12px; }
    .stTabs [data-baseweb="tab-list"] { gap: 16px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 2px; font-size: 0.9rem; }
    [data-testid="stHorizontalBlock"],
    div[data-testid="stHorizontalBlock"],
    [data-testid="stColumns"] {
        flex-direction: column !important;
        gap: 0.75rem !important;
        flex-wrap: wrap !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="column"],
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
    [data-testid="stColumns"] > div,
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
    }
    .weather-card { padding: 14px 12px; }
    .weather-card .temp { font-size: 1.55rem; }
}

@media (max-width: 480px) {
    .main .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
    h1 { font-size: 1.35rem; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
}
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)


df = carregar_leituras()


with st.sidebar:
    st.markdown("### FarmTech Solutions")
    st.markdown("**Painel da Araucaria**")
    st.caption("Fase 3 — Banco de Dados + Dashboard")
    st.markdown("---")
    st.caption("Microclima monitorado")
    st.markdown("**Curitiba/PR** — outono")
    st.markdown("---")
    st.caption("Janela temporal")

    _min = df["timestamp"].min().to_pydatetime()
    _max = df["timestamp"].max().to_pydatetime()
    janela = st.slider(
        "Periodo",
        min_value=_min, max_value=_max,
        value=(_min, _max),
        format="DD/MM HH:mm",
        label_visibility="collapsed",
    )

    df_view = (
        df[(df["timestamp"] >= janela[0]) & (df["timestamp"] <= janela[1])]
        .reset_index(drop=True)
    )

    st.markdown("---")
    st.caption("Resumo da janela")
    if len(df_view):
        horas = (
            df_view["timestamp"].max() - df_view["timestamp"].min()
        ).total_seconds() / 3600
        st.write(f"**{len(df_view)}** leituras")
        st.write(f"**{horas:.1f}h** de cobertura")
    else:
        st.warning("Nenhuma leitura na janela.")


st.title("Painel da Araucaria")
st.markdown(
    "Sistema de irrigacao inteligente para mudas de *Araucaria angustifolia*. "
    "Dados dos sensores do ESP32 monitorados na Fase 2."
)
st.markdown("")

tab_visao, tab_sensores, tab_diag, tab_realtime = st.tabs(
    ["Visao Geral", "Sensores", "Diagnostico", "Tempo Real"]
)


with tab_visao:
    if not len(df_view):
        st.info("Ajuste a janela temporal na barra lateral.")
    else:
        umid = df_view["umidade"].mean()
        temp = df_view["temperatura"].mean()
        pct_irr = 100 * df_view["irrigou"].sum() / len(df_view)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Leituras", f"{len(df_view)}")
        c2.metric("Umidade media (%)", f"{umid:.1f}")
        c3.metric("Temperatura (°C)", f"{temp:.1f}")
        c4.metric("Irrigacoes ativas (%)", f"{pct_irr:.0f}")

        st.markdown("")
        st.markdown("---")
        st.subheader("Serie temporal — visao rapida")
        st.caption(
            "Faixa coral abaixo de 60% indica solo seco; faixa azul acima "
            "de 75% indica solo encharcado."
        )
        st.plotly_chart(
            serie_umidade_temperatura(df_view),
            use_container_width=True,
            key="visao_serie",
        )


with tab_sensores:
    if not len(df_view):
        st.info("Ajuste a janela temporal na barra lateral.")
    else:
        st.subheader("Umidade e temperatura do solo")
        st.caption(
            "Bandas destacam os limiares do firmware: <60% solo seco; "
            ">75% solo encharcado."
        )
        st.plotly_chart(
            serie_umidade_temperatura(df_view),
            use_container_width=True,
            key="sensores_serie",
        )

        st.markdown("")
        st.subheader("Acionamento da bomba")
        st.caption(
            "Cada barra representa uma leitura: verde quando a bomba estava "
            "ligada, coral quando estava desligada."
        )
        st.plotly_chart(
            timeline_bomba(df_view),
            use_container_width=True,
            key="sensores_timeline",
        )

        st.markdown("")
        col_ph, col_npk = st.columns(2)
        with col_ph:
            st.subheader("pH do solo")
            st.caption("Faixa verde marca o intervalo ideal para a araucaria (5 a 7).")
            st.plotly_chart(
                serie_ph(df_view), use_container_width=True, key="sensores_ph"
            )
        with col_npk:
            st.subheader("Nutrientes ao longo do tempo")
            st.caption(
                "Quadrados verdes indicam presenca do nutriente; "
                "celulas escuras indicam ausencia."
            )
            st.plotly_chart(
                heatmap_npk(df_view), use_container_width=True, key="sensores_npk"
            )


with tab_diag:
    if not len(df_view):
        st.info("Ajuste a janela temporal na barra lateral.")
    else:
        df_clas = df_view.copy()
        df_clas["condicao"] = df_clas.apply(classificar_condicao, axis=1)
        contagens = df_clas["condicao"].value_counts()

        classes_alerta = ["pH fora da faixa", "Solo encharcado", "Fosforo ausente"]
        classes_saudaveis = ["Solo seco - irrigar", "Umidade adequada"]
        n_total = len(df_clas)
        n_alerta = int(sum(contagens.get(c, 0) for c in classes_alerta))
        n_saudavel = int(sum(contagens.get(c, 0) for c in classes_saudaveis))
        n_irrigou = int(df_clas["irrigou"].sum())
        pct_saudavel = 100 * n_saudavel / n_total if n_total else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Leituras totais", f"{n_total}")
        c2.metric("Solo saudavel (%)", f"{pct_saudavel:.0f}")
        c3.metric("Com alerta", f"{n_alerta}")
        c4.metric("Bomba acionada", f"{n_irrigou}")

        st.markdown("")
        st.markdown("---")

        col_donut, col_timeline = st.columns([1, 1.3])
        with col_donut:
            st.subheader("Distribuicao por condicao")
            st.caption(
                "Mesma logica do CASE WHEN da Consulta 8 (consultas.sql): "
                "pH > encharcamento > fosforo > umidade seca > umidade adequada."
            )
            st.plotly_chart(
                donut_distribuicao(contagens),
                use_container_width=True,
                key="diag_donut",
            )
        with col_timeline:
            st.subheader("Quando os alertas aconteceram")
            st.caption(
                "Cada marcador eh uma leitura com alerta. Permite ver se os "
                "problemas se concentraram ou se distribuiram no periodo."
            )
            st.plotly_chart(
                timeline_alertas(df_clas),
                use_container_width=True,
                key="diag_timeline",
            )

        st.markdown("---")
        st.subheader("Leituras com alerta")
        st.caption(
            "Apenas as leituras em que um criterio agronomico foi violado. "
            "Cor da celula 'condicao' destaca o tipo de alerta."
        )

        df_alerta = df_clas[df_clas["condicao"].isin(classes_alerta)].copy()
        if len(df_alerta) == 0:
            st.success("Nenhum alerta agronomico nesta janela. Solo dentro dos limites.")
        else:
            df_alerta["timestamp"] = df_alerta["timestamp"].dt.strftime("%d/%m/%Y %H:%M")
            df_alerta = df_alerta[
                ["timestamp", "condicao", "ph", "umidade", "n", "p", "k", "irrigou"]
            ]
            cores_fundo = {
                "pH fora da faixa":  "rgba(255, 107, 107, 0.18)",
                "Solo encharcado":   "rgba(59, 197, 221, 0.18)",
                "Fosforo ausente":   "rgba(214, 102, 173, 0.20)",
            }

            def _pintar_condicao(val):
                cor = cores_fundo.get(val, "")
                return f"background-color: {cor}; font-weight: 500;" if cor else ""

            styled = df_alerta.style.map(_pintar_condicao, subset=["condicao"]).format(
                {"umidade": "{:.1f}"}
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)


with tab_realtime:
    if not API_KEY:
        st.warning(
            "**Previsao em tempo real indisponivel.** "
            "Crie um arquivo `.env` em `iralem1_dashboard/` com a sua "
            "`OPENWEATHER_API_KEY` (veja `.env.example`)."
        )

    previsao = buscar_previsao(horas=12)

    st.subheader("Previsao do tempo — Curitiba/PR")
    if previsao is None or not previsao["slots"]:
        st.info(
            "Sem dados de previsao no momento. Verifique se a chave da API "
            "esta ativa e tem cota disponivel."
        )
    else:
        st.caption(
            "Cidade de referencia do viveiro. Slots de 3 em 3 horas, "
            "ate as proximas 12 horas. Atualizado a cada 10 minutos."
        )
        cols = st.columns(len(previsao["slots"]))
        for col, slot in zip(cols, previsao["slots"]):
            with col:
                horario = datetime.fromtimestamp(slot["dt"])
                hora_txt = horario.strftime("%a %Hh").capitalize()
                pop = slot["pop"]
                cls_chovendo = " chovendo" if pop >= 50 else ""
                st.markdown(
                    f"""
                    <div class="weather-card{cls_chovendo}">
                      <div class="hora">{hora_txt}</div>
                      <div class="temp">{slot["temperatura"]:.0f}°C</div>
                      <div class="desc">{slot["descricao"]}</div>
                      <div class="pop">Chuva: {pop:.0f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.subheader("Simulador — Irrigar agora?")
    st.caption(
        "Ajuste as condicoes atuais do solo. A recomendacao combina a regra "
        "do firmware (sketch.ino) com a previsao do tempo acima."
    )

    col_inputs, col_resultado = st.columns([1, 1])

    with col_inputs:
        ph_s = st.slider("pH do solo", 0, 14, 6, key="sim_ph")
        umid_s = st.slider("Umidade do solo (%)", 0.0, 100.0, 50.0, 1.0, key="sim_umid")
        st.caption("Nutrientes presentes")
        sc1, sc2, sc3 = st.columns(3)
        n_s = sc1.toggle("Nitrogenio", value=True, key="sim_n")
        p_s = sc2.toggle("Fosforo",    value=True, key="sim_p")
        k_s = sc3.toggle("Potassio",   value=True, key="sim_k")

    with col_resultado:
        firmware_ok, motivo = decisao_firmware(
            int(n_s), int(p_s), int(k_s), ph_s, umid_s
        )
        vai_chover = chuva_prevista(previsao)
        rotulo, mensagem, tipo = decisao_final(firmware_ok, motivo, vai_chover)

        st.markdown(
            f"""
            <div class="decisao-card {tipo}">
              <div class="rotulo">{rotulo}</div>
              <div class="mensagem">{mensagem}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        firmware_txt = "acionar" if firmware_ok else "nao acionar"
        chuva_txt = "chuva" if vai_chover else "sem chuva"
        st.caption(
            f"Regra do firmware: **{firmware_txt}** ({motivo}). "
            f"Previsao: **{chuva_txt}** nas proximas 12h."
        )
