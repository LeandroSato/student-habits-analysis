# 6. Síntese de insights

Gerado por `analysis/run_analysis.py`. Todo número desta página vem das etapas anteriores e do código que as produziu.

> **Correlação não é causa.** Tudo nesta página mede se duas coisas andam juntas, nunca se uma produz a outra. O dado é observacional e de um único momento: não há grupo de controle, nada foi sorteado e qualquer relação aqui pode vir de uma terceira variável não medida, ou valer no sentido inverso.

## 6.1 Quais hábitos mais afetam as notas

A tabela junta as duas medidas que a análise produziu: a correlação simples (tarefa 3) e o peso dentro do modelo, que controla pelos outros hábitos (tarefa 4). Quando as duas apontam na mesma direção, a conclusão é mais firme.

| hábito | correlação com a nota | pontos por unidade (modelo) | pontos por desvio padrão | força |
|---|---|---|---|---|
| Horas de estudo por dia | 0.825 | 9.536 | 14.007 | forte |
| Saúde mental autodeclarada (1 a 10) | 0.322 | 1.949 | 5.551 | moderada |
| Horas de streaming por dia | -0.172 | -2.318 | -2.493 | fraca |
| Horas em redes sociais por dia | -0.167 | -2.703 | -3.169 | fraca |
| Exercício (vezes por semana) | 0.16 | 1.315 | 2.664 | fraca |
| Horas de sono por noite | 0.122 | 1.992 | 2.443 | fraca |

**Horas de estudo por dia domina.** Correlação de 0.825 e 9.536 pontos de nota por hora no modelo — 2.5 vezes o peso do segundo colocado quando se comparam desvios padrão. Nenhuma outra variável da base chega perto.

**O segundo bloco é de tempo de tela.** Redes sociais e streaming aparecem com sinal negativo nas duas medidas. Somadas em uma coluna só, elas correlacionam mais forte com a nota (-0.238) do que cada uma separada (-0.167 e -0.172), então a leitura que se sustenta é sobre **tempo de lazer em tela como um todo**, não sobre uma plataforma específica.

**Sono e exercício pesam pouco, mas pesam.** Associações fracas e significativas, e com sinal estável nas duas medidas — não são ruído, mas também não resolvem o problema de ninguém sozinhos.

## 6.2 Recomendações práticas

Cada recomendação abaixo é uma **hipótese a testar**, com o tamanho do efeito que o modelo prevê. O dado não permite prometer resultado — permite priorizar o que vale a pena tentar primeiro, e com que expectativa.

O ponto de partida é o aluno mediano da base (3.5h de estudo, 2.5h de redes, 1.8h de streaming, 6.5h de sono), com nota prevista de **68.4**.

### 1. Comece pela hora de estudo, não pelo resto

Uma hora a mais por dia leva a previsão de 68.38 para 77.92 (**+9.54 pontos**). Nenhuma outra mudança de uma unidade chega perto. Na comparação por faixa, a nota média vai de 45.6 (Até 2h) a 97.4 (6h ou mais).

Para quem coordena: se só der para tratar um assunto na conversa de tutoria, é esse.

### 2. Trate tempo de tela como um bloco só

Uma hora a menos de redes **e** uma a menos de streaming somam +5.02 pontos na previsão. Separar as duas em conversas diferentes desperdiça o achado: o que a análise sustenta é o tempo total. Por faixa, a nota média vai de 74.1 (Até 1h) a 64.2 (4h ou mais).

### 3. Combinar as duas rende mais que qualquer uma sozinha

Uma hora a mais de estudo com uma a menos de redes sociais: 68.38 para 80.62 (**+12.24 pontos**). É a troca mais direta de levar para um aluno, porque uma hora sai de um lugar e entra no outro.

### 4. Saúde mental merece programa próprio, não conselho

É a segunda variável de maior peso no modelo e a única que separa grupos de forma significativa. Mas é autodeclarada e medida junto com a nota: pode ser causa, consequência, ou as duas. A recomendação não é “melhore sua saúde mental” — é **tratar nota baixa persistente como possível sinal de alerta** e ter para onde encaminhar.

### 5. Sono: ganho pequeno, custo pequeno

Por faixa, Menos de 6h tem média 67.6 e a faixa recomendada tem 72.1. O efeito é fraco, mas é a recomendação mais barata da lista — entra como item de orientação geral, não como prioridade de programa.

### O que não recomendar

Dieta, qualidade da internet, trabalho de meio período e atividade extracurricular **não mostraram relação com a nota** nesta base. Montar programa em cima de qualquer um deles seria gastar esforço sem nada no dado que sustente.

## 6.3 Diferenças entre grupos

### Faixa de saúde mental — há diferença

| grupo | alunos | media | mediana | desvio |
|---|---|---|---|---|
| Baixa (1-3) | 301 | 63.43 | 63.6 | 15.94 |
| Média (4-6) | 317 | 67.87 | 69.2 | 16.85 |
| Alta (7-10) | 382 | 75.9 | 75.45 | 15.49 |

Kruskal-Wallis com p corrigido < 0,000001 e ε² = 0.098. Entre o grupo de maior média (Alta (7-10), 75.9) e o de menor (Baixa (1-3), 63.43) há **12.5 pontos**.

O ε² diz que cerca de 9.8% da variação de posição na nota está ligada a essa variável: real, mas longe de explicar tudo.

### Gênero — não há diferença, e isso é um achado

| grupo | alunos | media | mediana | desvio |
|---|---|---|---|---|
| Female | 481 | 69.74 | 70.7 | 16.9 |
| Male | 477 | 69.37 | 70.2 | 17.15 |
| Other | 42 | 70.65 | 69 | 13.76 |

Kruskal-Wallis com p = 1 e ε² = 0.0. As médias ficam a menos de um ponto umas das outras.

Vale registrar justamente porque contraria a expectativa de quem procura diferença de desempenho por gênero: **nesta base ela não existe**. Com 42 alunos em `Other`, o grupo é pequeno e um efeito pequeno poderia passar despercebido — mas a diferença entre `Female` e `Male`, que têm quase 480 cada, também não aparece.

### Os demais grupos

Sem diferença detectável em qualidade da internet, qualidade da dieta, escolaridade dos pais, trabalho de meio período, atividade extracurricular. Chama atenção que **escolaridade dos pais** esteja nessa lista: costuma ser a explicação pronta para diferença de desempenho, e nesta base ela não sustenta nada.

## 6.4 Limitações, ditas sem rodeio

| Limitação | O que ela impede |
|---|---|
| **Dado observacional, de um único momento** | Impede qualquer afirmação de causa. Nada foi sorteado, não há grupo de controle e hábitos e nota foram medidos juntos. |
| **Causa reversa é plausível em pelo menos duas variáveis** | Ir bem na prova pode melhorar a saúde mental declarada, e quem vai bem pode se sentir à vontade para estudar mais. O dado não distingue. |
| **Variáveis não medidas** | Renda, escola de origem, conhecimento prévio, qualidade do professor. Qualquer uma pode explicar parte do que aqui aparece como efeito de hábito. |
| **Tudo é autodeclarado** | Horas de estudo e saúde mental vêm do próprio aluno, com todo o viés de memória e de desejo de parecer bem que isso carrega. |
| **Efeito teto** | 48 alunos (4.8%) tiraram exatamente 100. O modelo subestima quem já está no topo. |
| **Uma base, um contexto** | 1000 alunos sem informação de país, instituição ou curso. Não há como saber para quem isso generaliza. |
| **Erro do modelo** | ±4.07 pontos em média. Serve para orientar conversa e priorização, não para decidir a vida de um aluno. |

### Como sair da correlação, se alguém quiser

A pergunta que este dado não responde é “mudar o hábito muda a nota?”. Responder exigiria outro desenho:

1. **Piloto com grupo de comparação.** Oferecer o programa de organização de estudo a parte dos alunos, sorteados, e comparar as notas depois.
2. **Medir em dois momentos.** Hábitos no começo do semestre, nota no fim — assim pelo menos a ordem no tempo fica estabelecida.
3. **Acompanhar os mesmos alunos ao longo do tempo**, para ver se quem muda de hábito muda de nota.

Enquanto isso não existe, o que esta análise entrega é priorização com base em evidência de associação — que é bem mais do que palpite, e bem menos do que prova.
