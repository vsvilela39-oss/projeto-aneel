
from pathlib import Path
import requests

ARQUIVOS_PADRAO = [
    "dim_causa_interrupcao_final.parquet",
    "dim_conjunto.parquet",
    "dim_data.parquet",
    "dim_distribuidora.parquet",
    "dim_indicador.parquet",
    "dim_motivo_interrupcao.parquet",
    "dim_tipo_interrupcao.parquet",
    "fato_causa_mensal_final.parquet",
    "fato_continuidade_final.parquet",
]


def baixar_arquivo(url, destino):

    destino = Path(destino)

    destino.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if destino.exists() and destino.stat().st_size > 0:
        print(
            f"[cache] {destino.name}"
        )
        return destino

    print(
        f"[download] {destino.name}"
    )

    with requests.get(
        url,
        stream=True,
        timeout=(30, 900)
    ) as resposta:

        resposta.raise_for_status()

        total = int(
            resposta.headers.get(
                "content-length",
                0
            )
        )

        recebido = 0

        with destino.open("wb") as arquivo:

            for bloco in resposta.iter_content(
                chunk_size=4 * 1024 * 1024
            ):

                if not bloco:
                    continue

                arquivo.write(bloco)
                recebido += len(bloco)

                if total:
                    percentual = (
                        recebido / total * 100
                    )

                    print(
                        f"\r"
                        f"{percentual:5.1f}% "
                        f"- "
                        f"{recebido / 1024 / 1024:.1f} MB",
                        end=""
                    )

        if total:
            print()

    print(
        f"[ok] {destino.name} "
        f"- "
        f"{destino.stat().st_size / 1024 / 1024:.2f} MB"
    )

    return destino


def baixar_release(
    usuario="vsvilela39-oss",
    repositorio="projeto-aneel",
    tag="v1.0-dados",
    arquivos=None,
    destino="/content/projeto-aneel/dados/parquet_modelo"
):

    if arquivos is None:
        arquivos = ARQUIVOS_PADRAO

    destino = Path(destino)

    destino.mkdir(
        parents=True,
        exist_ok=True
    )

    base_url = (
        f"https://github.com/"
        f"{usuario}/"
        f"{repositorio}/"
        f"releases/download/"
        f"{tag}"
    )

    baixados = []

    erros = []

    for nome in arquivos:

        url = (
            f"{base_url}/{nome}"
        )

        caminho = (
            destino / nome
        )

        try:

            baixar_arquivo(
                url,
                caminho
            )

            baixados.append(
                caminho
            )

        except Exception as erro:

            print(
                f"[erro] {nome}"
            )

            print(erro)

            erros.append(nome)

    print()
    print("=" * 50)
    print("RESUMO")
    print("=" * 50)

    for arquivo in baixados:

        print(
            arquivo.name,
            f"{arquivo.stat().st_size / 1024 / 1024:.2f} MB"
        )

    if erros:

        print()
        print("Arquivos com erro:")

        for nome in erros:
            print("-", nome)

    return baixados
