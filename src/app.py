import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# >>> use o agente
from src.agent.orchestrator import run_agent

app = FastAPI(title="RS-Dados Chatbot", version="0.1.0")

class Query(BaseModel):
    question: str

@app.post("/chat")
def chat(q: Query):
    answer = run_agent(q.question)
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)

