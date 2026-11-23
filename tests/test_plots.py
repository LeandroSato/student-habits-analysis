"""Testes das figuras.

Gráfico é saída visual: o teste automático não julga se ficou legível — isso vai
para a conferência no relatório. O que dá para garantir aqui é que cada figura é
gerada, vai para o caminho pedido e não sai vazia, e que o preparo dos dados
(rótulo, ordem das faixas) está certo.
"""

import numpy as np
import pandas as pd
import pytest

from src import config, plots


@pytest.fixture
def df_figuras() -> pd.DataFrame:
    rng = np.random.default_rng(11)
    n = 120
    estudo = rng.uniform(0, 8, n)
    redes = rng.uniform(0, 7, n)
    nota = np.clip(40 + 6 * estudo - 2 * redes + rng.normal(0, 4, n), 0, 100)
    df = pd.DataFrame(
        {
            "study_hours_per_day": estudo,
            "social_media_hours": redes,
            "exam_score": nota,
        }
    )
    from src.features import add_bins

    return add_bins(df)


def test_rotulo_traduz_coluna_conhecida():
    assert plots.rotulo("study_hours_per_day") == "Horas de estudo por dia"


def test_rotulo_tem_reserva_para_coluna_desconhecida():
    assert plots.rotulo("coluna_nova") == "coluna nova"


def test_heatmap_gera_arquivo(tmp_path, df_figuras):
    matriz = df_figuras[["study_hours_per_day", "social_media_hours", "exam_score"]].corr()
    destino = plots.plot_correlation_heatmap(matriz, path=tmp_path / "calor.png")

    assert destino.exists()
    assert destino.stat().st_size > 0


def test_variavel_de_maior_impacto_gera_arquivo(tmp_path, df_figuras):
    destino = plots.plot_top_variable(
        df_figuras,
        coluna="study_hours_per_day",
        faixa="faixa_estudo",
        path=tmp_path / "impacto.png",
    )

    assert destino.exists()
    assert destino.stat().st_size > 0


def test_boxplot_por_faixa_gera_arquivo(tmp_path, df_figuras):
    destino = plots.plot_score_by_bin(
        df_figuras,
        faixa="faixa_redes_sociais",
        titulo="Nota por faixa de redes sociais",
        nome_arquivo="ignorado.png",
        path=tmp_path / "caixa.png",
    )

    assert destino.exists()
    assert destino.stat().st_size > 0


def test_distribuicao_gera_arquivo(tmp_path, df_figuras):
    destino = plots.plot_score_distribution(df_figuras, path=tmp_path / "dist.png")

    assert destino.exists()
    assert destino.stat().st_size > 0


def test_coeficientes_gera_arquivo(tmp_path):
    coefs = pd.DataFrame(
        {
            "variavel": ["study_hours_per_day", "social_media_hours"],
            "pontos_por_unidade": [9.5, -2.7],
            "pontos_por_desvio": [14.0, -3.2],
            "direcao": ["positiva", "negativa"],
        }
    )

    destino = plots.plot_model_coefficients(coefs, path=tmp_path / "coef.png")

    assert destino.exists()
    assert destino.stat().st_size > 0


def test_coeficientes_ignora_linha_sem_desvio(tmp_path):
    """Colunas de one-hot não têm desvio padrão a aplicar: ficam fora do gráfico."""
    coefs = pd.DataFrame(
        {
            "variavel": ["study_hours_per_day", "parental_education_level_Master"],
            "pontos_por_unidade": [9.5, 1.2],
            "pontos_por_desvio": [14.0, None],
            "direcao": ["positiva", "positiva"],
        }
    )

    destino = plots.plot_model_coefficients(coefs, path=tmp_path / "coef.png")

    assert destino.exists()


def test_figuras_usam_o_caminho_padrao_quando_nao_se_pede_outro(df_figuras, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "FIGURES_DIR", tmp_path / "figuras")

    destino = plots.plot_score_distribution(df_figuras)

    assert destino.parent == tmp_path / "figuras"
    assert destino.exists()
