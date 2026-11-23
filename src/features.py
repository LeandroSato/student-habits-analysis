"""Variáveis derivadas (tarefa 2 do desafio).

Três tipos de derivada, cada uma com um propósito diferente:

- **Faixas** (`faixa_*`): servem à leitura e aos gráficos por grupo. Nota média
  por faixa de rede social é algo que se explica em uma frase; coeficiente de
  regressão não é.
- **Combinações** (`leisure_screen_hours`, `study_share`): juntam colunas que
  medem a mesma coisa (tempo de tela) e criam uma medida relativa, que compara
  alunos com rotinas de tamanhos diferentes.
- **Codificações** (`*_ord`, `*_bin`): texto com ordem natural e sim/não viram
  número para poderem entrar em correlação e no modelo.

Nada aqui substitui a coluna original: as derivadas são colunas novas, então a
base crua continua disponível e qualquer número do relatório é rastreável.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config

LEISURE_COL = "leisure_screen_hours"
STUDY_SHARE_COL = "study_share"


def add_bins(df: pd.DataFrame, specs: dict | None = None) -> pd.DataFrame:
    """Cria as colunas de faixa definidas em `config.BIN_SPECS`.

    As faixas são fechadas à esquerda (`right=False`): um valor exatamente em
    cima do corte cai na faixa de cima. Sem isso, 2,0 h de rede social iria para
    "1 a 2h", o que contradiz o rótulo.
    """
    specs = specs if specs is not None else config.BIN_SPECS
    com_faixas = df.copy()
    for nome, spec in specs.items():
        coluna = spec["coluna"]
        if coluna not in com_faixas.columns:
            continue
        com_faixas[nome] = pd.cut(
            com_faixas[coluna],
            bins=spec["bins"],
            labels=spec["labels"],
            right=False,
            include_lowest=True,
        )
    return com_faixas


def add_derived_hours(df: pd.DataFrame) -> pd.DataFrame:
    """Soma o tempo de tela de lazer e calcula a fatia do tempo dedicada ao estudo.

    `leisure_screen_hours` = redes sociais + streaming. As duas medem tempo de
    tela por lazer; somadas, dão o tamanho real do concorrente do estudo.

    `study_share` = estudo / (estudo + tela de lazer). É a medida relativa:
    2 h de estudo com 1 h de tela é uma rotina diferente de 2 h de estudo com
    6 h de tela, e em horas absolutas as duas aparecem iguais.

    Fica nulo quando o aluno não registra nenhuma das duas coisas (divisão por
    zero). Na base do desafio isso não acontece — nenhum aluno tem tela de lazer
    igual a zero — mas o guarda existe para não produzir infinito em silêncio.
    """
    derivadas = df.copy()
    derivadas[LEISURE_COL] = derivadas[config.LEISURE_SCREEN_COLS].sum(axis=1)

    tempo_medido = derivadas["study_hours_per_day"] + derivadas[LEISURE_COL]
    derivadas[STUDY_SHARE_COL] = np.where(
        tempo_medido > 0,
        (derivadas["study_hours_per_day"] / tempo_medido).round(4),
        np.nan,
    )
    return derivadas


def encode_ordinals(df: pd.DataFrame, maps: dict | None = None) -> pd.DataFrame:
    """Converte escalas de qualidade em número, preservando a ordem.

    `diet_quality` e `internet_quality` têm ordem natural (Poor < Fair/Average <
    Good), então 0/1/2 carrega informação de verdade.

    `parental_education_level` ficou fora de propósito: depois do tratamento ela
    tem a categoria "Não informado", que não ocupa lugar nenhum em uma escala
    ordenada. Ela entra no modelo como one-hot, na tarefa 4.
    """
    maps = maps if maps is not None else config.ORDINAL_MAPS
    codificado = df.copy()
    for coluna, mapa in maps.items():
        if coluna not in codificado.columns:
            continue
        codificado[coluna + config.ORDINAL_SUFFIX] = (
            codificado[coluna].map(mapa).astype("Int64")
        )
    return codificado


def encode_binaries(df: pd.DataFrame, maps: dict | None = None) -> pd.DataFrame:
    """Converte as colunas sim/não em 0/1 para entrarem na correlação."""
    maps = maps if maps is not None else config.BINARY_MAPS
    codificado = df.copy()
    for coluna, mapa in maps.items():
        if coluna not in codificado.columns:
            continue
        codificado[coluna + config.BINARY_SUFFIX] = (
            codificado[coluna].map(mapa).astype("Int64")
        )
    return codificado


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica as três famílias de derivadas, na ordem."""
    completo = add_bins(df)
    completo = add_derived_hours(completo)
    completo = encode_ordinals(completo)
    completo = encode_binaries(completo)
    return completo


def derived_columns(df: pd.DataFrame) -> list[str]:
    """Nomes das colunas criadas por `build_features` que existem em `df`."""
    candidatas = (
        list(config.BIN_SPECS)
        + [LEISURE_COL, STUDY_SHARE_COL]
        + [c + config.ORDINAL_SUFFIX for c in config.ORDINAL_MAPS]
        + [c + config.BINARY_SUFFIX for c in config.BINARY_MAPS]
        + [c + config.MISSING_FLAG_SUFFIX for c in config.COLS_MISSING_AS_CATEGORY]
    )
    return [c for c in candidatas if c in df.columns]
