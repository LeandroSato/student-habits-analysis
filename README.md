# Hábitos e desempenho estudantil

Análise de 1000 alunos para responder uma pergunta prática: **quais hábitos
andam junto com nota alta, e o que dá para fazer com essa informação?**

Resposta do desafio técnico de Analytics Engineer (estágio) da
[Klubi](https://github.com/somosbro/data-analysis-challenge-klubi), por Leandro Sato.

> **Aviso de leitura:** tudo aqui é **associação**, não causa. O dado é
> observacional e de um único momento, então nada no repositório afirma que mudar
> um hábito *provoca* mudança na nota. A seção de limitações detalha.

## Como rodar

Precisa de Python 3.11 ou mais novo (desenvolvido em 3.14.6).

```powershell
git clone https://github.com/<seu-usuario>/klubi-student-habits.git
cd klubi-student-habits
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

No Linux ou macOS, troque a ativação por `source .venv/bin/activate`.

**Gerar a análise** (lê `data/raw/`, grava os relatórios em `reports/`):

```powershell
python analysis/run_analysis.py
```

**Rodar os testes:**

```powershell
pytest
```

## Estrutura do projeto

```
data/raw/            CSV do desafio, intacto
data/processed/      base tratada, gerada pela análise
src/                 módulos de tratamento, estatística e modelo
tests/               pytest das funções de tratamento
analysis/            script que roda tudo e grava os relatórios
app/                 simulador em Streamlit
reports/             relatório de cada etapa + figuras
docs/spec.md         escopo, decisões e porquês
```

O código de tratamento fica em `src/`, separado do script de análise e do app:
o mesmo tratamento alimenta o relatório e o Streamlit, sem código duplicado.

## Relatórios

| Etapa | Onde |
|---|---|
| 1. Exploração inicial e diagnóstico de qualidade | [reports/01_exploracao.md](reports/01_exploracao.md) |
| 2. Engenharia de dados (cada decisão com o motivo) | [reports/02_engenharia.md](reports/02_engenharia.md) |
| 3. Análise estatística e ranking de influência | [reports/03_estatistica.md](reports/03_estatistica.md) |

## Principais conclusões

Em construção — preenchido ao fim da análise.

## Limitações

Em construção — preenchido ao fim da análise.
