"""Figuras estáticas dos relatórios (tarefa 5).

Decisões de visualização, todas registradas porque mudam a leitura:

- **Matplotlib/seaborn aqui, Altair no app.** Os relatórios precisam de PNG que
  apareça no README do GitHub sem servidor nenhum; o app precisa de gráfico
  interativo. Cada ferramenta no lugar em que ela resolve.
- **Paleta divergente só onde há polaridade.** Correlação vai de -1 a +1, então
  o mapa de calor usa dois tons opostos com cinza neutro no meio. Nada de arco-
  íris: cor de matiz variável sugere categoria onde existe grandeza contínua.
- **Uma série, nenhuma legenda.** Quando o gráfico mostra uma coisa só, o título
  já a nomeia; caixa de legenda seria ruído.
- **Eixos e grade recuados.** A grade é referência, não conteúdo: fica em tom
  fraco para que os dados sejam a coisa mais escura da figura.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sem janela: estes gráficos são gerados por script

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from src import config  # noqa: E402

# Paleta: superfície, tinta e as duas pontas do divergente.
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_FRACA = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"

AZUL = "#2a78d6"  # série única e polo positivo
VERMELHO = "#e34948"  # polo negativo
CINZA_NEUTRO = "#f0efec"  # meio do divergente

DIVERGENTE = LinearSegmentedColormap.from_list(
    "azul_cinza_vermelho", [VERMELHO, CINZA_NEUTRO, AZUL]
)

DPI = 150


def apply_style() -> None:
    """Estilo comum a todas as figuras."""
    plt.rcParams.update(
        {
            "figure.facecolor": SUPERFICIE,
            "axes.facecolor": SUPERFICIE,
            "savefig.facecolor": SUPERFICIE,
            "axes.edgecolor": EIXO,
            "axes.labelcolor": TINTA_SECUNDARIA,
            "axes.titlecolor": TINTA,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlepad": 12,
            "axes.labelsize": 10,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRADE,
            "grid.linewidth": 0.8,
            "xtick.color": TINTA_FRACA,
            "ytick.color": TINTA_FRACA,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "text.color": TINTA,
            "font.size": 10,
            "figure.dpi": DPI,
            "savefig.dpi": DPI,
            "savefig.bbox": "tight",
        }
    )


def _limpa_molduras(ax, manter=("left", "bottom")) -> None:
    for lado, spine in ax.spines.items():
        spine.set_visible(lado in manter)


def rotulo(coluna: str) -> str:
    """Nome legível de uma coluna, com reserva para o nome técnico."""
    return config.FEATURE_LABELS.get(coluna, coluna.replace("_", " "))


def _destino(path: Path | None, nome: str) -> Path:
    destino = Path(path) if path is not None else config.FIGURES_DIR / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    return destino


def plot_correlation_heatmap(
    matriz: pd.DataFrame, path: Path | None = None
) -> Path:
    """Mapa de calor da matriz de correlação.

    Só o triângulo inferior, e sem a diagonal: a matriz é simétrica, e a
    diagonal é sempre 1 — desenhá-la encheria o gráfico de células fortes que
    não dizem nada e puxariam o olho para longe do que importa.
    """
    apply_style()
    # Sem a diagonal, a primeira linha e a última coluna ficariam vazias: saem.
    matriz = matriz.iloc[1:, :-1]
    mascara = np.triu(np.ones_like(matriz, dtype=bool), k=1)
    rotulos_y = [rotulo(c) for c in matriz.index]
    rotulos_x = [rotulo(c) for c in matriz.columns]

    altura = 0.55 * len(matriz) + 3
    fig, ax = plt.subplots(figsize=(altura + 1.5, altura))
    sns.heatmap(
        matriz,
        mask=mascara,
        cmap=DIVERGENTE,
        vmin=-1,
        vmax=1,
        center=0,
        annot=True,
        fmt=".2f",
        annot_kws={"size": 8},
        linewidths=1,
        linecolor=SUPERFICIE,
        cbar_kws={"label": "correlação de Pearson", "shrink": 0.6},
        xticklabels=rotulos_x,
        yticklabels=rotulos_y,
        ax=ax,
    )
    ax.set_title("Como os hábitos se relacionam entre si e com a nota")
    ax.grid(False)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    plt.setp(ax.get_yticklabels(), rotation=0)

    destino = _destino(path, "01_mapa_de_calor.png")
    fig.savefig(destino)
    plt.close(fig)
    return destino


def plot_top_variable(
    df: pd.DataFrame,
    coluna: str,
    faixa: str,
    path: Path | None = None,
    target: str = config.TARGET,
) -> Path:
    """A variável de maior impacto, em dois ângulos.

    À esquerda, cada aluno e a reta de tendência: mostra a dispersão real, que
    uma média por faixa esconde. À direita, a mesma relação por faixa, que é
    como a conclusão vai ser contada.
    """
    apply_style()
    fig, (ax_dispersao, ax_faixa) = plt.subplots(1, 2, figsize=(12, 4.8))

    ax_dispersao.scatter(
        df[coluna], df[target], s=14, alpha=0.35, color=AZUL, linewidths=0
    )
    coef = np.polyfit(df[coluna], df[target], 1)
    grade_x = np.linspace(df[coluna].min(), df[coluna].max(), 100)
    ax_dispersao.plot(
        grade_x, np.polyval(coef, grade_x), color=TINTA, linewidth=2
    )
    correlacao = float(df[coluna].corr(df[target]))
    ax_dispersao.set_title(f"Cada ponto é um aluno (r = {correlacao:.3f})")
    ax_dispersao.set_xlabel(rotulo(coluna))
    ax_dispersao.set_ylabel("Nota na prova")
    ax_dispersao.set_ylim(*config.SCORE_LIMITS)
    _limpa_molduras(ax_dispersao)

    ordem = list(df[faixa].cat.categories)
    sns.boxplot(
        data=df,
        x=faixa,
        y=target,
        order=ordem,
        color=AZUL,
        width=0.55,
        fliersize=3,
        linewidth=1.2,
        ax=ax_faixa,
    )
    for patch in ax_faixa.patches:
        patch.set_alpha(0.75)
    # A média vai num rodapé fixo, não em cima da caixa: quando o grupo é
    # estreito e colado no teto, o rótulo em cima cobre a própria caixa.
    medias = df.groupby(faixa, observed=True)[target].mean().reindex(ordem)
    for posicao, valor in enumerate(medias):
        ax_faixa.annotate(
            f"média {valor:.1f}",
            (posicao, 3),
            ha="center",
            va="bottom",
            fontsize=9,
            color=TINTA_SECUNDARIA,
        )
    ax_faixa.set_title("Nota por faixa")
    ax_faixa.set_xlabel(rotulo(coluna) + " — faixa")
    ax_faixa.set_ylabel("")
    ax_faixa.set_ylim(*config.SCORE_LIMITS)
    _limpa_molduras(ax_faixa)

    fig.suptitle(
        f"{rotulo(coluna)}: a variável de maior associação com a nota",
        fontsize=14,
        fontweight="bold",
        color=TINTA,
        x=0.01,
        ha="left",
    )
    fig.tight_layout()

    destino = _destino(path, "02_variavel_de_maior_impacto.png")
    fig.savefig(destino)
    plt.close(fig)
    return destino


def plot_score_by_bin(
    df: pd.DataFrame,
    faixa: str,
    titulo: str,
    nome_arquivo: str,
    path: Path | None = None,
    target: str = config.TARGET,
) -> Path:
    """Boxplot da nota por faixa, com o tamanho de cada grupo no eixo.

    O n vai no rótulo porque caixa de 26 alunos e caixa de 382 não merecem a
    mesma confiança, e sem o número elas parecem iguais.
    """
    apply_style()
    ordem = list(df[faixa].cat.categories)
    contagens = df[faixa].value_counts().reindex(ordem, fill_value=0)

    fig, ax = plt.subplots(figsize=(8.5, 5))
    sns.boxplot(
        data=df,
        x=faixa,
        y=target,
        order=ordem,
        color=AZUL,
        width=0.55,
        fliersize=3,
        linewidth=1.2,
        ax=ax,
    )
    for patch in ax.patches:
        patch.set_alpha(0.75)

    ax.set_xticks(range(len(ordem)))
    ax.set_xticklabels([f"{f}\n(n = {contagens[f]})" for f in ordem])
    ax.set_title(titulo)
    ax.set_xlabel("")
    ax.set_ylabel("Nota na prova")
    ax.set_ylim(*config.SCORE_LIMITS)
    _limpa_molduras(ax)
    fig.tight_layout()

    destino = _destino(path, nome_arquivo)
    fig.savefig(destino)
    plt.close(fig)
    return destino


def plot_score_distribution(
    df: pd.DataFrame, path: Path | None = None, target: str = config.TARGET
) -> Path:
    """Histograma da nota, com o acúmulo no teto marcado.

    Existe para tornar visível o efeito teto encontrado na tarefa 1: ele é fácil
    de ignorar em uma tabela e salta aos olhos num histograma.
    """
    apply_style()
    _, maximo = config.SCORE_LIMITS
    no_teto = int((df[target] == maximo).sum())

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.hist(df[target], bins=40, color=AZUL, alpha=0.85, edgecolor=SUPERFICIE)
    ax.axvline(maximo, color=VERMELHO, linewidth=2)
    ax.annotate(
        f"{no_teto} alunos exatamente em {maximo:.0f}",
        xy=(maximo, ax.get_ylim()[1] * 0.85),
        xytext=(-18, 0),
        textcoords="offset points",
        ha="right",
        fontsize=9,
        color=VERMELHO,
    )
    ax.set_title("Distribuição da nota: o acúmulo no teto")
    ax.set_xlabel("Nota na prova")
    ax.set_ylabel("Alunos")
    _limpa_molduras(ax)
    fig.tight_layout()

    destino = _destino(path, "05_distribuicao_da_nota.png")
    fig.savefig(destino)
    plt.close(fig)
    return destino


def plot_model_coefficients(
    coeficientes: pd.DataFrame, path: Path | None = None
) -> Path:
    """Peso de cada hábito no modelo, em pontos por desvio padrão.

    Barras divergentes: azul para quem puxa a nota para cima, vermelho para
    quem puxa para baixo. O sinal também está no número ao lado da barra, então
    a cor não é o único canal.
    """
    apply_style()
    dados = coeficientes.dropna(subset=["pontos_por_desvio"]).copy()
    dados = dados.sort_values("pontos_por_desvio")
    cores = [AZUL if v > 0 else VERMELHO for v in dados["pontos_por_desvio"]]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    barras = ax.barh(
        [rotulo(c) for c in dados["variavel"]],
        dados["pontos_por_desvio"],
        color=cores,
        height=0.6,
    )
    ax.bar_label(
        barras,
        labels=[f"{v:+.1f}" for v in dados["pontos_por_desvio"]],
        padding=4,
        fontsize=9,
        color=TINTA_SECUNDARIA,
    )
    ax.axvline(0, color=EIXO, linewidth=1)
    ax.set_title("Peso de cada hábito no modelo")
    ax.set_xlabel("Pontos de nota por desvio padrão do hábito")
    ax.margins(x=0.15)
    ax.grid(axis="y", visible=False)
    _limpa_molduras(ax, manter=("bottom",))
    fig.tight_layout()

    destino = _destino(path, "06_peso_dos_habitos.png")
    fig.savefig(destino)
    plt.close(fig)
    return destino
