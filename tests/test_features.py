import pandas as pd

from src import config
from src.features import (
    add_bins,
    add_derived_hours,
    build_features,
    encode_binaries,
    encode_ordinals,
)


def test_add_bins_cria_uma_coluna_por_faixa(df_valido):
    com_faixas = add_bins(df_valido)

    for nome in config.BIN_SPECS:
        assert nome in com_faixas.columns


def test_add_bins_nao_deixa_aluno_fora_de_faixa(df_valido):
    com_faixas = add_bins(df_valido)

    for nome in config.BIN_SPECS:
        assert com_faixas[nome].isna().sum() == 0


def test_add_bins_coloca_valor_no_corte_na_faixa_de_cima():
    df = pd.DataFrame({"social_media_hours": [0.0, 0.9, 1.0, 2.0, 4.0, 7.2]})

    faixas = add_bins(df, specs={"faixa_redes_sociais": config.BIN_SPECS["faixa_redes_sociais"]})

    assert faixas["faixa_redes_sociais"].astype(str).tolist() == [
        "Até 1h",
        "Até 1h",
        "1 a 2h",
        "2 a 3h",
        "4h ou mais",
        "4h ou mais",
    ]


def test_add_bins_ignora_faixa_cuja_coluna_nao_existe():
    df = pd.DataFrame({"social_media_hours": [1.0]})

    faixas = add_bins(df)

    assert "faixa_redes_sociais" in faixas.columns
    assert "faixa_estudo" not in faixas.columns


def test_add_derived_hours_soma_tela_de_lazer():
    df = pd.DataFrame(
        {
            "social_media_hours": [2.0, 1.0],
            "netflix_hours": [1.0, 0.5],
            "study_hours_per_day": [3.0, 1.5],
        }
    )

    derivadas = add_derived_hours(df)

    assert derivadas["leisure_screen_hours"].tolist() == [3.0, 1.5]
    assert derivadas["study_share"].tolist() == [0.5, 0.5]


def test_add_derived_hours_deixa_study_share_nulo_quando_nao_ha_tempo_medido():
    df = pd.DataFrame(
        {
            "social_media_hours": [0.0],
            "netflix_hours": [0.0],
            "study_hours_per_day": [0.0],
        }
    )

    derivadas = add_derived_hours(df)

    assert derivadas["study_share"].isna().all()


def test_encode_ordinals_respeita_a_ordem_das_escalas(df_valido):
    codificado = encode_ordinals(df_valido)

    assert codificado["diet_quality_ord"].tolist() == [2, 1, 0, 2, 1]
    assert codificado["internet_quality_ord"].tolist() == [2, 1, 0, 2, 2]


def test_encode_ordinals_nao_cria_escala_para_escolaridade_dos_pais(df_valido):
    codificado = encode_ordinals(df_valido)

    assert "parental_education_level_ord" not in codificado.columns


def test_encode_binaries_mapeia_sim_e_nao(df_valido):
    codificado = encode_binaries(df_valido)

    assert codificado["part_time_job_bin"].tolist() == [0, 1, 0, 0, 0]
    assert codificado["extracurricular_participation_bin"].tolist() == [1, 0, 0, 1, 0]


def test_build_features_preserva_as_linhas_e_as_colunas_originais(df_valido):
    completo = build_features(df_valido)

    assert len(completo) == len(df_valido)
    for coluna in df_valido.columns:
        assert coluna in completo.columns


def test_build_features_entrega_todas_as_derivadas(df_valido):
    completo = build_features(df_valido)

    esperadas = (
        list(config.BIN_SPECS)
        + ["leisure_screen_hours", "study_share"]
        + [c + config.ORDINAL_SUFFIX for c in config.ORDINAL_MAPS]
        + [c + config.BINARY_SUFFIX for c in config.BINARY_MAPS]
    )
    for coluna in esperadas:
        assert coluna in completo.columns


def test_derived_columns_lista_so_as_derivadas_que_existem(df_valido):
    """Sem esta cobertura a função só era exercitada pelo script de análise."""
    from src.features import derived_columns

    completo = build_features(df_valido)
    derivadas = derived_columns(completo)

    assert "faixa_estudo" in derivadas
    assert "leisure_screen_hours" in derivadas
    assert config.TARGET not in derivadas
    assert "study_hours_per_day" not in derivadas  # original não é derivada


def test_derived_columns_devolve_vazio_em_base_sem_derivadas():
    import pandas as pd

    from src.features import derived_columns

    assert derived_columns(pd.DataFrame({"study_hours_per_day": [1.0]})) == []
