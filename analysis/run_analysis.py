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

from src import cleaning, config, features, profiling  # noqa: E402
from src import stats_analysis as sa  # noqa: E402
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


def bloco_decisao_ausentes(df: pd.DataFrame) -> str:
    check = profiling.missingness_check(df, "parental_education_level")
    coluna = _cod("parental_education_level")

    tabela = pd.DataFrame(
        [
            {
                "grupo": "não informou",
                "alunos": check["n_ausente"],
                "nota média": check["media_ausente"],
            },
            {
                "grupo": "informou",
                "alunos": check["n_presente"],
                "nota média": check["media_presente"],
            },
        ]
    )

    if check["p_valor"] is not None and check["p_valor"] < 0.05:
        leitura = (
            f"O teste de Mann-Whitney dá **p = {check['p_valor']}**, abaixo de 0,05: "
            "quem não informou tem nota diferente de quem informou. A ausência "
            "carrega sinal e **não pode** ser descartada nem preenchida pela moda."
        )
    else:
        leitura = (
            f"O teste de Mann-Whitney dá **p = {check['p_valor']}**, bem acima de "
            "0,05: não há evidência de que a nota de quem não informou seja "
            f"diferente (diferença observada de {check['diferenca']} ponto). A "
            "ausência parece aleatória em relação ao alvo."
        )

    return "\n".join(
        [
            "## 2.1 Decisão sobre os valores ausentes",
            "",
            f"{coluna} é a única coluna com ausência: **{check['n_ausente']} de "
            f"{check['n_ausente'] + check['n_presente']} alunos**. Antes de decidir o "
            "que fazer, a pergunta é se essa ausência tem relação com a nota.",
            "",
            markdown_table(tabela),
            "",
            leitura,
            "",
            "### As três opções, e por que a escolhida",
            "",
            "| Opção | Efeito | Decisão |",
            "|---|---|---|",
            f"| Descartar as {check['n_ausente']} linhas | Perde "
            f"{round(100 * check['n_ausente'] / len(df), 1)}% da base sem corrigir "
            "viés nenhum, já que a ausência não se liga à nota | descartada |",
            "| Preencher pela moda (`High School`) | Põe "
            f"{check['n_ausente']} alunos em um grupo sem nenhuma evidência: infla "
            "esse grupo e dilui a comparação entre grupos da tarefa 3 | descartada |",
            f"| Categoria própria `{config.MISSING_LABEL}` + flag "
            f"`parental_education_level{config.MISSING_FLAG_SUFFIX}` | Mantém os "
            "1000 alunos, não inventa valor e deixa a própria ausência disponível "
            "para análise | **escolhida** |",
            "",
            "A flag existe por um motivo prático: se não informar a escolaridade dos "
            "pais estivesse associado à nota, a flag mostraria isso na matriz de "
            "correlação. Aqui ela serve de prova de que não está.",
        ]
    )


def bloco_tratamento(log: dict) -> str:
    tabela = pd.DataFrame(
        [
            {"passo": "linhas na entrada", "resultado": log["linhas_entrada"]},
            {"passo": "linhas duplicadas removidas", "resultado": log["duplicatas_removidas"]},
            {
                "passo": "valores impossíveis corrigidos",
                "resultado": log["valores_impossiveis_corrigidos"],
            },
            {
                "passo": "colunas com ausência virada categoria",
                "resultado": len(log["colunas_com_ausencia_como_categoria"]),
            },
            {"passo": "nulos restantes", "resultado": log["nulos_restantes"]},
            {"passo": "linhas na saída", "resultado": log["linhas_saida"]},
        ]
    )
    return "\n".join(
        [
            "## 2.2 O que o tratamento fez",
            "",
            markdown_table(tabela),
            "",
            "### Inconsistências: barrar em vez de consertar escondido",
            "",
            "A tarefa 1 não encontrou nenhum valor fora do domínio, então não havia "
            "o que corrigir. Em vez de escrever um tratamento para um problema "
            "inexistente — código morto que ninguém testa — o pipeline **valida e "
            "interrompe**: se um arquivo futuro trouxer 30 horas de estudo por dia, "
            "`clean()` levanta `DomainViolationError` e para. Corrigir em silêncio "
            "com um `clip` seria pior: o número ficaria plausível e errado.",
            "",
            "A remoção de duplicatas segue no pipeline pelo mesmo raciocínio ao "
            "contrário: custa nada, e o log registrando zero é um resultado "
            "verificado, não um passo inútil.",
        ]
    )


def bloco_faixas(df: pd.DataFrame) -> str:
    partes = [
        "## 2.3 Faixas criadas",
        "",
        "Faixa serve à leitura: “alunos que passam mais de 4h em redes sociais "
        "tiram X” se explica em uma frase, coeficiente de regressão não. Todas as "
        "faixas são **fechadas à esquerda** — um valor exatamente no corte cai na "
        "faixa de cima, senão 2,0 h cairia em “1 a 2h” e contradiria o rótulo.",
        "",
    ]
    for nome, spec in config.BIN_SPECS.items():
        contagem = df[nome].value_counts().reindex(spec["labels"], fill_value=0)
        tabela = pd.DataFrame(
            {
                "faixa": contagem.index,
                "alunos": contagem.to_numpy(),
                "pct": (100 * contagem / len(df)).round(1).to_numpy(),
            }
        )
        cortes = ", ".join(
            "infinito" if c == config.INF else str(c) for c in spec["bins"]
        )
        partes += [
            f"### {_cod(nome)} — de {_cod(spec['coluna'])}",
            "",
            f"Cortes: {cortes}.",
            "",
            f"**Por quê:** {spec['motivo']}",
            "",
            markdown_table(tabela),
            "",
        ]
    return "\n".join(partes).rstrip()


def bloco_combinacoes(df: pd.DataFrame) -> str:
    resumo = profiling.numeric_summary(
        df, cols=[features.LEISURE_COL, features.STUDY_SHARE_COL]
    )
    nulos_share = int(df[features.STUDY_SHARE_COL].isna().sum())
    return "\n".join(
        [
            "## 2.4 Combinações entre colunas",
            "",
            f"**{_cod(features.LEISURE_COL)}** = "
            + " + ".join(_cod(c) for c in config.LEISURE_SCREEN_COLS)
            + ". As duas medem tempo de tela por lazer; somadas, dão o tamanho real "
            "do concorrente do estudo, em vez de duas metades analisadas à parte.",
            "",
            f"**{_cod(features.STUDY_SHARE_COL)}** = estudo ÷ (estudo + tela de "
            "lazer). É a medida relativa: 2h de estudo com 1h de tela é uma rotina "
            "diferente de 2h de estudo com 6h de tela, e em horas absolutas as duas "
            "aparecem iguais.",
            "",
            markdown_table(resumo, index=True, index_label="coluna"),
            "",
            f"Nulos em {_cod(features.STUDY_SHARE_COL)}: **{nulos_share}**. A coluna "
            "fica nula quando o aluno não registra nem estudo nem tela (divisão por "
            "zero); na base do desafio isso não ocorre, mas o guarda existe para não "
            "gerar infinito em silêncio.",
        ]
    )


def bloco_codificacoes(df: pd.DataFrame) -> str:
    linhas_ord = []
    for coluna, mapa in config.ORDINAL_MAPS.items():
        ordem = " < ".join(f"{k} = {v}" for k, v in sorted(mapa.items(), key=lambda kv: kv[1]))
        linhas_ord.append(
            {
                "coluna": coluna,
                "nova coluna": coluna + config.ORDINAL_SUFFIX,
                "escala": ordem,
            }
        )
    linhas_bin = [
        {
            "coluna": coluna,
            "nova coluna": coluna + config.BINARY_SUFFIX,
            "escala": " · ".join(f"{k} = {v}" for k, v in mapa.items()),
        }
        for coluna, mapa in config.BINARY_MAPS.items()
    ]

    return "\n".join(
        [
            "## 2.5 Codificações",
            "",
            "Texto com ordem natural vira número para poder entrar em correlação e "
            "no modelo. Sim/não vira 0/1 pelo mesmo motivo.",
            "",
            markdown_table(pd.DataFrame(linhas_ord + linhas_bin)),
            "",
            f"{_cod('parental_education_level')} ficou **de fora** da codificação "
            "ordinal de propósito: depois do tratamento ela tem a categoria "
            f"`{config.MISSING_LABEL}`, que não ocupa lugar nenhum em uma escala "
            "ordenada. Ela entra no modelo da tarefa 4 como one-hot.",
            "",
            "### Todas as colunas derivadas",
            "",
            ", ".join(_cod(c) for c in features.derived_columns(df))
            + f" — {len(features.derived_columns(df))} colunas novas, nenhuma "
            "substituindo a original.",
        ]
    )


def etapa_2_engenharia(df: pd.DataFrame) -> tuple[pd.DataFrame, Path]:
    tratado, log = cleaning.clean(df)
    com_features = features.build_features(tratado)

    destino = config.REPORTS_DIR / "02_engenharia.md"
    write_report(
        destino,
        "2. Engenharia de dados",
        [
            "Gerado por `analysis/run_analysis.py`. Cada transformação desta página "
            "tem o motivo escrito junto, porque decisão sem motivo não se defende.",
            bloco_decisao_ausentes(df),
            bloco_tratamento(log),
            bloco_faixas(com_features),
            bloco_combinacoes(com_features),
            bloco_codificacoes(com_features),
        ],
    )
    return com_features, destino


AVISO_CAUSA = (
    "> **Correlação não é causa.** Tudo nesta página mede se duas coisas andam "
    "juntas, nunca se uma produz a outra. O dado é observacional e de um único "
    "momento: não há grupo de controle, nada foi sorteado e qualquer relação aqui "
    "pode vir de uma terceira variável não medida, ou valer no sentido inverso."
)


def _sim_nao(valor) -> str:
    return "sim" if bool(valor) else "não"


def _formata_p(valor) -> str:
    """p-valor como texto, sem escrever "0" para algo que é apenas muito pequeno."""
    if valor is None or pd.isna(valor):
        return "—"
    if valor < 1e-6:
        return "< 0,000001"
    return f"{valor:g}"


def bloco_ranking(ranking: pd.DataFrame) -> str:
    tabela = ranking.copy()
    tabela["significativo"] = tabela["significativo"].map(_sim_nao)
    tabela["concordam"] = tabela["concordam"].map(_sim_nao)
    tabela["p_ajustado"] = tabela["p_ajustado"].map(_formata_p)
    tabela = tabela[
        [
            "variavel",
            "r_pearson",
            "r_spearman",
            "p_ajustado",
            "significativo",
            "direcao",
            "forca",
            "concordam",
        ]
    ].rename(
        columns={
            "r_pearson": "r (Pearson)",
            "r_spearman": "r (Spearman)",
            "p_ajustado": "p corrigido",
            "concordam": "métodos concordam",
        }
    )

    return "\n".join(
        [
            "## 3.1 Ranking de influência",
            "",
            "Ordenado pela força da associação com a nota, do mais forte para o mais "
            "fraco. `p corrigido` já passou pela correção de Holm-Bonferroni.",
            "",
            markdown_table(tabela),
            "",
            "Leitura da coluna `força` (convenção usual, não corte desta base): "
            f"|r| >= {sa.FORCA_FORTE} forte, >= {sa.FORCA_MODERADA} moderada, "
            f">= {sa.FORCA_FRACA} fraca, abaixo disso desprezível.",
        ]
    )


def bloco_maiores_influencias(ranking: pd.DataFrame) -> str:
    significativas = ranking[ranking["significativo"]]
    positivas = significativas[significativas["direcao"] == "positiva"]
    negativas = significativas[significativas["direcao"] == "negativa"]

    partes = ["## 3.2 As variáveis de maior influência", ""]

    if not positivas.empty:
        top = positivas.iloc[0]
        partes += [
            "### Maior influência positiva",
            "",
            f"**{_cod(top['variavel'])}, r = {top['r_pearson']}** "
            f"(Spearman {top['r_spearman']}, p corrigido {_formata_p(top['p_ajustado'])}). "
            f"Associação {top['forca']} e a mais forte da base — nenhuma outra "
            "variável chega perto.",
            "",
        ]
        outras_pos = positivas.iloc[1:]
        if not outras_pos.empty:
            partes += [
                "Demais associações positivas significativas: "
                + ", ".join(
                    f"{_cod(r.variavel)} (r = {r.r_pearson}, {r.forca})"
                    for r in outras_pos.itertuples()
                )
                + ".",
                "",
            ]

    if not negativas.empty:
        top = negativas.iloc[0]
        partes += [
            "### Maior influência negativa",
            "",
            f"**{_cod(top['variavel'])}, r = {top['r_pearson']}** "
            f"(Spearman {top['r_spearman']}, p corrigido {_formata_p(top['p_ajustado'])}). "
            f"Associação {top['forca']}: quanto maior, menor a nota que acompanha.",
            "",
        ]
        outras_neg = negativas.iloc[1:]
        if not outras_neg.empty:
            partes += [
                "Demais associações negativas significativas: "
                + ", ".join(
                    f"{_cod(r.variavel)} (r = {r.r_pearson}, {r.forca})"
                    for r in outras_neg.itertuples()
                )
                + ".",
                "",
            ]

    desprezivel = significativas[significativas["forca"] == "desprezível"]
    if not desprezivel.empty:
        partes += [
            "### Significativo não quer dizer relevante",
            "",
            ", ".join(_cod(r.variavel) for r in desprezivel.itertuples())
            + " passa no teste estatístico mas tem força desprezível "
            + ", ".join(f"(r = {r.r_pearson})" for r in desprezivel.itertuples())
            + ". Com 1000 alunos, relação minúscula fica significativa; reportar "
            "isso como achado seria exagerar o que o dado diz.",
            "",
        ]

    nao_significativas = ranking[~ranking["significativo"]]
    if not nao_significativas.empty:
        partes += [
            "### Sem relação detectável com a nota",
            "",
            ", ".join(_cod(r.variavel) for r in nao_significativas.itertuples())
            + ". Nenhuma passa pelo teste depois da correção de Holm. Vale dizer o "
            "que isso **não** significa: não é prova de que não exista relação, só "
            "de que esta amostra não a mostra.",
        ]

    return "\n".join(partes).rstrip()


def bloco_concordancia(ranking: pd.DataFrame) -> str:
    discordantes = ranking[~ranking["concordam"]]
    if discordantes.empty:
        texto = (
            "Pearson e Spearman concordam em **todas** as variáveis (mesmo sinal e "
            "diferença menor que 0,1). Nenhuma relação depende de valor extremo nem "
            "esconde curva: as associações são lineares e monótonas, o que sustenta "
            "o uso de regressão linear na tarefa 4."
        )
    else:
        texto = (
            "Pearson e Spearman divergem em "
            + ", ".join(_cod(r.variavel) for r in discordantes.itertuples())
            + ". Divergência indica relação não linear ou extremo puxando o "
            "resultado — nessas variáveis a leitura linear precisa de cuidado."
        )
    return "\n".join(["## 3.3 Os dois métodos contam a mesma história?", "", texto])


def bloco_redundancia(pares: pd.DataFrame) -> str:
    partes = ["## 3.4 Redundância entre as variáveis", ""]
    if pares.empty:
        partes.append(
            "Nenhum par de preditoras passa de "
            f"|r| = {config.MULTICOLLINEARITY_THRESHOLD}."
        )
        return "\n".join(partes)

    partes += [
        "Pares que carregam quase a mesma informação "
        f"(|r| >= {config.MULTICOLLINEARITY_THRESHOLD}):",
        "",
        markdown_table(pares),
        "",
        "Isso era esperado: as duas derivadas da tarefa 2 "
        + ", ".join(_cod(c) for c in config.DERIVED_COLS)
        + " são calculadas a partir das colunas de origem, então correlacionam com "
        "elas por construção.",
        "",
        "**Consequência prática:** elas ficam **fora** do modelo da tarefa 4. Com "
        "duas variáveis quase idênticas, o coeficiente de cada uma fica instável e "
        "a leitura “quanto cada hora de estudo pesa na nota” deixa de valer. Elas "
        "continuam úteis para ler e para os gráficos, não para o modelo.",
    ]
    return "\n".join(partes)


def bloco_grupos(df: pd.DataFrame, grupos: pd.DataFrame) -> str:
    tabela = grupos.copy()
    tabela["significativo"] = tabela["significativo"].map(_sim_nao)
    tabela["p_ajustado"] = tabela["p_ajustado"].map(_formata_p)
    tabela = tabela[
        ["coluna", "n_grupos", "H", "p_ajustado", "efeito_epsilon2", "significativo"]
    ].rename(
        columns={
            "coluna": "variável",
            "n_grupos": "grupos",
            "p_ajustado": "p corrigido",
            "efeito_epsilon2": "efeito (ε²)",
        }
    )

    significativos = grupos[grupos["significativo"]]
    partes = [
        "## 3.5 A nota difere entre grupos?",
        "",
        "Teste de Kruskal-Wallis em cada coluna categórica, com p corrigido por "
        "Holm. O tamanho de efeito (ε²) está na tabela porque p pequeno em amostra "
        "grande não quer dizer diferença grande.",
        "",
        markdown_table(tabela),
        "",
    ]

    if significativos.empty:
        partes.append("Nenhuma diferença entre grupos sobrevive à correção.")
        return "\n".join(partes)

    for linha in significativos.itertuples():
        resumo = sa.group_summary(df, linha.coluna)
        partes += [
            f"### {_cod(linha.coluna)} — diferença confirmada",
            "",
            f"p corrigido {_formata_p(linha.p_ajustado)}, ε² = {linha.efeito_epsilon2} "
            f"(≈ {round(100 * linha.efeito_epsilon2, 1)}% da variação de posição na "
            "nota ligada a essa variável).",
            "",
            markdown_table(resumo),
            "",
        ]

    nao_significativos = grupos[~grupos["significativo"]]
    if not nao_significativos.empty:
        partes.append(
            "Sem diferença detectável: "
            + ", ".join(_cod(r.coluna) for r in nao_significativos.itertuples())
            + ". O caso de "
            + _cod("gender")
            + " é o mais útil de registrar, porque contraria a expectativa de que "
            "haja diferença por gênero: aqui não há."
        )

    return "\n".join(partes).rstrip()


def bloco_metodo() -> str:
    return "\n".join(
        [
            "## 3.6 Método, e por que cada escolha",
            "",
            "| Escolha | Por quê |",
            "|---|---|",
            "| Pearson **e** Spearman | Pearson mede relação linear, Spearman mede se "
            "a ordem acompanha. Concordando, a relação é sólida; divergindo, há curva "
            "ou extremo puxando — e isso precisa aparecer, não ser escondido. |",
            "| Correção de Holm-Bonferroni | São 15 variáveis testadas contra a mesma "
            "nota. A 5% por teste, esperar-se-ia quase um achado falso só por acaso. "
            "Holm é menos conservadora que Bonferroni puro e não exige que os testes "
            "sejam independentes — e aqui eles não são. |",
            "| Kruskal-Wallis para grupos | Serve para 2 ou mais grupos, não exige "
            "distribuição normal nem variância igual. Nota autodeclarada em grupos de "
            "tamanhos muito diferentes (42 alunos em `Other` contra 481 em `Female`) "
            "não cumpre essas condições. |",
            "| Tamanho de efeito junto do p | Com 1000 alunos, quase tudo fica "
            "significativo. O ε² responde “a diferença é grande?”, que é a pergunta "
            "que interessa. |",
            "| Coluna constante ignorada | Correlação com algo que não varia é "
            "indefinida; incluir devolveria um número sem sentido. |",
        ]
    )


def etapa_3_estatistica(df: pd.DataFrame) -> Path:
    ranking = sa.influence_ranking(df)
    pares = sa.multicollinearity(df)
    grupos = sa.compare_all_groups(df)

    destino = config.REPORTS_DIR / "03_estatistica.md"
    write_report(
        destino,
        "3. Análise estatística",
        [
            "Gerado por `analysis/run_analysis.py`.",
            AVISO_CAUSA,
            bloco_ranking(ranking),
            bloco_maiores_influencias(ranking),
            bloco_concordancia(ranking),
            bloco_redundancia(pares),
            bloco_grupos(df, grupos),
            bloco_metodo(),
        ],
    )
    return destino


def main() -> None:
    df = load_raw()
    print(f"Base carregada: {len(df)} linhas x {len(df.columns)} colunas")

    destino = etapa_1_exploracao(df)
    print(f"Etapa 1 (exploracao)  -> {destino.relative_to(config.PROJECT_ROOT)}")

    com_features, destino = etapa_2_engenharia(df)
    print(f"Etapa 2 (engenharia)  -> {destino.relative_to(config.PROJECT_ROOT)}")

    destino = etapa_3_estatistica(com_features)
    print(f"Etapa 3 (estatistica) -> {destino.relative_to(config.PROJECT_ROOT)}")

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    base_tratada = config.PROCESSED_DIR / "alunos_tratados.csv"
    com_features.to_csv(base_tratada, index=False, encoding="utf-8")
    print(
        f"Base tratada          -> {base_tratada.relative_to(config.PROJECT_ROOT)} "
        f"({len(com_features)} linhas x {len(com_features.columns)} colunas)"
    )


if __name__ == "__main__":
    main()
