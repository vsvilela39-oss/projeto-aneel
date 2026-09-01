# Como subir o projeto no GitHub

## 1. Crie o repositório
Crie no GitHub um repositório chamado `projeto-aneel`.

## 2. Suba esta estrutura
No computador:

```bash
git clone https://github.com/SEU_USUARIO/projeto-aneel.git
cd projeto-aneel
```

Copie o conteúdo deste pacote e execute:

```bash
git add .
git commit -m "Estrutura inicial do projeto ANEEL"
git push origin main
```

## 3. Clone no Colab

```python
!git clone https://github.com/SEU_USUARIO/projeto-aneel.git
%cd projeto-aneel
!pip install -r requirements.txt
```

## 4. Envie os arquivos brutos para `dados/raw/`

Arquivos esperados:

```text
continuidade_2020_2029.parquet
limites.csv
atributos.csv
interrupcoes_2024.parquet
interrupcoes_2025.parquet
```

## 5. Processe no Colab

```python
from src.processar_aneel_colab_github import main
resultado = main(anos_interrupcoes=[2024, 2025])
```

## 6. Publique os Parquets em uma Release
No GitHub: `Releases` → `Draft a new release`.

Tag sugerida: `v1.0-dados`

Faça upload dos arquivos de `dados/parquet_modelo/`.

## 7. Nos próximos notebooks, baixe a Release

```python
from src.baixar_dados_release import baixar_release
baixar_release(
    usuario="SEU_USUARIO",
    repositorio="projeto-aneel",
    tag="v1.0-dados"
)
```
