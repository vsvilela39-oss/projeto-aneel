from pathlib import Path
import requests

ARQUIVOS_PADRAO = [
    "dim_data.parquet",
    "dim_distribuidora.parquet",
    "dim_conjunto.parquet",
    "dim_indicador.parquet",
    "dim_tipo_interrupcao.parquet",
    "dim_motivo_interrupcao.parquet",
    "dim_fato_gerador.parquet",
    "fato_continuidade.parquet",
    "fato_interrupcao.parquet",
    "fato_causa_mensal.parquet",
]

def baixar_arquivo(url: str, destino: Path):
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and destino.stat().st_size > 0:
        print(f"[cache] {destino.name}")
        return destino
    print(f"[download] {destino.name}")
    with requests.get(url, stream=True, timeout=(30, 900)) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        recebido = 0
        with destino.open("wb") as f:
            for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                recebido += len(chunk)
                if total:
                    print(f"\r  {recebido/total*100:5.1f}% - {recebido/1024/1024:.1f} MB", end="")
        if total:
            print()
    return destino

def baixar_release(usuario: str, repositorio: str, tag: str = "v1.0-dados", arquivos=None,
                   destino="/content/projeto-aneel/dados/parquet_modelo"):
    if arquivos is None:
        arquivos = ARQUIVOS_PADRAO
    destino = Path(destino)
    base = f"https://github.com/{usuario}/{repositorio}/releases/download/{tag}"
    baixados = []
    for nome in arquivos:
        try:
            baixados.append(baixar_arquivo(f"{base}/{nome}", destino / nome))
        except requests.HTTPError as e:
            print(f"[aviso] {nome}: {e}")
    return baixados
