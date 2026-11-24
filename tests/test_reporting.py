"""Testes da formatação dos relatórios.

Estavam dentro de `test_profiling.py`, que é o arquivo de outro módulo — vieram
para cá na revisão final. Entram também os testes de `write_report`, que até
então só era exercitado de verdade pelo script de análise.
"""

import pandas as pd

from src.reporting import markdown_table, write_report


def test_markdown_table_monta_cabecalho_e_linhas():
    tabela = markdown_table(pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}))
    linhas = tabela.splitlines()

    assert linhas[0] == "| a | b |"
    assert linhas[1] == "|---|---|"
    assert linhas[2] == "| 1 | x |"


def test_markdown_table_marca_ausente_com_travessao():
    tabela = markdown_table(pd.DataFrame({"a": [1.0, float("nan")]}))

    assert tabela.splitlines()[-1] == "| — |"


def test_markdown_table_pode_trazer_o_indice_como_coluna():
    df = pd.DataFrame({"valor": [10, 20]}, index=["linha_a", "linha_b"])

    tabela = markdown_table(df, index=True, index_label="nome")
    linhas = tabela.splitlines()

    assert linhas[0] == "| nome | valor |"
    assert linhas[2] == "| linha_a | 10 |"


def test_write_report_cria_a_pasta_e_grava_o_conteudo(tmp_path):
    destino = tmp_path / "subpasta" / "relatorio.md"

    write_report(destino, "Título do teste", ["primeiro bloco", "segundo bloco"])

    texto = destino.read_text(encoding="utf-8")
    assert texto.startswith("# Título do teste")
    assert "primeiro bloco" in texto
    assert "segundo bloco" in texto


def test_write_report_sobrescreve_o_arquivo_anterior(tmp_path):
    """A análise roda de novo em cima do mesmo caminho: não pode acumular."""
    destino = tmp_path / "relatorio.md"

    write_report(destino, "Primeira versão", ["conteúdo antigo"])
    write_report(destino, "Segunda versão", ["conteúdo novo"])

    texto = destino.read_text(encoding="utf-8")
    assert "conteúdo antigo" not in texto
    assert "conteúdo novo" in texto
