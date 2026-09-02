# Projeto ANEEL — Energia em Risco

Projeto de **Análise de Dados e Machine Learning** utilizando dados públicos da Agência Nacional de Energia Elétrica — ANEEL.

---

## Problema

Como utilizar dados públicos de continuidade e interrupções do fornecimento de energia elétrica para identificar padrões, compreender os principais fatores associados aos indicadores DEC e FEC e desenvolver um modelo de Machine Learning capaz de identificar conjuntos consumidores com maior risco de ultrapassar os limites regulatórios?

---

## Contexto

A continuidade do fornecimento de energia elétrica é um dos principais indicadores de qualidade do serviço prestado pelas distribuidoras.

A ANEEL acompanha essa qualidade por meio de indicadores como:

- **DEC — Duração Equivalente de Interrupção por Unidade Consumidora**
- **FEC — Frequência Equivalente de Interrupção por Unidade Consumidora**

Além dos indicadores consolidados, a ANEEL disponibiliza dados detalhados sobre interrupções, permitindo analisar fatores como:

- tipo da interrupção;
- motivo da interrupção;
- fato gerador;
- duração;
- conjunto consumidor;
- distribuidora;
- período de ocorrência.

O projeto utiliza essas informações para transformar dados regulatórios em análises que permitam identificar padrões, causas relevantes e situações de maior risco.

---

## Objetivo

Construir uma solução de análise de dados capaz de:

- analisar a evolução dos indicadores DEC e FEC;
- comparar os valores realizados com os limites regulatórios;
- identificar conjuntos consumidores com maior incidência de transgressões;
- analisar os principais grupos e causas das interrupções;
- identificar padrões temporais e operacionais;
- relacionar causas de interrupções ao comportamento dos indicadores de continuidade;
- desenvolver um modelo de Machine Learning para estimar o risco de transgressão futura.

---

## Usuários da solução

A solução pode apoiar diferentes perfis:

### Gestores e responsáveis pela operação

- acompanhar indicadores de continuidade;
- identificar conjuntos críticos;
- priorizar ações de melhoria;
- acompanhar tendências de desempenho.

### Analistas de Dados

- realizar análises exploratórias;
- identificar padrões e anomalias;
- construir indicadores;
- desenvolver dashboards.

### Cientistas de Dados

- preparar variáveis para Machine Learning;
- desenvolver modelos preditivos;
- avaliar importância das variáveis;
- identificar fatores relacionados ao risco de transgressão.

---

## Dados utilizados

Os dados são provenientes do **Portal de Dados Abertos da ANEEL**.

### Indicadores de continuidade

Utilizados para análise de:

- DEC;
- FEC;
- limites regulatórios;
- conjuntos consumidores;
- distribuidoras;
- evolução temporal.

Período utilizado:

**2020 a 2026**

### Interrupções de energia elétrica

Utilizadas para análise de:

- quantidade de interrupções;
- duração das interrupções;
- tipo da interrupção;
- motivo;
- fato gerador;
- grupos de causas;
- causas detalhadas.

Período utilizado:

**2024 e 2025**

A base original possui aproximadamente **18,9 milhões de registros de interrupções**.

Para viabilizar a análise no Power BI e no ambiente Google Colab, os eventos foram agregados em nível mensal, resultando em aproximadamente **1,98 milhão de registros**, uma redução de aproximadamente **89,5%**.

---

## Principais hipóteses

O projeto busca avaliar hipóteses como:

### H1
Conjuntos com maior quantidade de interrupções tendem a apresentar valores mais elevados de DEC e FEC.

### H2
Interrupções não programadas possuem maior impacto nos indicadores de continuidade.

### H3
Falhas relacionadas ao próprio sistema elétrico estão entre os principais fatores associados à duração das interrupções.

### H4
Eventos ambientais, como vegetação, vento e descargas atmosféricas, possuem participação relevante nas interrupções.

### H5
O histórico recente de DEC, FEC e interrupções pode ser utilizado para prever o risco de um conjunto ultrapassar o limite regulatório no período seguinte.

---




## Estratégia GitHub
O repositório guarda código, notebooks, documentação e configuração. Parquets grandes devem ser publicados em **GitHub Releases**, não diretamente no Git.

## Estrutura

```text
projeto-aneel/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
├── src/
├── notebooks/
├── docs/
└── dados/
    ├── raw/
    └── parquet_modelo/
```

## Colab

```python
!git clone https://github.com/SEU_USUARIO/projeto-aneel.git
%cd projeto-aneel
!pip install -r requirements.txt
```

Após enviar os arquivos oficiais da ANEEL para `dados/raw/`:

```python
from src.processar_aneel_colab_github import main
resultado = main(anos_interrupcoes=[2024, 2025])
```

Depois publique os Parquets gerados em uma GitHub Release `v1.0-dados`.
