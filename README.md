# Projeto ANEEL — Energia em Risco

Projeto de **Análise de Dados + Machine Learning** utilizando dados públicos da ANEEL.

## Objetivo
Analisar DEC/FEC, estudar os fatos geradores das interrupções e preparar um modelo preditivo de risco regulatório.

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
