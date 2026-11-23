import pandas as pd
import pytest

from src import config
from src.data_loading import (
    MissingColumnsError,
    categorical_columns,
    load_raw,
    numeric_columns,
)


def test_load_raw_le_o_csv_do_desafio():
    df = load_raw()
    assert len(df) == 1000
    assert list(df.columns) == config.EXPECTED_COLUMNS


def test_load_raw_reclama_de_csv_sem_as_colunas_esperadas(tmp_path):
    csv = tmp_path / "quebrado.csv"
    pd.DataFrame({"student_id": ["S1"], "age": [20]}).to_csv(csv, index=False)

    with pytest.raises(MissingColumnsError) as erro:
        load_raw(csv)

    assert "exam_score" in str(erro.value)


def test_load_raw_reclama_de_arquivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_raw(tmp_path / "nao_existe.csv")


def test_numeric_columns_ignora_texto_e_respeita_exclude(df_sujo):
    cols = numeric_columns(df_sujo, exclude=[config.TARGET])

    assert "study_hours_per_day" in cols
    assert "gender" not in cols
    assert config.TARGET not in cols


def test_categorical_columns_pega_texto_mesmo_no_pandas_3(df_sujo):
    cols = categorical_columns(df_sujo, exclude=[config.ID_COL])

    assert "gender" in cols
    assert "diet_quality" in cols
    assert config.ID_COL not in cols
    assert "age" not in cols
