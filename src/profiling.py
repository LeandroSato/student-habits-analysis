"""Diagnóstico de qualidade da base (tarefa 1 do desafio).

Cada função devolve um DataFrame ou dict pronto para ir ao relatório — nenhuma
imprime nada e nenhuma altera o DataFrame recebido. Isso mantém o diagnóstico
testável e deixa a formatação por conta de quem chama.
"""

from __future__ import annotations

import pandas as pd

from src import config
from src.data_loading import categorical_columns, numeric_columns


def column_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por coluna: tipo, preenchimento e cardinalidade."""
    total = len(df)
    linhas = []
    for coluna in df.columns:
        nulos = int(df[coluna].isna().sum())
        linhas.append(
            {
                "coluna": coluna,
                "dtype": str(df[coluna].dtype),
                "nao_nulos": total - nulos,
                "nulos": nulos,
                "pct_nulos": round(100 * nulos / total, 2) if total else 0.0,
                "unicos": int(df[coluna].nunique()),
            }
        )
    return pd.DataFrame(linhas)


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Só as colunas com valor ausente, da pior para a menos grave."""
    visao = column_overview(df)
    faltantes = visao.loc[visao["nulos"] > 0, ["coluna", "nulos", "pct_nulos"]]
    return faltantes.sort_values("nulos", ascending=False).reset_index(drop=True)


def duplicate_report(df: pd.DataFrame, id_col: str = config.ID_COL) -> dict:
    """Distingue linha inteira repetida de identificador repetido.

    São problemas diferentes: linha repetida é erro de carga; id repetido com
    conteúdo diferente pode ser dois alunos ou um registro corrigido.
    """
    return {
        "linhas": len(df),
        "linhas_duplicadas": int(df.duplicated().sum()),
        "ids_duplicados": int(df[id_col].duplicated().sum()),
    }


def numeric_summary(df: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    """Estatísticas descritivas das colunas numéricas, com assimetria.

    A assimetria entra porque ela antecipa dois problemas do passo seguinte:
    cauda longa (candidata a outlier) e distribuição que não é simétrica.
    """
    cols = cols if cols is not None else numeric_columns(df)
    linhas = []
    for coluna in cols:
        s = df[coluna].dropna()
        linhas.append(
            {
                "coluna": coluna,
                "contagem": int(s.count()),
                "media": round(float(s.mean()), 2),
                "desvio": round(float(s.std()), 2),
                "minimo": float(s.min()),
                "q25": round(float(s.quantile(0.25)), 2),
                "mediana": round(float(s.median()), 2),
                "q75": round(float(s.quantile(0.75)), 2),
                "maximo": float(s.max()),
                "assimetria": round(float(s.skew()), 2),
            }
        )
    return pd.DataFrame(linhas).set_index("coluna")


def categorical_summary(df: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    """Contagem e percentual de cada categoria, incluindo o ausente."""
    cols = cols if cols is not None else categorical_columns(df, exclude=[config.ID_COL])
    total = len(df)
    linhas = []
    for coluna in cols:
        contagens = df[coluna].value_counts(dropna=False)
        for valor, contagem in contagens.items():
            linhas.append(
                {
                    "coluna": coluna,
                    "valor": "(ausente)" if pd.isna(valor) else valor,
                    "contagem": int(contagem),
                    "pct": round(100 * int(contagem) / total, 2) if total else 0.0,
                }
            )
    return pd.DataFrame(linhas)


def outlier_report(
    df: pd.DataFrame, cols: list[str] | None = None, k: float = 1.5
) -> pd.DataFrame:
    """Outliers pela regra do IQR (Tukey), com k=1.5.

    Escolhido por não depender de normalidade — a base tem variáveis bem
    assimétricas. O relatório só conta e mostra os limites: nada é removido
    aqui, porque valor extremo plausível (estudar 8h/dia) é informação, não erro.
    """
    cols = cols if cols is not None else numeric_columns(df)
    linhas = []
    for coluna in cols:
        s = df[coluna].dropna()
        q1, q3 = float(s.quantile(0.25)), float(s.quantile(0.75))
        iqr = q3 - q1
        inferior, superior = q1 - k * iqr, q3 + k * iqr
        abaixo = int((s < inferior).sum())
        acima = int((s > superior).sum())
        linhas.append(
            {
                "coluna": coluna,
                "limite_inferior": round(inferior, 2),
                "limite_superior": round(superior, 2),
                "abaixo": abaixo,
                "acima": acima,
                "total_outliers": abaixo + acima,
                "pct_outliers": round(100 * (abaixo + acima) / len(s), 2) if len(s) else 0.0,
            }
        )
    return pd.DataFrame(linhas)


def range_violations(
    df: pd.DataFrame, ranges: dict[str, tuple[float, float]] | None = None
) -> pd.DataFrame:
    """Valores fora do que é possível no mundo real (não do que é comum).

    Diferente de outlier: aqui a pergunta é "esse número pode existir?".
    """
    ranges = ranges if ranges is not None else config.PLAUSIBLE_RANGES
    linhas = []
    for coluna, (minimo, maximo) in ranges.items():
        if coluna not in df.columns:
            continue
        s = df[coluna].dropna()
        fora = int(((s < minimo) | (s > maximo)).sum())
        linhas.append(
            {
                "coluna": coluna,
                "minimo_esperado": minimo,
                "maximo_esperado": maximo,
                "minimo_observado": float(s.min()),
                "maximo_observado": float(s.max()),
                "violacoes": fora,
            }
        )
    return pd.DataFrame(linhas)


def daily_hours_check(
    df: pd.DataFrame,
    cols: list[str] | None = None,
    max_hours: float = config.MAX_HOURS_PER_DAY,
) -> dict:
    """As horas declaradas cabem em um dia?

    Checagem cruzada entre colunas: cada uma pode ser plausível sozinha e o
    conjunto ser impossível.
    """
    cols = cols if cols is not None else config.DAILY_HOURS_COLS
    soma = df[cols].sum(axis=1)
    return {
        "colunas": cols,
        "limite": max_hours,
        "maior_soma": round(float(soma.max()), 2),
        "media_soma": round(float(soma.mean()), 2),
        "linhas_acima_do_limite": int((soma > max_hours).sum()),
    }


def extreme_value_concentration(
    df: pd.DataFrame, col: str = config.TARGET
) -> dict:
    """Quantos registros estão empilhados no mínimo e no máximo da coluna.

    Importa para o alvo: muita gente no valor máximo indica efeito teto, e
    qualquer modelo linear vai subestimar justamente esse grupo.
    """
    s = df[col].dropna()
    minimo, maximo = float(s.min()), float(s.max())
    n_min, n_max = int((s == minimo).sum()), int((s == maximo).sum())
    return {
        "coluna": col,
        "valor_minimo": minimo,
        "n_no_minimo": n_min,
        "pct_no_minimo": round(100 * n_min / len(s), 2),
        "valor_maximo": maximo,
        "n_no_maximo": n_max,
        "pct_no_maximo": round(100 * n_max / len(s), 2),
    }
