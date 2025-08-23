import os
from typing import Dict, Any, List, Tuple, Union

from src.agent.prompt import SYSTEM_PROMPT

# ==== (opcional) memória curtinha em RAM ====
from collections import deque
_MEMORY = deque(maxlen=10)
def _push_memory(text: str):
    _MEMORY.append(text)
def _get_memory() -> List[str]:
    return list(_MEMORY)

# ==== Importa ferramentas se já existirem; caso contrário usa stubs ====
TextOrTuple = Union[str, Tuple[str, List[str]]]

def _stub(name: str):
    def _f(_query: str) -> TextOrTuple:
        return (
            f"[{name}] ferramenta ainda não configurada. "
            f"Crie src/tools/{name}.py ou adicione a função correspondente.",
            [f"{name} • stub"]
        )
    return _f

try:
    # você pode criar essas funções em src/tools/ conforme o esqueleto sugerido
    from src.tools.sidra import get_pib_rs_ano, top_municipios_pop
except Exception:
    get_pib_rs_ano = _stub("sidra.get_pib_rs_ano")
    top_municipios_pop = _stub("sidra.top_municipios_pop")

try:
    from src.tools.datasus import get_indicadores_saude_rs
except Exception:
    get_indicadores_saude_rs = _stub("datasus.get_indicadores_saude_rs")

try:
    from src.tools.transparencia_rs import buscar_execucao_orcamentaria
except Exception:
    buscar_execucao_orcamentaria = _stub("transparencia_rs.buscar_execucao_orcamentaria")

try:
    from src.tools.websearch import web_search
except Exception:
    web_search = _stub("websearch")

try:
    from src.tools.tabulate import df_to_markdown
except Exception:
    def df_to_markdown(x):  # fallback simples
        return str(x)

TOOLS = {
    "pib_rs_ano": get_pib_rs_ano,
    "top_municipios_pop": top_municipios_pop,
    "indicadores_saude_rs": get_indicadores_saude_rs,
    "execucao_orcamentaria": buscar_execucao_orcamentaria,
    "web_search": web_search,
    "tabulate": df_to_markdown,
}

# ==== Roteador simples de intenção ====
def route_intent(user_query: str) -> List[str]:
    q = user_query.lower()
    tools: List[str] = []

    if any(k in q for k in ["pib", "contas regionais", "economia", "emprego", "exporta", "indústria", "industria", "agro"]):
        tools.append("pib_rs_ano")

    if any(k in q for k in ["popula", "município", "municipio", "municípios", "municipios", "cidades"]):
        tools.append("top_municipios_pop")

    if any(k in q for k in ["saúde", "saude", "leitos", "epidem", "datasus", "sus", "morbidade"]):
        tools.append("indicadores_saude_rs")

    if any(k in q for k in ["orçament", "orcament", "receita", "despesa", "execução", "execucao", "gasto público"]):
        tools.append("execucao_orcamentaria")

    # fallback
    if not tools:
        tools.append("web_search")

    return tools

# ==== Chamada ao LLM (placeholder seguro) ====
from openai import OpenAI
from dotenv import load_dotenv
import os

# carrega variáveis do .env
load_dotenv()

def call_llm(messages):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        temperature=0.2,
    )
    return resp.choices[0].message.content

    # Fallback sem LLM:
    tool_blob = next((m["content"] for m in messages if m["role"] == "system" and m["content"].startswith("Resultados de ferramentas:")), "")
    sources_blob = next((m["content"] for m in messages if m["role"] == "system" and m["content"].startswith("Fontes coletadas:")), "")
    user_q = next((m["content"] for m in messages if m["role"] == "user"), "")

    answer = (
        f"Resumo: processei sua pergunta — {user_q!r} — com as ferramentas disponíveis.\n\n"
        f"Detalhes coletados (pré-LLM):\n{tool_blob or '—'}\n\n"
        f"{sources_blob or ''}\n\n"
        "Observação: o modelo LLM ainda não está configurado. Para respostas naturais, "
        "defina OPENAI_API_KEY/OPENAI_MODEL (ou adapte em call_llm)."
    )
    return answer

# ==== Loop do agente ====
def run_agent(user_query: str) -> str:
    _push_memory(user_query)

    # Quais ferramentas usar?
    candidate_tools = route_intent(user_query)

    collected: List[str] = []
    sources: List[str] = []

    # Executa as ferramentas escolhidas
    for t in candidate_tools:
        tool = TOOLS.get(t)
        if not tool:
            collected.append(f"[{t}] ferramenta não encontrada.")
            continue
        try:
            result = tool(user_query)
            if isinstance(result, tuple) and len(result) == 2:
                payload, srcs = result
                if isinstance(srcs, list):
                    sources.extend(srcs)
                else:
                    sources.append(str(srcs))
            else:
                payload = result

            # Normaliza para string
            if hasattr(payload, "to_markdown"):
                collected.append(payload.to_markdown())
            else:
                collected.append(str(payload))

        except Exception as e:
            collected.append(f"[{t}] erro: {e}")

    # Monta mensagens para o LLM (ou fallback)
    sys = {"role": "system", "content": SYSTEM_PROMPT}
    mem = {"role": "system", "content": "Contexto/memória: " + " | ".join(_get_memory())}
    usr = {"role": "user", "content": user_query}
    tool_note = {"role": "system", "content": "Resultados de ferramentas:\n" + ("\n\n".join(collected) if collected else "—")}
    src_note = {"role": "system", "content": "Fontes coletadas: " + ("; ".join(sorted(set(sources))) if sources else "—")}

    messages = [sys, mem, usr, tool_note, src_note]
    return call_llm(messages)
