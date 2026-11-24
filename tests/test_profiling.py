import pandas as pd

from src import profiling


def test_column_overview_conta_nulos_e_unicos(df_sujo):
    visao = profiling.column_overview(df_sujo).set_index("coluna")

    assert visao.loc["parental_education_level", "nulos"] == 2
    assert visao.loc["parental_education_level", "pct_nulos"] == 33.33
    assert visao.loc["student_id", "nulos"] == 0
    assert visao.loc["student_id", "unicos"] == 5  # S5 aparece duas vezes


def test_missing_report_lista_so_quem_tem_nulo(df_sujo):
    faltantes = profiling.missing_report(df_sujo)

    assert list(faltantes["coluna"]) == ["parental_education_level"]
    assert faltantes.iloc[0]["nulos"] == 2


def test_missing_report_vazio_quando_nao_ha_nulo():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})

    assert profiling.missing_report(df).empty


def test_duplicate_report_separa_id_repetido_de_linha_repetida(df_sujo):
    relatorio = profiling.duplicate_report(df_sujo, id_col="student_id")

    assert relatorio["ids_duplicados"] == 1
    assert relatorio["linhas_duplicadas"] == 0  # S5 repete o id, não a linha toda


def test_numeric_summary_traz_mediana_e_assimetria(df_sujo):
    resumo = profiling.numeric_summary(df_sujo, cols=["study_hours_per_day"])
    linha = resumo.loc["study_hours_per_day"]

    assert linha["contagem"] == 6
    assert linha["mediana"] == 3.5
    assert linha["maximo"] == 30.0
    assert linha["assimetria"] > 1  # o 30.0 puxa a cauda à direita


def test_categorical_summary_da_contagem_e_percentual(df_sujo):
    resumo = profiling.categorical_summary(df_sujo, cols=["gender"])
    female = resumo[resumo["valor"] == "Female"].iloc[0]

    assert female["contagem"] == 3
    assert female["pct"] == 50.0


def test_outlier_report_acha_o_valor_plantado(df_sujo):
    relatorio = profiling.outlier_report(
        df_sujo, cols=["study_hours_per_day"]
    ).set_index("coluna")

    assert relatorio.loc["study_hours_per_day", "acima"] == 1
    assert relatorio.loc["study_hours_per_day", "abaixo"] == 0


def test_range_violations_flagra_valor_impossivel(df_sujo):
    violacoes = profiling.range_violations(
        df_sujo, ranges={"study_hours_per_day": (0, 24)}
    ).set_index("coluna")

    assert violacoes.loc["study_hours_per_day", "violacoes"] == 1
    assert violacoes.loc["study_hours_per_day", "maximo_observado"] == 30.0


def test_daily_hours_check_acusa_dia_de_mais_de_24h(df_sujo):
    checagem = profiling.daily_hours_check(
        df_sujo,
        cols=["study_hours_per_day", "social_media_hours", "netflix_hours", "sleep_hours"],
    )

    assert checagem["linhas_acima_do_limite"] == 1
    assert checagem["maior_soma"] == 39.0  # 30 + 1 + 1 + 7


def test_extreme_value_concentration_mede_efeito_teto(df_sujo):
    extremos = profiling.extreme_value_concentration(df_sujo, "exam_score")

    assert extremos["valor_maximo"] == 100.0
    assert extremos["n_no_maximo"] == 1
    assert extremos["pct_no_maximo"] == 16.67
