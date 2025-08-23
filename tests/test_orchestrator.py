from src.agent.orchestrator import route_intent

def test_route_intent_pib():
    tools = route_intent("Qual foi o PIB do RS em 2022?")
    assert "pib_rs_ano" in tools

def test_route_intent_populacao():
    tools = route_intent("Quais os municípios mais populosos do RS?")
    assert "top_municipios_pop" in tools

def test_route_intent_fallback_websearch():
    tools = route_intent("Me conte curiosidades históricas do RS")
    assert "web_search" in tools
