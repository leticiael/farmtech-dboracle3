import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


COR_BG_TRANSPARENTE   = "rgba(0,0,0,0)"
COR_GRID              = "rgba(255,255,255,0.06)"
COR_TEXTO             = "#F0F2EE"
COR_TEXTO_SUAVE       = "#8B928D"
COR_TOOLTIP_BG        = "#1A2120"
COR_TOOLTIP_FG        = "#F0F2EE"

COR_UMIDADE           = "#3BC5DD"
COR_UMIDADE_FILL_TOP  = "rgba(59,197,221,0.45)"

COR_TEMPERATURA       = "#FF9844"
COR_TEMP_FILL_TOP     = "rgba(255,152,68,0.45)"

COR_PH                = "#B093FF"
COR_PH_FILL_TOP       = "rgba(176,147,255,0.40)"

COR_ARAUCARIA         = "#7EBC5A"
COR_ARAUCARIA_BG      = "rgba(126,188,90,0.18)"

COR_NAO_IRRIGAR       = "#FF6B6B"
COR_FOSFORO           = "#D666AD"


def _aplicar_tema(fig: go.Figure, altura: int = 360) -> go.Figure:
    fig.update_layout(
        height=altura,
        plot_bgcolor=COR_BG_TRANSPARENTE,
        paper_bgcolor=COR_BG_TRANSPARENTE,
        font=dict(family="Inter, sans-serif", color=COR_TEXTO, size=12),
        margin=dict(l=12, r=12, t=36, b=52),
        hoverlabel=dict(
            bgcolor=COR_TOOLTIP_BG,
            font=dict(color=COR_TOOLTIP_FG, family="Inter, sans-serif"),
            bordercolor="rgba(255,255,255,0.1)",
        ),
        showlegend=False,
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=COR_GRID, gridwidth=1,
        zeroline=False, showline=False, ticks="",
        tickfont=dict(color=COR_TEXTO_SUAVE, size=11),
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=COR_GRID, gridwidth=1,
        zeroline=False, showline=False, ticks="",
        tickfont=dict(color=COR_TEXTO_SUAVE, size=11),
        automargin=True,
    )
    return fig


def _adicionar_curva_glow(
    fig: go.Figure, x, y, cor: str, cor_fill_topo: str,
    hover: str, row: int = None, col: int = None,
) -> None:
    kwargs = {"row": row, "col": col} if row else {}
    fig.add_trace(
        go.Scatter(
            x=x, y=y, mode="lines",
            line=dict(color=cor, width=10, shape="spline", smoothing=1.2),
            opacity=0.18,
            hoverinfo="skip",
        ),
        **kwargs,
    )
    fig.add_trace(
        go.Scatter(
            x=x, y=y, mode="lines",
            line=dict(color=cor, width=2.5, shape="spline", smoothing=1.2),
            fill="tozeroy",
            fillgradient=dict(
                type="vertical",
                colorscale=[[0.0, "rgba(0,0,0,0)"], [1.0, cor_fill_topo]],
            ),
            hovertemplate=hover,
        ),
        **kwargs,
    )


def serie_umidade_temperatura(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.18,
        subplot_titles=("Umidade do solo (%)", "Temperatura do ar (°C)"),
        row_heights=[0.5, 0.5],
    )
    _adicionar_curva_glow(
        fig, df["timestamp"], df["umidade"], COR_UMIDADE, COR_UMIDADE_FILL_TOP,
        "%{x|%d/%m %H:%M}<br><b>%{y:.1f}%</b><extra></extra>",
        row=1, col=1,
    )
    fig.add_hrect(y0=75, y1=100, fillcolor=COR_UMIDADE, opacity=0.06, line_width=0, row=1, col=1)
    fig.add_hrect(y0=0, y1=60, fillcolor=COR_NAO_IRRIGAR, opacity=0.05, line_width=0, row=1, col=1)
    _adicionar_curva_glow(
        fig, df["timestamp"], df["temperatura"], COR_TEMPERATURA, COR_TEMP_FILL_TOP,
        "%{x|%d/%m %H:%M}<br><b>%{y:.1f} °C</b><extra></extra>",
        row=2, col=1,
    )
    for ann in fig.layout.annotations:
        ann.font = dict(family="Inter, sans-serif", color=COR_TEXTO, size=12)
    fig.update_xaxes(tickformat="%d/%m %Hh", row=2, col=1)
    return _aplicar_tema(fig, altura=460)


def timeline_bomba(df: pd.DataFrame) -> go.Figure:
    cores = [COR_ARAUCARIA if v == 1 else COR_NAO_IRRIGAR for v in df["irrigou"]]
    rotulos = ["Bomba ligada" if v == 1 else "Bomba desligada" for v in df["irrigou"]]
    fig = go.Figure(
        go.Bar(
            x=df["timestamp"], y=[1] * len(df),
            marker=dict(color=cores, line=dict(width=0)),
            customdata=rotulos,
            hovertemplate="%{x|%d/%m %H:%M}<br><b>%{customdata}</b><extra></extra>",
        )
    )
    fig.update_yaxes(visible=False, range=[0, 1.05])
    fig.update_xaxes(tickformat="%d/%m %Hh")
    return _aplicar_tema(fig, altura=200)


def serie_ph(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_hrect(
        y0=5, y1=7, fillcolor=COR_ARAUCARIA, opacity=0.12, line_width=0,
    )
    _adicionar_curva_glow(
        fig, df["timestamp"], df["ph"], COR_PH, COR_PH_FILL_TOP,
        "%{x|%d/%m %H:%M}<br><b>pH %{y}</b><extra></extra>",
    )
    fig.update_yaxes(range=[0, 14], dtick=2)
    fig.update_xaxes(tickformat="%d/%m %Hh")
    return _aplicar_tema(fig, altura=340)


def heatmap_npk(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            x=df["timestamp"],
            y=["Potassio", "Fosforo", "Nitrogenio"],
            z=[df["k"].tolist(), df["p"].tolist(), df["n"].tolist()],
            colorscale=[[0, "rgba(255,255,255,0.04)"], [1, COR_ARAUCARIA]],
            showscale=False, xgap=0, ygap=4,
            hovertemplate="%{x|%d/%m %H:%M}<br><b>%{y}</b>: %{z}<extra></extra>",
        )
    )
    fig.update_xaxes(tickformat="%d/%m %Hh")
    fig.update_yaxes(tickfont=dict(size=12, color=COR_TEXTO), autorange="reversed")
    return _aplicar_tema(fig, altura=260)


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
            labels=labels,
            values=values,
            hole=0.68,
            marker=dict(colors=cores, line=dict(color="#0A0F0D", width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} leituras (%{percent})<extra></extra>",
            sort=False,
            direction="clockwise",
        )
    )

    total = sum(values)
    saudavel = sum(v for l, v in zip(labels, values) if l in CLASSES_SAUDAVEIS)
    pct = 100 * saudavel / total if total else 0

    fig.add_annotation(
        text=f"<span style='font-size:36px;color:#F0F2EE;font-weight:600'>{pct:.0f}%</span>",
        x=0.5, y=0.55, showarrow=False,
        font=dict(family="Inter, sans-serif"),
    )
    fig.add_annotation(
        text="<span style='font-size:10px;color:#8B928D;letter-spacing:0.08em'>SOLO SAUDAVEL</span>",
        x=0.5, y=0.42, showarrow=False,
        font=dict(family="Inter, sans-serif"),
    )

    fig.update_layout(
        legend=dict(
            orientation="v", yanchor="middle", y=0.5,
            xanchor="left", x=1.02,
            font=dict(color=COR_TEXTO, size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
    )
    return _aplicar_tema(fig, altura=380)


def timeline_alertas(df_classificado) -> go.Figure:
    fig = go.Figure()
    presentes = False

    for classe in CLASSES_ALERTA:
        subset = df_classificado[df_classificado["condicao"] == classe]
        if len(subset) == 0:
            continue
        presentes = True
        cor = CORES_CONDICAO[classe]
        fig.add_trace(
            go.Scatter(
                x=subset["timestamp"],
                y=[classe] * len(subset),
                mode="markers",
                marker=dict(
                    size=14,
                    color=cor,
                    line=dict(color="#0A0F0D", width=1.5),
                    opacity=0.95,
                ),
                hovertemplate=f"<b>{classe}</b><br>%{{x|%d/%m %H:%M}}<extra></extra>",
            )
        )

    if not presentes:
        fig.add_annotation(
            text="Nenhum alerta no periodo selecionado",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(family="Inter, sans-serif", color=COR_TEXTO_SUAVE, size=14),
        )

    fig.update_xaxes(tickformat="%d/%m %Hh")
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=list(reversed(CLASSES_ALERTA)),
        tickfont=dict(size=11, color=COR_TEXTO),
    )
    return _aplicar_tema(fig, altura=260)
