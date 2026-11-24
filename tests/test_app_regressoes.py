"""Regressões achadas na passada de avaliação com Playwright.

Dois defeitos que só aparecem usando o app, e que viram teste para não voltarem:

1. O passo do controle de frequência era 0,5, e a mediana da base é 84,4 — o
   controle não conseguia representar o próprio valor que ele abre. Ao mexer em
   qualquer coisa, ele pulava para 84,5 e o "aluno mediano" deixava de ser o
   mediano.
2. O rótulo do maior valor do gráfico de barras saía cortado na borda em tela
   estreita, porque a folga do eixo é em unidades de dado e o rótulo é em pixels.
"""

import pandas as pd

from src import cleaning, config, features
from src.data_loading import load_raw


def _base() -> pd.DataFrame:
    tratado, _ = cleaning.clean(load_raw())
    return features.build_features(tratado)


def test_todo_controle_consegue_representar_a_propria_mediana():
    """O valor em que o slider abre tem de cair na grade do passo dele."""
    base = _base()

    fora_da_grade = []
    for coluna, passo in config.FEATURE_STEPS.items():
        mediana = float(base[coluna].median())
        minimo = float(base[coluna].min())
        # Quantos passos da mediana até o mínimo: tem de dar um número inteiro.
        passos = (mediana - minimo) / passo
        if abs(passos - round(passos)) > 1e-9:
            fora_da_grade.append((coluna, mediana, passo))

    assert not fora_da_grade, (
        "Estes controles não conseguem mostrar a própria mediana: " + str(fora_da_grade)
    )


def test_folga_do_eixo_cabe_o_rotulo_em_tela_estreita():
    """A maior barra não pode passar de 80% da largura útil do gráfico.

    Acima disso o rótulo ao lado dela não cabe numa tela de 390px — foi assim
    que o "+9.54" apareceu cortado. O teste lê a folga que o app usa de verdade,
    para quebrar se alguém reduzir o valor sem conferir na tela estreita.
    """
    maior_barra_em_fracao_do_eixo = 1 / config.CHART_HEADROOM

    assert maior_barra_em_fracao_do_eixo <= 0.80
