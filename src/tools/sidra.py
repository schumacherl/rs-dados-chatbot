import re
from typing import Tuple, List
import requests
import pandas as pd

SIDRA_API = "https://apisidra.ibge.gov.br/values"


# --- util: escolher coluna existente dentre opções
def _pick_col(options: List[str], columns: List[str]):
    return next((c for c in options if c in columns), None)


def get_pib_rs_ano(query: str) -> Tuple[str, List[str]]:
    """
    Busca o PIB do Rio Grande do Sul em determinado ano.
    Tabela 5938 (PIB a preços correntes, por UF).
    """
    m = re.search(r"(19|20)\d{2}", query or "")
    ano = m.group(0) if m else "2022"

    url = f"{SIDRA_API}/t/5938/n3/43/v/37/p/{ano}?formato=json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()

    if len(js) < 2:
        return f"Não encontrei dados do PIB do RS para {ano}.", [f"SIDRA/IBGE • t5938 • {ano} • {url}"]

    df = pd.DataFrame(js[1:])
    # coluna do valor pode variar
    val_col = _pick_col(["V", "Valor", "valor", "Value"], list(df.columns))
    if val_col is None:
        return (
            f"Não foi possível identificar a coluna de valor no retorno do SIDRA para {ano}. "
            f"Colunas disponíveis: {list(df.columns)}",
            [f"SIDRA/IBGE • t5938 • {ano} • {url}"],
        )

    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    if df[val_col].notna().sum() == 0:
        return (
            f"O retorno do SIDRA para {ano} não trouxe valores numéricos.",
            [f"SIDRA/IBGE • t5938 • {ano} • {url}"],
        )

    valor = float(df[val_col].iloc[0])
    txt = f"PIB do RS em {ano}: R$ {valor:,.0f}".replace(",", ".")
    fontes = [f"SIDRA/IBGE • t5938 • {ano} • {url}"]
    return txt, fontes


def top_municipios_pop(_query: str) -> Tuple[str, List[str]]:
    """
    Top 5 municípios mais populosos do RS (IBGE/SIDRA 2022 – t6579, v9324).
    Robusto a mudanças de nomes de colunas.
    """
    ano = "2022"
    url = f"{SIDRA_API}/t/6579/n6/all/v/9324/p/{ano}?formato=json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()
    if len(js) < 2:
        return "Não encontrei dados de população para 2022.", [f"SIDRA/IBGE • t6579 • {ano} • {url}"]

    df = pd.DataFrame(js[1:])
    cols = list(df.columns)

    # detectar colunas possíveis
    val_col = _pick_col(["V", "Valor", "valor", "Value"], cols)
    mun_col = _pick_col(["D3N", "Município", "Municipio", "Nome do Município"], cols)
    uf_col  = _pick_col(["D1N", "UF", "Unidade da Federação"], cols)

    if not val_col or not mun_col:
        # Ajuda no diagnóstico se quebrar de novo
        raise KeyError(f"Não achei colunas esperadas. Colunas recebidas: {cols}")

    # Filtra RS se houver coluna de UF
    if uf_col:
        df = df[df[uf_col] == "Rio Grande do Sul"]

    # Converte e prepara
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    df = df[[mun_col, val_col]].dropna().rename(columns={mun_col: "Município", val_col: "População"})

    top5 = df.sort_values("População", ascending=False).head(5).copy()
    top5["População"] = top5["População"].astype(float).map(lambda x: f"{int(round(x)):,.0f}".replace(",", "."))

    md = top5[["Município", "População"]].to_markdown(index=False)
    fontes = [f"SIDRA/IBGE • t6579 • {ano} • {url}"]
    return md, fontes
