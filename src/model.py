"""Regressão linear para prever a nota a partir dos hábitos (tarefa 4).

Decisões que moldam este módulo, todas a favor da interpretabilidade:

- **Regressão linear (OLS), não árvore nem boosting.** O que o simulador precisa
  responder é "o que acontece com a nota se eu estudar uma hora a mais", e um
  coeficiente responde isso em uma frase. Um modelo mais forte ganharia alguns
  pontos de R² e perderia a frase — que é justamente o produto.
- **Sem padronizar dentro do pipeline.** Regressão linear não precisa de escala,
  e sem ela o coeficiente já sai na unidade que interessa: pontos de nota por
  hora. O efeito padronizado é calculado à parte, para comparar importância.
- **Previsão truncada em [0, 100].** A tarefa 1 achou efeito teto (48 alunos em
  100). Sem truncar, o modelo devolveria nota 104 para um aluno dedicado, o que
  não existe.
- **Modelo treinado na hora, não salvo em arquivo.** São 1000 linhas: treinar
  leva milissegundos. Guardar um `.pkl` no repositório criaria um artefato
  binário que envelhece em silêncio quando o tratamento muda.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src import config


@dataclass
class FittedModel:
    """Modelo treinado, com o que é preciso para explicá-lo e usá-lo."""

    pipeline: Pipeline
    numeric: list[str]
    categorical: list[str]
    target: str
    metrics: dict
    desvios: dict = field(default_factory=dict)

    @property
    def features(self) -> list[str]:
        return list(self.numeric) + list(self.categorical)


def build_pipeline(numeric: list[str], categorical: list[str]) -> Pipeline:
    """Monta o pipeline: one-hot nas categóricas, nada nas numéricas.

    `drop="first"` deixa uma categoria como referência, senão as colunas somam
    sempre 1 e o modelo fica indeterminado.
    """
    transformadores = [("num", "passthrough", numeric)]
    if categorical:
        transformadores.append(
            (
                "cat",
                OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False),
                categorical,
            )
        )
    return Pipeline(
        [
            ("preparo", ColumnTransformer(transformadores)),
            ("regressao", LinearRegression()),
        ]
    )


def train(
    df: pd.DataFrame,
    numeric: list[str] | None = None,
    categorical: list[str] | None = None,
    target: str = config.TARGET,
    test_size: float = config.TEST_SIZE,
    random_state: int = config.RANDOM_STATE,
) -> FittedModel:
    """Treina em 80% e mede em 20% que o modelo nunca viu.

    O baseline (prever sempre a nota média) vai junto nas métricas: sem ele, um
    R² solto não diz se o modelo está fazendo algo melhor que o óbvio.
    """
    numeric = list(numeric if numeric is not None else config.MODEL_NUMERIC_REDUCED)
    categorical = list(
        categorical if categorical is not None else config.MODEL_CATEGORICAL_REDUCED
    )
    features = numeric + categorical

    dados = df[features + [target]].dropna()
    X, y = dados[features], dados[target]

    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    pipeline = build_pipeline(numeric, categorical)
    pipeline.fit(X_treino, y_treino)

    previsto = _clip(pipeline.predict(X_teste))
    media_treino = float(y_treino.mean())
    baseline = np.full(len(y_teste), media_treino)

    metrics = {
        "r2": round(float(r2_score(y_teste, previsto)), 4),
        "mae": round(float(mean_absolute_error(y_teste, previsto)), 2),
        "rmse": round(float(root_mean_squared_error(y_teste, previsto)), 2),
        "mae_baseline": round(float(mean_absolute_error(y_teste, baseline)), 2),
        "r2_treino": round(float(r2_score(y_treino, _clip(pipeline.predict(X_treino)))), 4),
        "n_treino": int(len(X_treino)),
        "n_teste": int(len(X_teste)),
        "nota_media_treino": round(media_treino, 2),
    }

    desvios = {coluna: float(X[coluna].std()) for coluna in numeric}

    return FittedModel(
        pipeline=pipeline,
        numeric=numeric,
        categorical=categorical,
        target=target,
        metrics=metrics,
        desvios=desvios,
    )


def _clip(valores: np.ndarray) -> np.ndarray:
    minimo, maximo = config.SCORE_LIMITS
    return np.clip(valores, minimo, maximo)


def _nomes_das_colunas(fitted: FittedModel) -> list[str]:
    preparo: ColumnTransformer = fitted.pipeline.named_steps["preparo"]
    nomes = list(fitted.numeric)
    if fitted.categorical:
        codificador: OneHotEncoder = preparo.named_transformers_["cat"]
        nomes += list(codificador.get_feature_names_out(fitted.categorical))
    return nomes


def coefficient_table(fitted: FittedModel) -> pd.DataFrame:
    """Coeficientes em duas unidades, porque respondem perguntas diferentes.

    - `pontos_por_unidade`: quanto a nota muda por uma unidade da variável
      (uma hora, um ponto percentual). É o número que o simulador usa.
    - `pontos_por_desvio`: quanto a nota muda por um desvio padrão da variável.
      É o número que permite comparar importância entre variáveis de unidades
      diferentes — hora de estudo e ponto de frequência não se comparam direto.

    Para as colunas de one-hot, `pontos_por_unidade` é a diferença em relação à
    categoria de referência, e não há desvio padrão a aplicar.
    """
    regressao: LinearRegression = fitted.pipeline.named_steps["regressao"]
    nomes = _nomes_das_colunas(fitted)

    linhas = []
    for nome, coef in zip(nomes, regressao.coef_):
        desvio = fitted.desvios.get(nome)
        linhas.append(
            {
                "variavel": nome,
                "pontos_por_unidade": round(float(coef), 3),
                "pontos_por_desvio": (
                    round(float(coef) * desvio, 3) if desvio is not None else None
                ),
                "direcao": "positiva" if coef > 0 else ("negativa" if coef < 0 else "nula"),
            }
        )

    tabela = pd.DataFrame(linhas)
    tabela["ordem"] = (
        tabela["pontos_por_desvio"].abs().fillna(tabela["pontos_por_unidade"].abs())
    )
    tabela = tabela.sort_values("ordem", ascending=False).drop(columns="ordem")
    return tabela.reset_index(drop=True)


def intercept(fitted: FittedModel) -> float:
    """Nota prevista quando todas as variáveis valem zero.

    Não tem leitura prática (ninguém dorme 0 hora e tem 0% de frequência), mas
    entra na conta do simulador e aparece na equação.
    """
    return round(float(fitted.pipeline.named_steps["regressao"].intercept_), 3)


def predict(fitted: FittedModel, dados: dict | pd.DataFrame) -> np.ndarray:
    """Prevê a nota, truncando no intervalo que existe.

    Aceita dicionário (um cenário do simulador) ou DataFrame (vários alunos).
    """
    if isinstance(dados, dict):
        dados = pd.DataFrame([dados])

    faltando = [c for c in fitted.features if c not in dados.columns]
    if faltando:
        raise ValueError(
            "Faltam variáveis para a previsão: " + ", ".join(faltando)
        )

    return _clip(fitted.pipeline.predict(dados[fitted.features]))


def scenario_delta(
    fitted: FittedModel, base: dict, mudancas: dict
) -> dict:
    """Compara dois cenários: o atual e o atual com alguns hábitos trocados.

    É a operação do simulador. Devolve as duas notas e a diferença — mas a
    diferença é "o que o modelo prevê para um aluno com esses hábitos", não "o
    que acontece se este aluno mudar". A distinção está escrita na interface.
    """
    cenario = {**base, **mudancas}
    # As três são arredondadas de forma consistente: a interface mostra as duas
    # notas e a diferença, e a subtração que o leitor faz na tela tem de fechar.
    antes = round(float(predict(fitted, base)[0]), 2)
    depois = round(float(predict(fitted, cenario)[0]), 2)
    return {
        "nota_antes": antes,
        "nota_depois": depois,
        "diferenca": round(depois - antes, 2),
        "mudancas": mudancas,
    }


def cross_val_r2(
    df: pd.DataFrame,
    numeric: list[str] | None = None,
    categorical: list[str] | None = None,
    target: str = config.TARGET,
    folds: int = config.CV_FOLDS,
    random_state: int = config.RANDOM_STATE,
) -> dict:
    """R² em validação cruzada, para saber se o resultado do holdout foi sorte.

    Um desvio alto entre as dobras significaria que o modelo depende de qual
    pedaço da base caiu no treino.
    """
    numeric = list(numeric if numeric is not None else config.MODEL_NUMERIC_REDUCED)
    categorical = list(
        categorical if categorical is not None else config.MODEL_CATEGORICAL_REDUCED
    )
    features = numeric + categorical

    dados = df[features + [target]].dropna()
    pipeline = build_pipeline(numeric, categorical)
    divisao = KFold(n_splits=folds, shuffle=True, random_state=random_state)
    scores = cross_val_score(pipeline, dados[features], dados[target], cv=divisao, scoring="r2")

    return {
        "dobras": folds,
        "r2_por_dobra": [round(float(s), 4) for s in scores],
        "r2_medio": round(float(scores.mean()), 4),
        "r2_desvio": round(float(scores.std()), 4),
    }


def compare_models(
    df: pd.DataFrame,
    conjuntos: dict[str, tuple[list[str], list[str]]] | None = None,
    target: str = config.TARGET,
) -> pd.DataFrame:
    """Treina um modelo por conjunto de variáveis e põe as métricas lado a lado.

    Serve para decidir com número, e não por gosto, se o modelo maior se paga.
    """
    conjuntos = conjuntos if conjuntos is not None else {
        "completo": (config.MODEL_NUMERIC_FULL, config.MODEL_CATEGORICAL_FULL),
        "enxuto": (config.MODEL_NUMERIC_REDUCED, config.MODEL_CATEGORICAL_REDUCED),
    }

    linhas = []
    for nome, (numeric, categorical) in conjuntos.items():
        ajustado = train(df, numeric=numeric, categorical=categorical, target=target)
        cv = cross_val_r2(df, numeric=numeric, categorical=categorical, target=target)
        linhas.append(
            {
                "conjunto": nome,
                "variaveis": len(numeric) + len(categorical),
                "r2": ajustado.metrics["r2"],
                "mae": ajustado.metrics["mae"],
                "rmse": ajustado.metrics["rmse"],
                "r2_cv_medio": cv["r2_medio"],
                "r2_cv_desvio": cv["r2_desvio"],
            }
        )
    return pd.DataFrame(linhas)


def choose_model(
    comparacao: pd.DataFrame, tolerancia: float = config.R2_TOLERANCE
) -> str:
    """Escolhe o conjunto mais enxuto que não perde R² relevante.

    Regra escrita antes de ver o resultado: o modelo maior só vence se ganhar
    mais de `tolerancia` de R² sobre o menor.
    """
    por_tamanho = comparacao.sort_values("variaveis")
    menor = por_tamanho.iloc[0]
    maior = por_tamanho.iloc[-1]
    if maior["r2_cv_medio"] - menor["r2_cv_medio"] > tolerancia:
        return str(maior["conjunto"])
    return str(menor["conjunto"])
