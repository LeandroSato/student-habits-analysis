"""Leitura do CSV bruto e separação das colunas por tipo.

Uma única porta de entrada para os dados: assim o notebook/script de análise,
o app Streamlit e os testes leem a base do mesmo jeito.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import config


class MissingColumnsError(ValueError):
    """CSV recebido não tem as colunas que o projeto espera."""


def load_raw(path: str | Path | None = None) -> pd.DataFrame:
    """Lê o CSV bruto e confere o contrato de colunas.

    Falhar cedo aqui vale mais do que um erro obscuro três módulos depois.
    """
    csv_path = Path(path) if path is not None else config.RAW_CSV
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV não encontrado em {csv_path}. "
            "Coloque o arquivo do desafio em data/raw/."
        )

    df = pd.read_csv(csv_path)
    missing = [c for c in config.EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise MissingColumnsError(f"Colunas ausentes no CSV: {missing}")

    return df


def numeric_columns(df: pd.DataFrame, exclude: list[str] | None = None) -> list[str]:
    """Colunas numéricas do DataFrame, na ordem em que aparecem."""
    exclude = set(exclude or [])
    return [
        c
        for c in df.select_dtypes(include="number").columns
        if c not in exclude
    ]


def categorical_columns(df: pd.DataFrame, exclude: list[str] | None = None) -> list[str]:
    """Colunas não numéricas (texto/categoria).

    Detectado por exclusão em vez de `select_dtypes("object")` porque o pandas 3
    passou a usar o dtype `str` para texto, e a checagem antiga devolve vazio.
    """
    exclude = set(exclude or [])
    numeric = set(df.select_dtypes(include="number").columns)
    return [c for c in df.columns if c not in numeric and c not in exclude]
