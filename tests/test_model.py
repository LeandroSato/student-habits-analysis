import numpy as np
import pandas as pd
import pytest

from src import config, model


@pytest.fixture
def df_sintetico() -> pd.DataFrame:
    """Base com relação conhecida: a nota é construída a partir dos hábitos.

    Usar relação conhecida deixa o teste verificar o sinal e a ordem de grandeza
    dos coeficientes, não apenas que o código roda.
    """
    rng = np.random.default_rng(7)
    n = 300
    estudo = rng.uniform(0, 8, n)
    redes = rng.uniform(0, 7, n)
    nota = 40 + 6 * estudo - 2 * redes + rng.normal(0, 2, n)
    return pd.DataFrame(
        {
            "study_hours_per_day": estudo,
            "social_media_hours": redes,
            "exam_score": np.clip(nota, 0, 100),
        }
    )


FEATURES = ["study_hours_per_day", "social_media_hours"]


def test_train_devolve_metricas_de_holdout(df_sintetico):
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])

    assert 0 < ajustado.metrics["r2"] <= 1
    assert ajustado.metrics["mae"] > 0
    assert ajustado.metrics["rmse"] >= ajustado.metrics["mae"]
    assert ajustado.metrics["n_treino"] + ajustado.metrics["n_teste"] == len(df_sintetico)


def test_train_bate_a_previsao_pela_media(df_sintetico):
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])

    # O modelo tem de errar menos que simplesmente chutar a nota média.
    assert ajustado.metrics["mae"] < ajustado.metrics["mae_baseline"]


def test_coefficient_table_acha_o_sinal_e_a_escala_certos(df_sintetico):
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])
    coefs = model.coefficient_table(ajustado).set_index("variavel")

    assert 5 < coefs.loc["study_hours_per_day", "pontos_por_unidade"] < 7
    assert -3 < coefs.loc["social_media_hours", "pontos_por_unidade"] < -1


def test_coefficient_table_traz_o_efeito_padronizado(df_sintetico):
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])
    coefs = model.coefficient_table(ajustado).set_index("variavel")

    # Estudo varia mais e pesa mais: o efeito padronizado tem de ser o maior.
    assert abs(coefs.loc["study_hours_per_day", "pontos_por_desvio"]) > abs(
        coefs.loc["social_media_hours", "pontos_por_desvio"]
    )


def test_coefficient_table_vem_ordenada_pela_forca(df_sintetico):
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])
    coefs = model.coefficient_table(ajustado)

    forcas = coefs["pontos_por_desvio"].abs().tolist()
    assert forcas == sorted(forcas, reverse=True)


def test_predict_respeita_os_limites_da_nota(df_sintetico):
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])

    # Hábitos muito acima de qualquer aluno da base: sem truncar, passaria de 100.
    alto = model.predict(ajustado, {"study_hours_per_day": 24, "social_media_hours": 0})
    baixo = model.predict(ajustado, {"study_hours_per_day": 0, "social_media_hours": 24})

    minimo, maximo = config.SCORE_LIMITS
    assert alto[0] == maximo
    assert minimo <= baixo[0] <= maximo


def test_predict_aceita_dicionario_e_dataframe(df_sintetico):
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])
    cenario = {"study_hours_per_day": 4.0, "social_media_hours": 2.0}

    de_dict = model.predict(ajustado, cenario)
    de_df = model.predict(ajustado, pd.DataFrame([cenario]))

    assert de_dict[0] == pytest.approx(de_df[0])


def test_predict_reclama_de_variavel_faltando(df_sintetico):
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])

    with pytest.raises(ValueError) as erro:
        model.predict(ajustado, {"study_hours_per_day": 4.0})

    assert "social_media_hours" in str(erro.value)


def test_train_e_reprodutivel(df_sintetico):
    primeiro = model.train(df_sintetico, numeric=FEATURES, categorical=[])
    segundo = model.train(df_sintetico, numeric=FEATURES, categorical=[])

    assert primeiro.metrics["r2"] == segundo.metrics["r2"]


def test_cross_val_r2_roda_todas_as_dobras(df_sintetico):
    resultado = model.cross_val_r2(df_sintetico, numeric=FEATURES, categorical=[])

    assert resultado["dobras"] == config.CV_FOLDS
    assert len(resultado["r2_por_dobra"]) == config.CV_FOLDS
    assert resultado["r2_desvio"] >= 0


def test_compare_models_devolve_uma_linha_por_conjunto(df_sintetico):
    comparacao = model.compare_models(
        df_sintetico,
        conjuntos={
            "completo": (FEATURES, []),
            "so_estudo": (["study_hours_per_day"], []),
        },
    )

    assert list(comparacao["conjunto"]) == ["completo", "so_estudo"]
    assert comparacao.iloc[0]["r2"] > comparacao.iloc[1]["r2"]


def test_scenario_delta_mostra_o_efeito_de_mudar_um_habito(df_sintetico):
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])
    base = {"study_hours_per_day": 3.0, "social_media_hours": 3.0}

    efeito = model.scenario_delta(ajustado, base, {"study_hours_per_day": 4.0})

    assert efeito["nota_antes"] < efeito["nota_depois"]
    assert efeito["diferenca"] == pytest.approx(
        efeito["nota_depois"] - efeito["nota_antes"]
    )


def test_train_funciona_com_variavel_categorica():
    rng = np.random.default_rng(3)
    n = 200
    estudo = rng.uniform(0, 8, n)
    grupo = rng.choice(["Master", "Bachelor", "Não informado"], n)
    df = pd.DataFrame(
        {
            "study_hours_per_day": estudo,
            "parental_education_level": grupo,
            "exam_score": np.clip(40 + 6 * estudo + rng.normal(0, 3, n), 0, 100),
        }
    )

    ajustado = model.train(
        df, numeric=["study_hours_per_day"], categorical=["parental_education_level"]
    )
    coefs = model.coefficient_table(ajustado)

    assert ajustado.metrics["r2"] > 0.5
    # One-hot com categoria de referência: 3 categorias geram 2 colunas.
    assert len(coefs) == 3


def test_intercept_e_a_nota_prevista_com_tudo_em_zero(df_sintetico):
    """O intercepto não tem leitura prática, mas entra na conta da previsão."""
    ajustado = model.train(df_sintetico, numeric=FEATURES, categorical=[])

    zerado = {coluna: 0.0 for coluna in FEATURES}
    previsto_do_zero = float(model.predict(ajustado, zerado)[0])

    minimo, maximo = config.SCORE_LIMITS
    esperado = min(max(model.intercept(ajustado), minimo), maximo)
    assert previsto_do_zero == pytest.approx(esperado, abs=0.01)
