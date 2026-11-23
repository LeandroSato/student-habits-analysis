import pandas as pd
import pytest

from src import config
from src.cleaning import (
    DomainViolationError,
    assert_within_domain,
    clean,
    missing_as_category,
    remove_exact_duplicates,
)


def test_remove_exact_duplicates_apaga_linha_repetida():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})

    limpo, removidas = remove_exact_duplicates(df)

    assert removidas == 1
    assert len(limpo) == 2


def test_remove_exact_duplicates_nao_mexe_em_base_sem_repeticao(df_valido):
    limpo, removidas = remove_exact_duplicates(df_valido)

    assert removidas == 0
    assert len(limpo) == len(df_valido)


def test_assert_within_domain_passa_em_base_plausivel(df_valido):
    assert_within_domain(df_valido)  # não deve levantar nada


def test_assert_within_domain_levanta_erro_em_valor_impossivel(df_sujo):
    with pytest.raises(DomainViolationError) as erro:
        assert_within_domain(df_sujo)

    assert "study_hours_per_day" in str(erro.value)


def test_missing_as_category_troca_nulo_por_rotulo_e_cria_flag(df_valido):
    tratado = missing_as_category(df_valido)
    coluna = "parental_education_level"
    flag = coluna + config.MISSING_FLAG_SUFFIX

    assert tratado[coluna].isna().sum() == 0
    assert (tratado[coluna] == config.MISSING_LABEL).sum() == 2
    assert tratado[flag].tolist() == [1, 0, 1, 0, 1]


def test_missing_as_category_nao_altera_o_dataframe_original(df_valido):
    antes = df_valido["parental_education_level"].isna().sum()

    missing_as_category(df_valido)

    assert df_valido["parental_education_level"].isna().sum() == antes


def test_clean_junta_os_passos_e_devolve_o_log(df_valido):
    limpo, log = clean(df_valido)

    assert log["linhas_entrada"] == 5
    assert log["linhas_saida"] == 5
    assert log["duplicatas_removidas"] == 0
    assert log["nulos_restantes"] == 0
    assert limpo["parental_education_level"].isna().sum() == 0


def test_clean_para_tudo_se_aparecer_valor_impossivel(df_sujo):
    with pytest.raises(DomainViolationError):
        clean(df_sujo)
