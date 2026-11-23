"""Formatação de tabelas em Markdown para os relatórios em reports/.

Escrito à mão em vez de usar `DataFrame.to_markdown` porque aquele método
exige a biblioteca `tabulate`; uma dependência a menos para quem for rodar.
"""

from __future__ import annotations

import pandas as pd


def _formata(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    if isinstance(valor, float):
        return f"{valor:g}"
    return str(valor)


def markdown_table(df: pd.DataFrame, index: bool = False, index_label: str = "") -> str:
    """Converte um DataFrame em tabela Markdown."""
    tabela = df.reset_index() if index else df
    if index and index_label:
        tabela = tabela.rename(columns={tabela.columns[0]: index_label})

    cabecalho = [str(c) for c in tabela.columns]
    linhas = [
        "| " + " | ".join(cabecalho) + " |",
        "|" + "|".join(["---"] * len(cabecalho)) + "|",
    ]
    for _, linha in tabela.iterrows():
        linhas.append("| " + " | ".join(_formata(v) for v in linha) + " |")
    return "\n".join(linhas)


def write_report(path, titulo: str, blocos: list[str]) -> None:
    """Grava o relatório, criando a pasta se preciso."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conteudo = f"# {titulo}\n\n" + "\n\n".join(blocos) + "\n"
    path.write_text(conteudo, encoding="utf-8")
