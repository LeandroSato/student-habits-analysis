# Hábitos e desempenho estudantil

Análise de 1000 alunos para responder uma pergunta prática: **quais hábitos
andam junto com nota alta, e o que dá para fazer com essa informação?**

Resposta do desafio técnico de Analytics Engineer (estágio) da
[Klubi](https://github.com/somosbro/data-analysis-challenge-klubi), por Leandro Sato.

> **Aviso de leitura:** tudo aqui é **associação**, não causa. O dado é
> observacional e de um único momento, então nada no repositório afirma que mudar
> um hábito *provoca* mudança na nota. A seção de limitações detalha.

## Principais conclusões

![Horas de estudo contra nota, em dispersão e por faixa](reports/figures/02_variavel_de_maior_impacto.png)

**1. Horas de estudo dominam, e não é perto.** Correlação de **0,825** com a
nota, contra 0,32 da segunda colocada. No modelo, cada hora a mais vale
**+9,5 pontos**. Por faixa, a nota média vai de 45,6 (até 2h/dia) a 97,4
(6h ou mais).

**2. Tempo de tela de lazer é o maior peso negativo — como bloco, não separado.**
Redes sociais e streaming somados correlacionam **−0,238** com a nota, mais forte
que cada um sozinho (−0,167 e −0,172). A conclusão que se sustenta é sobre tempo
total de tela, não sobre uma plataforma específica.

**3. Saúde mental é a segunda maior influência (r = 0,322)** e a **única**
variável que separa grupos de forma significativa: 63,4 de média na faixa baixa
contra 75,9 na alta, 12,5 pontos de diferença (Kruskal-Wallis, p < 0,000001,
ε² = 0,098). Mas é autodeclarada e medida junto com a nota — pode ser causa,
consequência, ou as duas.

**4. Não há diferença de nota por gênero.** 69,7 / 69,4 / 70,7 para Female, Male
e Other (p = 1 após correção). Também sem diferença: dieta, qualidade da
internet, trabalho de meio período, atividade extracurricular e **escolaridade
dos pais** — que costuma ser a explicação pronta para desempenho e aqui não
sustenta nada.

**5. O modelo prevê a nota com erro de ±4,1 pontos** (R² = 0,90), contra 12,4 de
chutar sempre a média. Com **sete hábitos**, nenhuma característica fixa do
aluno — o que é a parte acionável do resultado: tudo que explica a nota neste
modelo é comportamento, não origem.

**Recomendação prática, em uma linha:** para o aluno mediano, trocar uma hora de
rede social por uma hora de estudo leva a previsão de 68,4 para **80,6**. É a
troca mais direta de levar para uma conversa de tutoria — como hipótese a testar,
não como promessa.

As recomendações completas, com o tamanho de efeito de cada uma, estão em
[reports/06_insights.md](reports/06_insights.md).

## O simulador

![Tela do simulador de hábitos e nota](reports/figures/app_simulador.jpg)

Ajuste os hábitos de um aluno e o app mostra a nota que o modelo associa a esse
perfil, com as mudanças ordenadas pelo ganho previsto. Pensado para coordenação
pedagógica e tutoria: a decisão que ele apoia é **qual hábito levar para a
conversa primeiro**, e qual aluno chamar antes. O raciocínio completo está em
[reports/04_modelo.md](reports/04_modelo.md).

## Limitações

| Limitação | O que ela impede |
|---|---|
| **Dado observacional, de um único momento** | Impede qualquer afirmação de causa: nada foi sorteado, não há grupo de controle, e hábitos e nota foram medidos juntos. |
| **Causa reversa é plausível** | Ir bem na prova pode melhorar a saúde mental declarada, e quem vai bem pode se sentir à vontade para estudar mais. O dado não distingue. |
| **Variáveis não medidas** | Renda, escola de origem, conhecimento prévio, qualidade do professor — qualquer uma pode explicar parte do que aqui aparece como efeito de hábito. |
| **Tudo é autodeclarado** | Horas de estudo e saúde mental vêm do próprio aluno, com o viés de memória e de querer parecer bem. |
| **Efeito teto** | 48 alunos (4,8%) tiraram exatamente 100; o modelo subestima quem já está no topo, e a previsão é truncada em 100. |
| **Uma base, um contexto** | 1000 alunos, sem informação de país, instituição ou curso. Não há como saber para quem isso generaliza. |
| **Erro de ±4,1 pontos** | Serve para orientar conversa e priorização, não para decidir a vida de um aluno. |

**Para sair da correlação** seria preciso outro desenho: um piloto com grupo de
comparação sorteado, ou medir hábitos no começo do semestre e nota no fim. Até
lá, o que esta análise entrega é priorização apoiada em evidência de associação —
bem mais que palpite, bem menos que prova.

## Como rodar

Desenvolvido e testado em **Python 3.14.6**. As versões das bibliotecas estão
travadas em `requirements.txt`.

```powershell
git clone https://github.com/LeandroSato/student-habits-analysis.git
cd student-habits-analysis
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

No Linux ou macOS, troque a ativação por `source .venv/bin/activate`.

**Gerar a análise** (lê `data/raw/`, grava os relatórios em `reports/`):

```powershell
python analysis/run_analysis.py
```

**Abrir o simulador** (app interativo, abre em http://localhost:8501):

```powershell
streamlit run app/streamlit_app.py
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
docs/spec.md         escopo, decisões e porquês + lista das ferramentas usadas
                     (linguagem, bibliotecas, IA e skills) e das que ficaram de fora
```

O código de tratamento fica em `src/`, separado do script de análise e do app:
o mesmo tratamento alimenta o relatório e o Streamlit, sem código duplicado.

## Relatórios

| Etapa | Onde |
|---|---|
| 1. Exploração inicial e diagnóstico de qualidade | [reports/01_exploracao.md](reports/01_exploracao.md) |
| 2. Engenharia de dados (cada decisão com o motivo) | [reports/02_engenharia.md](reports/02_engenharia.md) |
| 3. Análise estatística e ranking de influência | [reports/03_estatistica.md](reports/03_estatistica.md) |
| 4. Modelo e simulador: que decisão apoia | [reports/04_modelo.md](reports/04_modelo.md) |
| 5. Visualização, com a leitura de cada gráfico | [reports/05_visualizacao.md](reports/05_visualizacao.md) |
| 6. Síntese de insights e recomendações | [reports/06_insights.md](reports/06_insights.md) |

Todos os relatórios são **gerados por código**: as frases são montadas a partir
dos valores calculados, então nenhum número foi digitado à mão e nenhum deles
pode divergir do CSV.
