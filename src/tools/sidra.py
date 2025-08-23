import requests
import pandas as pd

SIDRA_API = "https://apisidra.ibge.gov.br/values"

def get_pib_rs_ano(query: str):
    """
    Busca o PIB do Rio Grande do Sul em determinado ano.
    Usa a tabela 5938 (PIB a preços correntes, por UF).
    """
    import re
    m = re.search(r"(19|20)\d{2}", query)
    ano = m.group(0) if m else "2022"

    url = f"{SIDRA_API}/t/5938/n3/43/v/37/p/{ano}?formato=json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()

    if len(js) < 2:
        return f"Não encontrei dados do PIB do RS para {ano}", [f"SIDRA/IBGE tabela 5938 {ano}"]

    df = pd.DataFrame(js[1:])
    df["V"] = pd.to_numeric(df["V"], errors="coerce")

    valor = df["V"].iloc[0]
    txt = f"PIB do RS em {ano}: R$ {valor:,.0f}".replace(",", ".")
    fontes = [f"SIDRA/IBGE • tabela 5938 • {ano} • {url}"]

    return txt, fontes


def top_municipios_pop(_query: str):
    """
    Retorna os 5 municípios mais populosos do RS (estimativa IBGE 2022).
    """
    url = f"{SIDRA_API}/t/6579/n6/all/v/9324/p/2022?formato=json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()

    df = pd.DataFrame(js[1:])
    df["V"] = pd.to_numeric(df["V"], errors="coerce")
    df = df[df["D1N"] == "Rio Grande do Sul"]

    top5 = df.sort_values("V", ascending=False).head(5)
    top5 = top5.rename(columns={"D3N": "Município", "V": "População"})
    top5["População"] = top5["População"].map(lambda x: f"{int(x):,}".replace(",", "."))

    md = top5[["Município", "População"]].to_markdown(index=False)
    fontes = [f"SIDRA/IBGE • t6579 • 2022 • {url}"]

    return md, fontes
