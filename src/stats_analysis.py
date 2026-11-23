"""Correlações, ranking de influência e comparação entre grupos (tarefa 3).

Três cuidados moldam este módulo:

- **Pearson e Spearman lado a lado.** Pearson mede relação linear; Spearman mede
  se a ordem acompanha. Quando os dois concordam, a relação é sólida; quando
  divergem, há curva ou extremo puxando o resultado — e isso precisa aparecer.
- **Correção para múltiplos testes.** Testar 15 variáveis contra a mesma nota a
  5% faz esperar quase um "achado" falso por acaso. Todos os p-valores passam
  pela correção de Holm-Bonferroni antes de qualquer conclusão.
- **Nada aqui mede causa.** Correlação diz que duas coisas andam juntas, não que
  uma produz a outra. Os nomes das funções falam de "influência" no sentido
  estatístico de força de associação, e os relatórios repetem o aviso.
"""

from __future__ import annotations

import itertools

import pandas as pd
from scipy import stats

from src import config

# Faixas de interpretação da força de |r|. Convenção usual em ciências sociais
# (Cohen), não um corte vindo desta base.
FORCA_FORTE = 0.5
FORCA_MODERADA = 0.3
FORCA_FRACA = 0.1


def holm_adjust(pvalues: list[float]) -> list[float]:
    """Correção de Holm-Bonferroni para testes múltiplos.

    Ordena os p-valores, multiplica cada um por (m - posição) e impede que a
    sequência caia. Menos conservadora que Bonferroni puro e sem supor que os
    testes sejam independentes — as variáveis da base se correlacionam entre si.
    """
    m = len(pvalues)
    if m == 0:
        return []

    ordem = sorted(range(m), key=lambda i: pvalues[i])
    ajustados = [0.0] * m
    maior_ate_agora = 0.0
    for posicao, indice in enumerate(ordem):
        valor = min(1.0, (m - posicao) * pvalues[indice])
        maior_ate_agora = max(maior_ate_agora, valor)
        ajustados[indice] = round(maior_ate_agora, 6)
    return ajustados


def _classifica_forca(r: float) -> str:
    forca = abs(r)
    if forca >= FORCA_FORTE:
        return "forte"
    if forca >= FORCA_MODERADA:
        return "moderada"
    if forca >= FORCA_FRACA:
        return "fraca"
    return "desprezível"


def correlation_with_target(
    df: pd.DataFrame,
    cols: list[str] | None = None,
    target: str = config.TARGET,
    method: str = "pearson",
    alpha: float = config.ALPHA,
) -> pd.DataFrame:
    """Correlação de cada variável com o alvo, com p-valor corrigido.

    Coluna constante é ignorada: correlação com algo que não varia não existe
    (o cálculo devolveria indefinido).
    """
    cols = cols if cols is not None else config.CORRELATION_COLS
    funcao = stats.pearsonr if method == "pearson" else stats.spearmanr

    linhas = []
    for coluna in cols:
        if coluna not in df.columns or coluna == target:
            continue
        par = df[[coluna, target]].astype("float64").dropna()
        if len(par) < 3 or par[coluna].std() == 0 or par[target].std() == 0:
            continue
        resultado = funcao(par[coluna], par[target])
        linhas.append(
            {
                "variavel": coluna,
                "metodo": method,
                "n": len(par),
                "r": round(float(resultado.statistic), 3),
                "p_valor": float(resultado.pvalue),
            }
        )

    if not linhas:
        return pd.DataFrame(
            columns=["variavel", "metodo", "n", "r", "p_valor", "p_ajustado", "significativo"]
        )

    tabela = pd.DataFrame(linhas)
    tabela["p_ajustado"] = holm_adjust(tabela["p_valor"].tolist())
    tabela["significativo"] = tabela["p_ajustado"] < alpha
    tabela["p_valor"] = tabela["p_valor"].round(6)
    return tabela


def influence_ranking(
    df: pd.DataFrame,
    cols: list[str] | None = None,
    target: str = config.TARGET,
    alpha: float = config.ALPHA,
) -> pd.DataFrame:
    """Ranking das variáveis por força de associação com o alvo.

    Traz Pearson e Spearman juntos de propósito: se os dois discordarem, a
    relação não é simplesmente linear e a leitura precisa de cuidado extra.
    """
    pearson = correlation_with_target(df, cols=cols, target=target, method="pearson", alpha=alpha)
    spearman = correlation_with_target(df, cols=cols, target=target, method="spearman", alpha=alpha)

    if pearson.empty:
        return pearson

    ranking = pearson.merge(
        spearman[["variavel", "r", "p_ajustado"]],
        on="variavel",
        suffixes=("_pearson", "_spearman"),
        how="left",
    ).rename(
        columns={
            "r_pearson": "r_pearson",
            "r_spearman": "r_spearman",
            "p_ajustado_pearson": "p_ajustado",
            "p_ajustado_spearman": "p_ajustado_spearman",
        }
    )

    ranking["direcao"] = ranking["r_pearson"].map(
        lambda r: "positiva" if r > 0 else ("negativa" if r < 0 else "nula")
    )
    ranking["forca"] = ranking["r_pearson"].map(_classifica_forca)
    ranking["concordam"] = (
        ranking["r_pearson"] * ranking["r_spearman"] > 0
    ) & ((ranking["r_pearson"] - ranking["r_spearman"]).abs() < 0.1)

    ranking = ranking.drop(columns=["metodo"], errors="ignore")
    ranking["forca_abs"] = ranking["r_pearson"].abs()
    ranking = ranking.sort_values("forca_abs", ascending=False).drop(columns=["forca_abs"])
    return ranking.reset_index(drop=True)


def correlation_matrix(
    df: pd.DataFrame, cols: list[str] | None = None, method: str = "pearson"
) -> pd.DataFrame:
    """Matriz de correlação das colunas pedidas, pronta para o mapa de calor."""
    cols = cols if cols is not None else config.CORRELATION_COLS + [config.TARGET]
    presentes = [c for c in cols if c in df.columns]
    return df[presentes].astype("float64").corr(method=method).round(3)


def multicollinearity(
    df: pd.DataFrame,
    cols: list[str] | None = None,
    threshold: float = config.MULTICOLLINEARITY_THRESHOLD,
) -> pd.DataFrame:
    """Pares de preditoras que carregam quase a mesma informação.

    Importa para o modelo da tarefa 4: com duas variáveis quase idênticas, o
    coeficiente de cada uma fica instável e a leitura "quanto cada hora pesa"
    deixa de valer.
    """
    cols = cols if cols is not None else config.CORRELATION_COLS
    presentes = [c for c in cols if c in df.columns]
    matriz = df[presentes].astype("float64").corr()

    linhas = [
        {"variavel_a": a, "variavel_b": b, "r": round(float(matriz.loc[a, b]), 3)}
        for a, b in itertools.combinations(presentes, 2)
        if abs(matriz.loc[a, b]) >= threshold
    ]
    tabela = pd.DataFrame(linhas, columns=["variavel_a", "variavel_b", "r"])
    if tabela.empty:
        return tabela
    return tabela.reindex(
        tabela["r"].abs().sort_values(ascending=False).index
    ).reset_index(drop=True)


def _ordem_dos_grupos(serie: pd.Series) -> list:
    """Ordem de exibição: a das categorias, se houver; alfabética, se não."""
    if isinstance(serie.dtype, pd.CategoricalDtype):
        return [c for c in serie.cat.categories if c in set(serie.dropna())]
    return sorted(serie.dropna().unique())


def group_summary(
    df: pd.DataFrame, group_col: str, target: str = config.TARGET
) -> pd.DataFrame:
    """Nota por grupo: quantos alunos, média, mediana e desvio."""
    linhas = []
    for grupo in _ordem_dos_grupos(df[group_col]):
        notas = df.loc[df[group_col] == grupo, target].dropna()
        linhas.append(
            {
                "grupo": grupo,
                "alunos": int(len(notas)),
                "media": round(float(notas.mean()), 2),
                "mediana": round(float(notas.median()), 2),
                "desvio": round(float(notas.std()), 2),
            }
        )
    return pd.DataFrame(linhas)


def compare_groups(
    df: pd.DataFrame,
    group_col: str,
    target: str = config.TARGET,
    alpha: float = config.ALPHA,
) -> dict:
    """A nota difere entre os grupos dessa coluna?

    Teste de Kruskal-Wallis: serve para dois ou mais grupos, não exige
    distribuição normal e não supõe variância igual — condições que uma nota
    autodeclarada em grupos de tamanhos diferentes não cumpre.

    Tamanho de efeito por epsilon ao quadrado (H / (n - 1)): sem ele, p pequeno
    com amostra grande vira "diferença importante" quando pode ser mínima.
    """
    amostras = [
        df.loc[df[group_col] == grupo, target].dropna()
        for grupo in _ordem_dos_grupos(df[group_col])
    ]
    amostras = [a for a in amostras if len(a) > 0]
    n_total = int(sum(len(a) for a in amostras))

    if len(amostras) < 2 or n_total < 3:
        return {
            "coluna": group_col,
            "teste": "Kruskal-Wallis",
            "n_grupos": len(amostras),
            "n": n_total,
            "H": None,
            "p_valor": None,
            "efeito_epsilon2": None,
            "significativo": False,
        }

    resultado = stats.kruskal(*amostras)
    epsilon2 = float(resultado.statistic) / (n_total - 1)
    return {
        "coluna": group_col,
        "teste": "Kruskal-Wallis",
        "n_grupos": len(amostras),
        "n": n_total,
        "H": round(float(resultado.statistic), 2),
        "p_valor": round(float(resultado.pvalue), 6),
        "efeito_epsilon2": round(epsilon2, 3),
        "significativo": bool(resultado.pvalue < alpha),
    }


def compare_all_groups(
    df: pd.DataFrame,
    group_cols: list[str] | None = None,
    target: str = config.TARGET,
    alpha: float = config.ALPHA,
) -> pd.DataFrame:
    """Roda a comparação em várias colunas e corrige os p-valores em conjunto."""
    group_cols = group_cols if group_cols is not None else config.GROUP_COLS
    resultados = [
        compare_groups(df, coluna, target=target, alpha=alpha)
        for coluna in group_cols
        if coluna in df.columns
    ]
    resultados = [r for r in resultados if r["p_valor"] is not None]
    if not resultados:
        return pd.DataFrame()

    tabela = pd.DataFrame(resultados)
    tabela["p_ajustado"] = holm_adjust(tabela["p_valor"].tolist())
    tabela["significativo"] = tabela["p_ajustado"] < alpha
    return tabela.sort_values("p_ajustado").reset_index(drop=True)
