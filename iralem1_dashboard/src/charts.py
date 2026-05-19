import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
COR_BG_TRANSPARENTE   = "rgba(0,0,0,0)"
COR_GRID              = "rgba(255,255,255,0.05)"
COR_GRID_FORTE        = "rgba(255,255,255,0.10)"
COR_TEXTO             = "#F0F2EE"
COR_TEXTO_SUAVE       = "#8B928D"
COR_TOOLTIP_BG        = "rgba(20,26,32,0.92)"
COR_TOOLTIP_FG        = "#F0F2EE"

COR_UMIDADE           = "#3BC5DD"
COR_UMIDADE_FILL_TOP  = "rgba(59,197,221,0.55)"

COR_TEMPERATURA       = "#FF9844"
COR_TEMP_FILL_TOP     = "rgba(255,152,68,0.55)"

COR_PH                = "#B093FF"
COR_PH_FILL_TOP       = "rgba(176,147,255,0.50)"

COR_ARAUCARIA         = "#7EBC5A"
COR_ARAUCARIA_BG      = "rgba(126,188,90,0.18)"

COR_NAO_IRRIGAR       = "#FF6B6B"
COR_FOSFORO           = "#D666AD"


# ---------------------------------------------------------------------------
# Helpers de tema / interacao
# ---------------------------------------------------------------------------
def _aplicar_tema(fig: go.Figure, altura: int = 360, hover_unificado: bool = False) -> go.Figure:
    fig.update_layout(
        height=altura,
        plot_bgcolor=COR_BG_TRANSPARENTE,
        paper_bgcolor=COR_BG_TRANSPARENTE,
        font=dict(family="Inter, sans-serif", color=COR_TEXTO, size=12),
        margin=dict(l=12, r=16, t=44, b=52),
        hoverlabel=dict(
            bgcolor=COR_TOOLTIP_BG,
            font=dict(color=COR_TOOLTIP_FG, family="Inter, sans-serif", size=12),
            bordercolor="rgba(255,255,255,0.10)",
        ),
        hovermode="x unified" if hover_unificado else "closest",
        showlegend=False,
        # uirevision: preserva estado de zoom/pan entre re-renders do Streamlit
        uirevision="farmtech",
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=COR_GRID, gridwidth=1,
        zeroline=False, showline=False, ticks="",
        tickfont=dict(color=COR_TEXTO_SUAVE, size=11),
        automargin=True,
        showspikes=hover_unificado,
        spikemode="toaxis",
        spikethickness=1,
        spikecolor="rgba(255,255,255,0.18)",
        spikedash="dot",
        spikesnap="cursor",
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=COR_GRID, gridwidth=1,
        zeroline=False, showline=False, ticks="",
        tickfont=dict(color=COR_TEXTO_SUAVE, size=11),
        automargin=True,
    )
    return fig


def _range_selector() -> dict:
    """Botoes 24h / 7d / Tudo no canto superior."""
    return dict(
        rangeselector=dict(
            buttons=[
                dict(count=24, label="24h", step="hour", stepmode="backward"),
                dict(count=7,  label="7d",  step="day",  stepmode="backward"),
                dict(step="all", label="Tudo"),
            ],
            bgcolor="rgba(255,255,255,0.04)",
            activecolor="rgba(126,188,90,0.35)",
            bordercolor="rgba(255,255,255,0.08)",
            borderwidth=1,
            font=dict(color=COR_TEXTO_SUAVE, size=11, family="Inter, sans-serif"),
            x=0, y=1.18, yanchor="top",
        ),
    )


def _config_grafico(modebar: bool = False) -> dict:
    """Config para st.plotly_chart.

    scrollZoom DESLIGADO de proposito: scroll dispara muito re-render
    e trava o navegador. Zoom acontece pelos botoes 24h/7d/Tudo.
    """
    return {
        "displayModeBar": modebar,
        "displaylogo": False,
        "scrollZoom": False,
        "doubleClick": "reset",
        "modeBarButtonsToRemove": [
            "select2d", "lasso2d", "autoScale2d", "toggleSpikelines",
        ],
    }


CONFIG_GRAFICO = _config_grafico(modebar=False)


def _adicionar_curva_glow(
    fig: go.Figure, x, y, cor: str, cor_fill_topo: str,
    hover: str, nome: str = "",
    row: int = None, col: int = None,
) -> None:
    """Linha com brilho externo + area com gradient vertical (otimizado)."""
    kwargs = {"row": row, "col": col} if row else {}
    # glow externo — width baixa pra nao travar no zoom
    fig.add_trace(
        go.Scatter(
            x=x, y=y, mode="lines",
            line=dict(color=cor, width=6, shape="spline", smoothing=0.6),
            opacity=0.20,
            hoverinfo="skip",
            showlegend=False,
            name=f"{nome}_glow",
        ),
        **kwargs,
    )
    fig.add_trace(
        go.Scatter(
            x=x, y=y, mode="lines",
            line=dict(color=cor, width=2.4, shape="spline", smoothing=0.6),
            fill="tozeroy",
            fillgradient=dict(
                type="vertical",
                colorscale=[[0.0, "rgba(0,0,0,0)"], [1.0, cor_fill_topo]],
            ),
            hovertemplate=hover,
            name=nome,
            showlegend=False,
        ),
        **kwargs,
    )


def _marcador_valor_atual(
    fig: go.Figure, x, y, cor: str, sufixo: str = "",
    row: int = None, col: int = None,
) -> None:
    """Bolinha brilhante no ultimo ponto da serie."""
    if len(x) == 0:
        return
    kwargs = {"row": row, "col": col} if row else {}
    x_last = x.iloc[-1] if hasattr(x, "iloc") else x[-1]
    y_last = y.iloc[-1] if hasattr(y, "iloc") else y[-1]
    # halo
    fig.add_trace(
        go.Scatter(
            x=[x_last], y=[y_last], mode="markers",
            marker=dict(size=22, color=cor, opacity=0.20),
            hoverinfo="skip", showlegend=False,
        ),
        **kwargs,
    )
    # bolinha
    fig.add_trace(
        go.Scatter(
            x=[x_last], y=[y_last], mode="markers",
            marker=dict(
                size=10, color=cor,
                line=dict(color="#0A0F0D", width=2),
            ),
            hovertemplate=f"<b>Agora</b><br>%{{y:.1f}}{sufixo}<extra></extra>",
            showlegend=False,
        ),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Series temporais principais
# ---------------------------------------------------------------------------
def serie_umidade_temperatura(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.16,
        subplot_titles=("Umidade do solo (%)", "Temperatura do ar (°C)"),
        row_heights=[0.5, 0.5],
    )
    _adicionar_curva_glow(
        fig, df["timestamp"], df["umidade"], COR_UMIDADE, COR_UMIDADE_FILL_TOP,
        "<b>%{y:.1f}%</b> de umidade<extra></extra>",
        nome="Umidade", row=1, col=1,
    )
    fig.add_hrect(y0=75, y1=100, fillcolor=COR_UMIDADE, opacity=0.07, line_width=0, row=1, col=1)
    fig.add_hrect(y0=0,  y1=60,  fillcolor=COR_NAO_IRRIGAR, opacity=0.06, line_width=0, row=1, col=1)
    _marcador_valor_atual(fig, df["timestamp"], df["umidade"], COR_UMIDADE, sufixo="%", row=1, col=1)

    _adicionar_curva_glow(
        fig, df["timestamp"], df["temperatura"], COR_TEMPERATURA, COR_TEMP_FILL_TOP,
        "<b>%{y:.1f} °C</b><extra></extra>",
        nome="Temperatura", row=2, col=1,
    )
    _marcador_valor_atual(fig, df["timestamp"], df["temperatura"], COR_TEMPERATURA, sufixo=" °C", row=2, col=1)

    for ann in fig.layout.annotations:
        ann.font = dict(family="Inter, sans-serif", color=COR_TEXTO, size=12.5)
        ann.x = 0
        ann.xanchor = "left"

    fig.update_xaxes(tickformat="%d/%m %Hh", row=2, col=1)
    fig.update_xaxes(**_range_selector(), row=2, col=1)

    fig = _aplicar_tema(fig, altura=480, hover_unificado=True)
    fig.update_layout(margin=dict(l=12, r=16, t=70, b=52))
    return fig


def serie_ph(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_hrect(y0=5, y1=7, fillcolor=COR_ARAUCARIA, opacity=0.14, line_width=0)
    _adicionar_curva_glow(
        fig, df["timestamp"], df["ph"], COR_PH, COR_PH_FILL_TOP,
        "<b>pH %{y:.1f}</b><extra></extra>",
        nome="pH",
    )
    _marcador_valor_atual(fig, df["timestamp"], df["ph"], COR_PH)

    fig.update_yaxes(range=[0, 14], dtick=2)
    fig.update_xaxes(tickformat="%d/%m %Hh", **_range_selector())
    fig = _aplicar_tema(fig, altura=380, hover_unificado=True)
    fig.update_layout(margin=dict(l=12, r=16, t=64, b=52))
    return fig


# ---------------------------------------------------------------------------
# Timeline da bomba (faixa Gantt elegante)
# ---------------------------------------------------------------------------
def timeline_bomba(df: pd.DataFrame) -> go.Figure:
    if not len(df):
        return _aplicar_tema(go.Figure(), altura=140)

    if len(df) > 1:
        largura_ms = (df["timestamp"].diff().dropna().dt.total_seconds() * 1000).median()
    else:
        largura_ms = 30 * 60 * 1000

    cores = [COR_ARAUCARIA if v == 1 else "rgba(255,255,255,0.06)" for v in df["irrigou"]]
    rotulos = ["Bomba ligada" if v == 1 else "Bomba desligada" for v in df["irrigou"]]

    fig = go.Figure(
        go.Bar(
            x=df["timestamp"], y=[1] * len(df),
            width=[largura_ms * 0.95] * len(df),
            marker=dict(color=cores, line=dict(width=0)),
            customdata=rotulos,
            hovertemplate="%{x|%d/%m %H:%M}<br><b>%{customdata}</b><extra></extra>",
        )
    )

    n_lig = int(df["irrigou"].sum())
    n_tot = len(df)
    pct = 100 * n_lig / n_tot if n_tot else 0
    fig.add_annotation(
        xref="paper", yref="paper", x=1, y=1.18,
        xanchor="right", yanchor="bottom",
        text=f"<span style='color:{COR_ARAUCARIA};font-weight:600'>{n_lig}</span>"
             f"<span style='color:{COR_TEXTO_SUAVE}'> / {n_tot} ciclos ({pct:.0f}%)</span>",
        showarrow=False,
        font=dict(family="Inter, sans-serif", size=12),
    )

    fig.update_yaxes(visible=False, range=[0, 1.05])
    fig.update_xaxes(tickformat="%d/%m %Hh", showgrid=False)
    fig = _aplicar_tema(fig, altura=150)
    fig.update_layout(bargap=0.0, margin=dict(l=12, r=16, t=42, b=40))
    return fig


# ---------------------------------------------------------------------------
# Heatmap NPK
# ---------------------------------------------------------------------------
def heatmap_npk(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            x=df["timestamp"],
            y=["Potassio", "Fosforo", "Nitrogenio"],
            z=[df["k"].tolist(), df["p"].tolist(), df["n"].tolist()],
            colorscale=[
                [0.0, "rgba(255,255,255,0.03)"],
                [0.5, "rgba(126,188,90,0.30)"],
                [1.0, COR_ARAUCARIA],
            ],
            showscale=False, xgap=1, ygap=6,
            hovertemplate="%{x|%d/%m %H:%M}<br><b>%{y}</b>: %{z}<extra></extra>",
        )
    )
    fig.update_xaxes(tickformat="%d/%m %Hh", showgrid=False)
    fig.update_yaxes(
        tickfont=dict(size=12, color=COR_TEXTO),
        autorange="reversed", showgrid=False,
    )
    fig = _aplicar_tema(fig, altura=280)
    fig.update_layout(margin=dict(l=12, r=16, t=20, b=40))
    return fig


# ---------------------------------------------------------------------------
# Donut moderno
# ---------------------------------------------------------------------------
CORES_CONDICAO = {
    "pH fora da faixa":     COR_NAO_IRRIGAR,
    "Solo encharcado":      COR_UMIDADE,
    "Fosforo ausente":      COR_FOSFORO,
    "Solo seco - irrigar":  COR_ARAUCARIA,
    "Umidade adequada":     "#5C625D",
}

CLASSES_ALERTA = ["pH fora da faixa", "Solo encharcado", "Fosforo ausente"]
CLASSES_SAUDAVEIS = ["Solo seco - irrigar", "Umidade adequada"]


def donut_distribuicao(contagens) -> go.Figure:
    labels = contagens.index.tolist()
    values = contagens.values.tolist()
    cores = [CORES_CONDICAO.get(str(l), COR_TEXTO_SUAVE) for l in labels]

    fig = go.Figure(
        go.Pie(
            labels=labels, values=values,
            hole=0.78,
            marker=dict(colors=cores, line=dict(color="#0A0F0D", width=3)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} leituras (%{percent})<extra></extra>",
            sort=False, direction="clockwise", rotation=-90,
        )
    )

    total = sum(values)
    saudavel = sum(v for l, v in zip(labels, values) if l in CLASSES_SAUDAVEIS)
    pct = 100 * saudavel / total if total else 0

    fig.add_annotation(
        text=f"<span style='font-size:46px;color:#F0F2EE;font-weight:600'>{pct:.0f}<span style='font-size:22px;color:#8B928D'>%</span></span>",
        x=0.5, y=0.56, showarrow=False,
        font=dict(family="Inter, sans-serif"),
    )
    fig.add_annotation(
        text="<span style='font-size:10px;color:#8B928D;letter-spacing:0.14em'>SOLO&nbsp;SAUDAVEL</span>",
        x=0.5, y=0.40, showarrow=False,
        font=dict(family="Inter, sans-serif"),
    )

    fig.update_layout(
        legend=dict(
            orientation="v", yanchor="middle", y=0.5,
            xanchor="left", x=1.05,
            font=dict(color=COR_TEXTO, size=11, family="Inter, sans-serif"),
            bgcolor="rgba(0,0,0,0)",
            itemclick=False,
        ),
        showlegend=True,
    )
    fig = _aplicar_tema(fig, altura=380)
    fig.update_layout(margin=dict(l=12, r=12, t=20, b=20))
    return fig


# ---------------------------------------------------------------------------
# Radar polar do estado atual
# ---------------------------------------------------------------------------
def radar_estado_atual(df: pd.DataFrame) -> go.Figure:
    if not len(df):
        return _aplicar_tema(go.Figure(), altura=340)

    ult = df.iloc[-1]
    categorias = ["Umidade", "pH ok", "Nitrogenio", "Fosforo", "Potassio", "Temperatura"]
    valores = [
        float(ult["umidade"]),
        100.0 if 5 <= ult["ph"] <= 7 else max(0.0, 100 - abs(ult["ph"] - 6) * 20),
        100.0 if ult["n"] else 0.0,
        100.0 if ult["p"] else 0.0,
        100.0 if ult["k"] else 0.0,
        max(0.0, 100.0 - abs(float(ult["temperatura"]) - 20) * 5),
    ]
    ideal = [75, 100, 100, 100, 100, 100]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=ideal + [ideal[0]],
            theta=categorias + [categorias[0]],
            mode="lines",
            line=dict(color="rgba(255,255,255,0.18)", width=1, dash="dot"),
            hoverinfo="skip", name="Ideal",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=valores + [valores[0]],
            theta=categorias + [categorias[0]],
            mode="lines+markers",
            line=dict(color=COR_ARAUCARIA, width=2.5),
            marker=dict(size=8, color=COR_ARAUCARIA, line=dict(color="#0A0F0D", width=1.5)),
            fill="toself",
            fillcolor="rgba(126,188,90,0.18)",
            hovertemplate="<b>%{theta}</b>: %{r:.0f}<extra></extra>",
            name="Agora",
        )
    )
    fig.update_layout(
        polar=dict(
            bgcolor=COR_BG_TRANSPARENTE,
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor=COR_GRID, linecolor="rgba(0,0,0,0)",
                tickfont=dict(color=COR_TEXTO_SUAVE, size=9),
                tickvals=[25, 50, 75, 100],
            ),
            angularaxis=dict(
                gridcolor=COR_GRID,
                linecolor=COR_GRID_FORTE,
                tickfont=dict(color=COR_TEXTO, size=11, family="Inter, sans-serif"),
            ),
        ),
        showlegend=False,
        plot_bgcolor=COR_BG_TRANSPARENTE,
        paper_bgcolor=COR_BG_TRANSPARENTE,
        font=dict(family="Inter, sans-serif", color=COR_TEXTO, size=12),
        height=380,
        margin=dict(l=40, r=40, t=30, b=30),
        hoverlabel=dict(
            bgcolor=COR_TOOLTIP_BG,
            font=dict(color=COR_TOOLTIP_FG, family="Inter, sans-serif"),
            bordercolor="rgba(255,255,255,0.10)",
        ),
        uirevision="farmtech",
    )
    return fig


# ---------------------------------------------------------------------------
# Timeline de alertas (lollipop com halo)
# ---------------------------------------------------------------------------
def timeline_alertas(df_classificado) -> go.Figure:
    fig = go.Figure()
    presentes = False

    for classe in CLASSES_ALERTA:
        subset = df_classificado[df_classificado["condicao"] == classe]
        if len(subset) == 0:
            continue
        presentes = True
        cor = CORES_CONDICAO[classe]

        # halo
        fig.add_trace(
            go.Scatter(
                x=subset["timestamp"],
                y=[classe] * len(subset),
                mode="markers",
                marker=dict(size=26, color=cor, opacity=0.18),
                hoverinfo="skip", showlegend=False,
            )
        )
        # marcador principal
        fig.add_trace(
            go.Scatter(
                x=subset["timestamp"],
                y=[classe] * len(subset),
                mode="markers",
                marker=dict(
                    size=13, color=cor,
                    line=dict(color="#0A0F0D", width=1.8),
                ),
                hovertemplate=f"<b>{classe}</b><br>%{{x|%d/%m %H:%M}}<extra></extra>",
                showlegend=False,
            )
        )

    if not presentes:
        fig.add_annotation(
            text="Nenhum alerta no periodo selecionado ✓",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(family="Inter, sans-serif", color=COR_ARAUCARIA, size=14),
        )

    fig.update_xaxes(tickformat="%d/%m %Hh")
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=list(reversed(CLASSES_ALERTA)),
        tickfont=dict(size=11, color=COR_TEXTO),
    )
    fig = _aplicar_tema(fig, altura=280)
    return fig
