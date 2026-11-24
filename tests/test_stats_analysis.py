import numpy as np
import pandas as pd

from src import stats_analysis as sa


# --- Correção para múltiplos testes -----------------------------------------


def test_holm_adjust_corrige_e_mantem_ordem_crescente():
    # Holm: p ordenado, cada um multiplicado por (m - posição), e o resultado
    # nunca pode diminuir ao longo da lista.
    ajustados = sa.holm_adjust([0.01, 0.02, 0.03])

    assert ajustados == [0.03, 0.04, 0.04]


def test_holm_adjust_nao_passa_de_um():
    ajustados = sa.holm_adjust([0.5, 0.6])

    assert all(p <= 1.0 for p in ajustados)


def test_holm_adjust_respeita_a_ordem_de_entrada():
    # O menor p é o terceiro da lista; o ajuste tem de voltar na mesma posição.
    ajustados = sa.holm_adjust([0.03, 0.02, 0.01])

    assert ajustados == [0.04, 0.04, 0.03]


def test_holm_adjust_aceita_lista_vazia():
    assert sa.holm_adjust([]) == []


# --- Correlação com o alvo ---------------------------------------------------


def _df_relacao() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, 200)
    ruido = rng.normal(0, 0.5, 200)
    return pd.DataFrame(
        {
            "sobe_com_a_nota": x,
            "desce_com_a_nota": -x,
            "nada_a_ver": rng.uniform(0, 10, 200),
            "nota": 5 * x + ruido,
        }
    )


def test_correlation_with_target_acha_o_sinal_de_cada_relacao():
    corr = sa.correlation_with_target(
        _df_relacao(),
        cols=["sobe_com_a_nota", "desce_com_a_nota", "nada_a_ver"],
        target="nota",
    ).set_index("variavel")

    assert corr.loc["sobe_com_a_nota", "r"] > 0.9
    assert corr.loc["desce_com_a_nota", "r"] < -0.9
    assert abs(corr.loc["nada_a_ver", "r"]) < 0.3


def test_correlation_with_target_marca_o_que_e_significativo():
    corr = sa.correlation_with_target(
        _df_relacao(),
        cols=["sobe_com_a_nota", "nada_a_ver"],
        target="nota",
    ).set_index("variavel")

    assert bool(corr.loc["sobe_com_a_nota", "significativo"]) is True
    assert bool(corr.loc["nada_a_ver", "significativo"]) is False


def test_correlation_with_target_usa_spearman_quando_pedido():
    corr = sa.correlation_with_target(
        _df_relacao(),
        cols=["sobe_com_a_nota"],
        target="nota",
        method="spearman",
    )

    assert corr.iloc[0]["metodo"] == "spearman"
    assert corr.iloc[0]["r"] > 0.9


def test_correlation_with_target_ignora_coluna_constante():
    df = pd.DataFrame({"sempre_igual": [1] * 10, "nota": range(10)})

    corr = sa.correlation_with_target(df, cols=["sempre_igual"], target="nota")

    assert corr.empty


# --- Ranking de influência ---------------------------------------------------


def test_influence_ranking_ordena_por_forca_e_nomeia_a_direcao():
    ranking = sa.influence_ranking(
        _df_relacao(),
        cols=["nada_a_ver", "desce_com_a_nota", "sobe_com_a_nota"],
        target="nota",
    )

    assert ranking.iloc[0]["variavel"] in {"sobe_com_a_nota", "desce_com_a_nota"}
    assert ranking.iloc[-1]["variavel"] == "nada_a_ver"
    direcoes = dict(zip(ranking["variavel"], ranking["direcao"]))
    assert direcoes["sobe_com_a_nota"] == "positiva"
    assert direcoes["desce_com_a_nota"] == "negativa"


def test_influence_ranking_traz_pearson_e_spearman_lado_a_lado():
    ranking = sa.influence_ranking(
        _df_relacao(), cols=["sobe_com_a_nota"], target="nota"
    )

    assert "r_pearson" in ranking.columns
    assert "r_spearman" in ranking.columns


# --- Matriz de correlação ----------------------------------------------------


def test_correlation_matrix_e_quadrada_e_tem_um_na_diagonal():
    matriz = sa.correlation_matrix(
        _df_relacao(), cols=["sobe_com_a_nota", "nada_a_ver", "nota"]
    )

    assert matriz.shape == (3, 3)
    assert all(abs(matriz.loc[c, c] - 1.0) < 1e-9 for c in matriz.columns)


# --- Redundância entre preditoras -------------------------------------------


def test_multicollinearity_flagra_par_redundante():
    df = pd.DataFrame(
        {
            "a": [1.0, 2, 3, 4, 5],
            "copia_de_a": [2.0, 4, 6, 8, 10],
            "independente": [5.0, 1, 4, 2, 3],
        }
    )

    pares = sa.multicollinearity(df, cols=["a", "copia_de_a", "independente"], threshold=0.7)

    assert len(pares) == 1
    assert set(pares.iloc[0][["variavel_a", "variavel_b"]]) == {"a", "copia_de_a"}


def test_multicollinearity_vazio_quando_nada_e_redundante():
    df = pd.DataFrame({"a": [1.0, 2, 3, 4], "b": [4.0, 1, 3, 2]})

    assert sa.multicollinearity(df, cols=["a", "b"], threshold=0.9).empty


# --- Comparação entre grupos -------------------------------------------------


def test_compare_groups_acusa_diferenca_real():
    df = pd.DataFrame(
        {
            "grupo": ["A"] * 15 + ["B"] * 15,
            "nota": list(range(40, 55)) + list(range(80, 95)),
        }
    )

    resultado = sa.compare_groups(df, "grupo", "nota")

    assert resultado["p_valor"] < 0.05
    assert resultado["n_grupos"] == 2
    assert resultado["efeito_epsilon2"] > 0.5


def test_compare_groups_nao_acusa_diferenca_onde_nao_ha():
    df = pd.DataFrame(
        {
            "grupo": ["A", "B"] * 15,
            "nota": list(range(60, 90)),
        }
    )

    resultado = sa.compare_groups(df, "grupo", "nota")

    assert resultado["p_valor"] > 0.05


def test_compare_groups_devolve_resumo_por_grupo():
    df = pd.DataFrame(
        {
            "grupo": ["A"] * 10 + ["B"] * 10,
            "nota": list(range(50, 60)) + list(range(70, 80)),
        }
    )

    resumo = sa.group_summary(df, "grupo", "nota")

    assert list(resumo["grupo"]) == ["A", "B"]
    assert resumo.iloc[0]["alunos"] == 10
    assert resumo.iloc[0]["media"] < resumo.iloc[1]["media"]


# --- Comparação em lote -------------------------------------------------------


def test_compare_all_groups_corrige_os_p_valores_em_conjunto():
    """Várias colunas de uma vez: os p-valores têm de passar por Holm juntos."""
    df = pd.DataFrame(
        {
            "separa": ["A"] * 15 + ["B"] * 15,
            "nao_separa": ["X", "Y"] * 15,
            "nota": list(range(40, 55)) + list(range(80, 95)),
        }
    )

    resultado = sa.compare_all_groups(
        df, group_cols=["separa", "nao_separa"], target="nota"
    )

    assert len(resultado) == 2
    # Vem ordenado do mais significativo para o menos.
    assert resultado.iloc[0]["coluna"] == "separa"
    assert bool(resultado.iloc[0]["significativo"]) is True
    assert bool(resultado.iloc[1]["significativo"]) is False
    assert (resultado["p_ajustado"] >= resultado["p_valor"]).all()


def test_compare_all_groups_ignora_coluna_que_nao_existe():
    df = pd.DataFrame({"grupo": ["A", "B"] * 10, "nota": list(range(20))})

    resultado = sa.compare_all_groups(
        df, group_cols=["grupo", "coluna_inexistente"], target="nota"
    )

    assert list(resultado["coluna"]) == ["grupo"]
