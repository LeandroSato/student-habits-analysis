"""Tratamento de ausentes e de inconsistências (tarefa 2 do desafio).

Duas regras guiam este módulo:

1. **Não inventar dado.** A ausência é tratada como informação ("não informado"),
   não preenchida com a moda ou com a média.
2. **Falhar alto em vez de consertar escondido.** Valor impossível interrompe o
   pipeline em vez de ser corrigido em silêncio: um CSV novo com erro de domínio
   precisa de decisão humana, não de um `clip` automático que ninguém vê.
"""

from __future__ import annotations

import pandas as pd

from src import config


class DomainViolationError(ValueError):
    """Alguma coluna trouxe valor fora do que é possível no mundo real."""


def remove_exact_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove linhas idênticas em todas as colunas.

    Na base do desafio não há nenhuma, mas o passo fica no pipeline porque ele
    não deve supor que o próximo arquivo venha igual — e o log registra zero,
    o que é um resultado, não um passo inútil.
    """
    duplicadas = int(df.duplicated().sum())
    if duplicadas == 0:
        return df.copy(), 0
    return df.drop_duplicates().reset_index(drop=True), duplicadas


def assert_within_domain(
    df: pd.DataFrame, ranges: dict[str, tuple[float, float]] | None = None
) -> None:
    """Interrompe o pipeline se houver valor fora do domínio.

    A tarefa 1 mostrou que a base atual não tem nenhum. Em vez de escrever um
    tratamento para um problema que não existe (código morto) ou de corrigir
    valores em silêncio, a escolha foi barrar: se um arquivo futuro trouxer
    "30 horas de estudo por dia", alguém precisa olhar.
    """
    ranges = ranges if ranges is not None else config.PLAUSIBLE_RANGES
    problemas = []
    for coluna, (minimo, maximo) in ranges.items():
        if coluna not in df.columns:
            continue
        s = df[coluna].dropna()
        fora = int(((s < minimo) | (s > maximo)).sum())
        if fora:
            problemas.append(
                f"{coluna}: {fora} valor(es) fora de [{minimo}, {maximo}] "
                f"(observado de {s.min()} a {s.max()})"
            )
    if problemas:
        raise DomainViolationError(
            "Valores impossíveis encontrados — " + "; ".join(problemas)
        )


def missing_as_category(
    df: pd.DataFrame,
    cols: list[str] | None = None,
    label: str = config.MISSING_LABEL,
) -> pd.DataFrame:
    """Transforma a ausência em categoria própria e cria uma flag por coluna.

    Por que não imputar pela moda: colocaria 91 alunos em "High School" sem
    nenhuma evidência, inflando um grupo e diluindo a diferença entre grupos na
    tarefa 3.

    Por que não descartar as linhas: são 9,1% da base, e o teste de Mann-Whitney
    não achou diferença de nota entre quem informou e quem não informou
    (p = 0,71), ou seja, descartar perderia 91 alunos sem corrigir viés algum.

    A flag `<coluna>_informado` permite checar depois se "não informar" tem
    relação com a nota — a própria ausência pode ser um sinal.
    """
    cols = cols if cols is not None else config.COLS_MISSING_AS_CATEGORY
    tratado = df.copy()
    for coluna in cols:
        if coluna not in tratado.columns:
            continue
        flag = coluna + config.MISSING_FLAG_SUFFIX
        tratado[flag] = tratado[coluna].notna().astype(int)
        tratado[coluna] = tratado[coluna].fillna(label)
    return tratado


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Roda o tratamento inteiro e devolve um log do que aconteceu.

    O log vai para o relatório: toda transformação aplicada fica registrada com
    número, não só com descrição.
    """
    linhas_entrada = len(df)

    sem_duplicatas, duplicadas = remove_exact_duplicates(df)
    assert_within_domain(sem_duplicatas)
    tratado = missing_as_category(sem_duplicatas)

    log = {
        "linhas_entrada": linhas_entrada,
        "linhas_saida": len(tratado),
        "duplicatas_removidas": duplicadas,
        "valores_impossiveis_corrigidos": 0,
        "colunas_com_ausencia_como_categoria": [
            c for c in config.COLS_MISSING_AS_CATEGORY if c in df.columns
        ],
        "rotulo_de_ausencia": config.MISSING_LABEL,
        "nulos_restantes": int(tratado.isna().sum().sum()),
    }
    return tratado, log
