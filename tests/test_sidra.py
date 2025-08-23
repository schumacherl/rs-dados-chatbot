import re
import os
import pytest

# Estes testes chamam a API pública do IBGE (integração). Podem falhar sem internet.
pytestmark = pytest.mark.integration

from src.tools.sidra import get_pib_rs_ano, top_municipios_pop

def test_get_pib_rs_ano_returns_tuple_with_sources():
    txt, fontes = get_pib_rs_ano("Qual o PIB do RS em 2022?")
    assert isinstance(txt, str)
    assert isinstance(fontes, (list, tuple))
    assert any("SIDRA/IBGE" in f for f in fontes)

def test_get_pib_rs_ano_contains_year():
    txt, _ = get_pib_rs_ano("Qual o PIB do RS em 2022?")
    assert re.search(r"2022", txt)

def test_top_municipios_pop_markdown_table():
    md, fontes = top_municipios_pop("Top 5 municípios mais populosos do RS")
    # Deve conter cabeçalhos markdown de tabela
    assert "| Município | População |" in md
    assert any("SIDRA/IBGE" in f for f in fontes)
