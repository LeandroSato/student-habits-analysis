"""Fixtures compartilhadas.

Os testes usam um DataFrame pequeno e escrito à mão, com defeitos plantados de
propósito (nulo, duplicata, valor impossível, outlier). Assim cada função de
tratamento é verificada contra um resultado que se confere no olho, sem
depender do CSV do desafio.
"""

import pandas as pd
import pytest


@pytest.fixture
def df_sujo() -> pd.DataFrame:
    """6 linhas com: 1 id repetido, 2 nulos, 1 hora impossível, 1 outlier."""
    return pd.DataFrame(
        {
            "student_id": ["S1", "S2", "S3", "S4", "S5", "S5"],
            "age": [20, 21, 19, 22, 20, 20],
            "gender": ["Female", "Male", "Male", "Other", "Female", "Female"],
            "study_hours_per_day": [2.0, 3.0, 4.0, 5.0, 30.0, 2.0],
            "social_media_hours": [1.0, 2.0, 1.5, 2.5, 1.0, 1.0],
            "netflix_hours": [1.0, 1.0, 2.0, 1.0, 1.0, 1.0],
            "sleep_hours": [7.0, 8.0, 6.0, 7.0, 7.0, 7.0],
            "attendance_percentage": [90.0, 80.0, 70.0, 95.0, 85.0, 85.0],
            "diet_quality": ["Good", "Fair", "Poor", "Good", "Fair", "Fair"],
            "exercise_frequency": [3, 2, 0, 5, 3, 3],
            "parental_education_level": ["Master", None, "Bachelor", None, "Master", "Master"],
            "internet_quality": ["Good", "Average", "Poor", "Good", "Good", "Good"],
            "mental_health_rating": [8, 5, 3, 9, 7, 7],
            "part_time_job": ["No", "Yes", "No", "No", "No", "No"],
            "extracurricular_participation": ["Yes", "No", "No", "Yes", "No", "No"],
            "exam_score": [70.0, 65.0, 50.0, 100.0, 80.0, 80.0],
        }
    )


@pytest.fixture
def df_valido(df_sujo) -> pd.DataFrame:
    """Mesma base pequena, mas sem o valor impossível e sem a linha repetida.

    Serve para os testes de engenharia de dados, que pressupõem base já limpa.
    """
    df = df_sujo.copy()
    df.loc[4, "study_hours_per_day"] = 6.0
    return df.iloc[:5].reset_index(drop=True)
