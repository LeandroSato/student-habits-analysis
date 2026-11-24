"""Testes do app Streamlit.

Existem por causa de um bug real: o botão "Voltar ao aluno mediano" escrevia na
chave dos sliders **depois** que eles já tinham sido criados na mesma execução,
e o Streamlit levanta `StreamlitWidgetAlreadyInstantiatedError` nesse caso. O
erro só aparecia ao clicar, e a conferência no navegador não chegou a clicar.

Regra do projeto: bug que escapou vira teste, para não precisar testar na mão de
novo. Aqui não se testa aparência — só que o app sobe e que interagir com ele
não quebra.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"

# O app treina o modelo ao abrir; 60s dá folga para a primeira execução.
TIMEOUT = 60


@pytest.fixture(scope="module")
def app() -> AppTest:
    teste = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
    teste.run()
    return teste


def test_app_sobe_sem_erro(app):
    assert not app.exception
    assert any("Simulador" in t.value for t in app.title)


def test_app_mostra_os_sete_controles(app):
    assert len(app.sidebar.slider) == 7


def test_botao_de_voltar_ao_mediano_nao_quebra():
    """O bug que originou este arquivo."""
    teste = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
    teste.run()

    teste.sidebar.slider(key="slider_study_hours_per_day").set_value(7.0).run()
    assert not teste.exception

    teste.sidebar.button[0].click().run()

    assert not teste.exception


def test_botao_de_voltar_repoe_a_mediana():
    teste = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
    teste.run()

    chave = "slider_study_hours_per_day"
    mediana = teste.sidebar.slider(key=chave).value

    teste.sidebar.slider(key=chave).set_value(7.0).run()
    assert teste.sidebar.slider(key=chave).value == 7.0

    teste.sidebar.button[0].click().run()

    assert teste.sidebar.slider(key=chave).value == mediana


def test_mexer_no_estudo_muda_a_nota_prevista():
    """A previsão tem de responder ao controle, não ficar parada."""
    teste = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
    teste.run()

    antes = teste.metric[0].value
    teste.sidebar.slider(key="slider_study_hours_per_day").set_value(7.0).run()
    depois = teste.metric[0].value

    assert not teste.exception
    assert float(antes) < float(depois)


def test_previsao_nao_passa_do_teto():
    """Hábitos no extremo: a nota prevista trava em 100, não estoura."""
    teste = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
    teste.run()

    teste.sidebar.slider(key="slider_study_hours_per_day").set_value(8.3).run()
    teste.sidebar.slider(key="slider_social_media_hours").set_value(0.0).run()
    teste.sidebar.slider(key="slider_netflix_hours").set_value(0.0).run()
    teste.sidebar.slider(key="slider_mental_health_rating").set_value(10.0).run()

    assert not teste.exception
    assert float(teste.metric[0].value) <= 100.0
