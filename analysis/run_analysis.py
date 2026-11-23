"""Roda a análise de ponta a ponta e grava os relatórios em reports/.

Uso:  python analysis/run_analysis.py

Script em vez de notebook de propósito: roda do zero em qualquer máquina, dá
diff legível no git e garante que todo número citado no README saiu daqui.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite rodar como script solto (python analysis/run_analysis.py) sem instalar
# o projeto como pacote.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from src import config, profiling  # noqa: E402
from src.data_loading import categorical_columns, load_raw, numeric_columns  # noqa: E402
from src.reporting import markdown_table, write_report  # noqa: E402

CRASE = "`"


def _cod(nome: str) -> str:
    """Envolve um nome de coluna em acento grave, para o Markdown."""
    return f"{CRASE}{nome}{CRASE}"


def bloco_visao_geral(df: pd.DataFrame) -> str:
    dup = profiling.duplicate_report(df)
    linhas = [
        "## 1.1 O que é a base",
        "",
        f"- **{dup['linhas']} linhas x {len(df.columns)} colunas**, uma linha por aluno.",
        f"- Alvo da análise: {_cod(config.TARGET)} (nota na prova).",
        f"- Linhas inteiras duplicadas: **{dup['linhas_duplicadas']}**.",
        f"- Valores de {_cod(config.ID_COL)} repetidos: **{dup['ids_duplicados']}**.",
        "",
        "### Tipos, preenchimento e cardinalidade",
        "",
        markdown_table(profiling.column_overview(df)),
    ]
    return "\n".join(linhas)


def bloco_ausentes(df: pd.DataFrame) -> str:
    faltantes = profiling.missing_report(df)
    partes = ["## 1.2 Valores ausentes", ""]

    if faltantes.empty:
        partes.append("Nenhuma coluna tem valor ausente.")
        return "\n".join(partes)

    pior = faltantes.iloc[0]
    partes += [
        f"Ausência concentrada em **{len(faltantes)}** de {len(df.columns)} colunas. "
        f"A mais afetada é {_cod(pior['coluna'])}, com **{pior['nulos']} registros "
        f"({pior['pct_nulos']}%)** em branco.",
        "",
        markdown_table(faltantes),
        "",
        "O que fazer com esses registros é decisão da etapa de engenharia de dados "
        "(tarefa 2), não desta: aqui o objetivo é medir o tamanho do problema.",
    ]
    return "\n".join(partes)


def bloco_numericas(df: pd.DataFrame) -> str:
    resumo = profiling.numeric_summary(df)
    assimetricas = resumo[resumo["assimetria"].abs() >= 0.5]
    partes = [
        "## 1.3 Distribuição das variáveis numéricas",
        "",
        markdown_table(resumo, index=True, index_label="coluna"),
        "",
    ]
    if assimetricas.empty:
        partes.append(
            "Nenhuma variável numérica tem assimetria relevante (|assimetria| >= 0,5): "
            "as distribuições são aproximadamente simétricas."
        )
    else:
        nomes = ", ".join(_cod(c) for c in assimetricas.index)
        partes.append(
            f"Variáveis com assimetria relevante (|assimetria| >= 0,5): {nomes}. "
            "As demais são aproximadamente simétricas."
        )
    return "\n".join(partes)


def bloco_categoricas(df: pd.DataFrame) -> str:
    cols = categorical_columns(df, exclude=[config.ID_COL])
    resumo = profiling.categorical_summary(df, cols=cols)
    return "\n".join(
        [
            "## 1.4 Distribuição das variáveis categóricas",
            "",
            f"São {len(cols)} colunas categóricas (fora o identificador). "
            "A linha `(ausente)` aparece quando a coluna tem valor em branco.",
            "",
            markdown_table(resumo),
        ]
    )


def bloco_qualidade(df: pd.DataFrame) -> str:
    violacoes = profiling.range_violations(df)
    horas = profiling.daily_hours_check(df)
    outliers = profiling.outlier_report(df, cols=numeric_columns(df))
    extremos = profiling.extreme_value_concentration(df, config.TARGET)

    total_violacoes = int(violacoes["violacoes"].sum())
    com_outlier = outliers[outliers["total_outliers"] > 0]
    colunas_horas = ", ".join(_cod(c) for c in horas["colunas"])

    if total_violacoes == 0:
        veredito_dominio = "Nenhuma coluna tem valor impossível."
    else:
        veredito_dominio = "Há valores impossíveis a tratar na tarefa 2."

    if horas["linhas_acima_do_limite"] == 0:
        veredito_horas = (
            "Nenhum aluno declara um dia impossível: as colunas de tempo são "
            "coerentes entre si."
        )
    else:
        veredito_horas = (
            "Essas linhas são inconsistentes e precisam de decisão na tarefa 2."
        )

    if com_outlier.empty:
        veredito_outliers = "Nenhuma coluna numérica tem outlier pela regra do IQR."
    else:
        lista = ", ".join(
            f"{_cod(r.coluna)} ({r.total_outliers}; {r.pct_outliers}%)"
            for r in com_outlier.itertuples()
        )
        veredito_outliers = (
            f"Colunas com pontos fora da cerca: {lista}. Como nenhum deles viola o "
            "domínio (item a), são valores extremos **plausíveis** e serão mantidos: "
            "descartá-los apagaria justamente os alunos de comportamento mais "
            "acentuado, que são os que interessam à análise."
        )

    if extremos["pct_no_maximo"] >= 1:
        veredito_teto = (
            f"A concentração de {extremos['pct_no_maximo']}% dos alunos exatamente em "
            f"{extremos['valor_maximo']} indica **efeito teto**: a nota não tem para "
            "onde subir. Um modelo linear vai errar para baixo nesse grupo e pode "
            f"prever nota acima de {extremos['valor_maximo']}, o que não existe. Fica "
            "registrado como limitação e será tratado na tarefa 4, limitando a "
            "previsão ao intervalo válido."
        )
    else:
        veredito_teto = "Não há concentração relevante nos extremos."

    partes = [
        "## 1.5 Diagnóstico de qualidade",
        "",
        "### a) Valores impossíveis",
        "",
        "A pergunta aqui não é se o valor é raro, e sim se ele **pode existir**. Os "
        "limites são de domínio (horas de um dia, percentual de 0 a 100, escala de 1 "
        "a 10), não os observados na amostra.",
        "",
        markdown_table(violacoes),
        "",
        f"Total de valores fora do domínio: **{total_violacoes}**. {veredito_dominio}",
        "",
        "### b) Horas declaradas por dia",
        "",
        f"Somando {colunas_horas}, a maior soma observada é de "
        f"**{horas['maior_soma']} h/dia** (média de {horas['media_soma']} h) e "
        f"**{horas['linhas_acima_do_limite']} linhas** passam de {horas['limite']} h. "
        f"{veredito_horas}",
        "",
        "### c) Outliers (regra do IQR, k = 1,5)",
        "",
        markdown_table(outliers),
        "",
        veredito_outliers,
        "",
        "### d) Concentração nos extremos do alvo",
        "",
        f"{_cod(extremos['coluna'])} vai de **{extremos['valor_minimo']}** a "
        f"**{extremos['valor_maximo']}**. No valor máximo há "
        f"**{extremos['n_no_maximo']} alunos ({extremos['pct_no_maximo']}%)** e no "
        f"mínimo **{extremos['n_no_minimo']} ({extremos['pct_no_minimo']}%)**.",
        "",
        veredito_teto,
    ]
    return "\n".join(partes)


def bloco_conclusao(df: pd.DataFrame) -> str:
    faltantes = profiling.missing_report(df)
    dup = profiling.duplicate_report(df)
    violacoes = profiling.range_violations(df)
    horas = profiling.daily_hours_check(df)
    extremos = profiling.extreme_value_concentration(df, config.TARGET)

    achados = []
    if dup["linhas_duplicadas"] == 0 and dup["ids_duplicados"] == 0:
        achados.append("sem duplicatas de linha ou de identificador")
    if int(violacoes["violacoes"].sum()) == 0 and horas["linhas_acima_do_limite"] == 0:
        achados.append("nenhum valor impossível e horas coerentes entre si")
    if faltantes.empty:
        achados.append("sem valores ausentes")
        pendencia_ausentes = "Nenhuma ausência a tratar."
    else:
        pior = faltantes.iloc[0]
        achados.append(f"ausência restrita a {_cod(pior['coluna'])} ({pior['pct_nulos']}%)")
        pendencia_ausentes = (
            f"**Ausência em {_cod(pior['coluna'])}** ({pior['nulos']} registros): "
            "decidir na tarefa 2."
        )
    achados.append(f"efeito teto em {_cod(config.TARGET)} ({extremos['pct_no_maximo']}%)")

    return "\n".join(
        [
            "## 1.6 Veredito",
            "",
            "A base está em boa condição: " + "; ".join(achados) + ".",
            "",
            "Os dois pontos que exigem decisão explícita adiante:",
            "",
            f"1. {pendencia_ausentes}",
            f"2. **Efeito teto em {_cod(config.TARGET)}** "
            f"({extremos['n_no_maximo']} alunos em {extremos['valor_maximo']}): "
            "limita o modelo da tarefa 4.",
        ]
    )


def etapa_1_exploracao(df: pd.DataFrame) -> Path:
    destino = config.REPORTS_DIR / "01_exploracao.md"
    write_report(
        destino,
        "1. Exploração inicial e diagnóstico de qualidade",
        [
            "Gerado por `analysis/run_analysis.py`. Todo número desta página sai do "
            f"arquivo `data/raw/{config.RAW_CSV.name}`.",
            bloco_visao_geral(df),
            bloco_ausentes(df),
            bloco_numericas(df),
            bloco_categoricas(df),
            bloco_qualidade(df),
            bloco_conclusao(df),
        ],
    )
    return destino


def main() -> None:
    df = load_raw()
    print(f"Base carregada: {len(df)} linhas x {len(df.columns)} colunas")

    destino = etapa_1_exploracao(df)
    print(f"Etapa 1 (exploracao) -> {destino.relative_to(config.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
