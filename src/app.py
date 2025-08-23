import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# por enquanto só um placeholder, depois vamos conectar no agente
def run_agent(user_query: str) -> str:
    return f"Recebi sua pergunta: '{user_query}'. (Integração com agente ainda em construção 🚧)"

# Inicializa FastAPI
app = FastAPI(title="RS-Dados Chatbot", version="0.1.0")

# Modelo da requisição
class Query(BaseModel):
    question: str

# Rota principal
@app.post("/chat")
def chat(q: Query):
    answer = run_agent(q.question)
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
