from __future__ import annotations
import requests
from langchain_openai import AzureChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import json
import os

load_dotenv()

# === CONFIGURAZIONE LLM (Azure OpenAI GPT-4o) ===
llm = AzureChatOpenAI(
    deployment_name="gpt-4o",
    model="gpt-4o",
    api_version="2024-12-01-preview",
    azure_endpoint="https://it-sbx-sde-openai.openai.azure.com/",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    temperature=0
)

BASE_URL = "http://mock-mes.italynorth.azurecontainer.io:80"

# =======================
# UTILITY FUNCTIONS
# =======================
def safe_post(url, payload=None):
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return resp.text
    except Exception as e:
        return f"Errore POST {url}: {str(e)}"

def safe_get(url):
    try:
        resp = requests.get(url, timeout=5)
        return resp.text
    except Exception as e:
        return f"Errore GET {url}: {str(e)}"

# =======================
# MES TOOLS
# =======================

# 1. Crea un nuovo SFC
def create_sfc_tool_func(input):
    """Crea un nuovo SFC con ID univoco (es. SFCMOCK1). Lo SFC sarà inizialmente in stato 'New'."""
    return safe_post(f"{BASE_URL}/sfc")

# 2. Crea un routing
def create_routing_tool_func(input):
    """Crea un routing con un numero specifico di operazioni (1-15). Se non specificato, il numero di operazioni viene scelto casualmente."""
    try:
        payload = json.loads(input) if input else None
    except:
        payload = None
    return safe_post(f"{BASE_URL}/routing", payload)

# 3. Assegna routing a uno SFC
def assign_routing_tool_func(input):
    """
    Assegna un routing esistente a uno SFC.
    Il primo step diventa 'in work'.
    Input JSON: {"sfc_id":"SFCMOCK1","routing_id":"ROUTING2"}
    """
    try:
        payload = json.loads(input)
        sfc_id = payload["sfc_id"]
        routing_id = payload["routing_id"]
        return safe_post(f"{BASE_URL}/sfc/{sfc_id}/assign_routing", {"routing_id": routing_id})
    except Exception as e:
        return f"Errore assign_routing_tool_func: {str(e)}"

# 4. Avanza operazione
def advance_operation_tool_func(input: str):
    """Completa l’operazione corrente in 'in work' e mette in 'in work' la successiva. Input: ID dello SFC"""
    sfc_id = input.strip()
    return safe_post(f"{BASE_URL}/sfc/{sfc_id}/advance")

# 5. Rollback SFC a step specifico
def rollback_tool_func(input):
    """
    Riporta lo SFC a uno step specifico:
    - le operazioni precedenti allo step target restano 'done'
    - lo step target diventa 'in work'
    - le operazioni successive diventano 'blank'
    Input JSON: {"sfc_id":"SFCMOCK1","step":3}
    """
    try:
        payload = json.loads(input)
        sfc_id = payload["sfc_id"]
        step = payload["step"]
        return safe_post(f"{BASE_URL}/sfc/{sfc_id}/rollback", {"step": step})
    except Exception as e:
        return f"Errore rollback_tool_func: {str(e)}"

# 6. Rollback singola operazione
def rollback_single_tool_func(input):
    """
    Riporta una singola operazione a 'blank'.
    Input JSON: {"sfc_id":"SFCMOCK1","step":3}
    """
    try:
        payload = json.loads(input)
        sfc_id = payload["sfc_id"]
        step = payload["step"]
        return safe_post(f"{BASE_URL}/sfc/{sfc_id}/rollback_single", {"step": step})
    except Exception as e:
        return f"Errore rollback_single_tool_func: {str(e)}"

# 7. Avanzamento forzato
def force_advance_tool_func(input):
    """
    Avanza uno SFC a uno step specifico.
    Gli step intermedi non completati diventano 'bypassed'.
    Input JSON: {"sfc_id":"SFCMOCK1","step":5}
    """
    try:
        payload = json.loads(input)
        sfc_id = payload["sfc_id"]
        step = payload["step"]
        return safe_post(f"{BASE_URL}/sfc/{sfc_id}/force_advance", {"step": step})
    except Exception as e:
        return f"Errore force_advance_tool_func: {str(e)}"

# 8. Completa operazione
def complete_operation_tool_func(input: str):
    """Completa l’operazione corrente dello SFC in 'in work'. La successiva diventa 'in work'. Input: ID dello SFC"""
    sfc_id = input.strip()
    return safe_post(f"{BASE_URL}/sfc/{sfc_id}/complete")

# 9. Stato SFC
def get_sfc_tool_func(input: str):
    """Restituisce lo stato completo dello SFC. Input: ID dello SFC"""
    sfc_id = input.strip()
    return safe_get(f"{BASE_URL}/sfc/{sfc_id}")

# 10. Stato routing di uno SFC
def get_routing_state_tool_func(input: str):
    """Restituisce lo stato del routing associato a uno SFC. Input: ID dello SFC"""
    sfc_id = input.strip()
    return safe_get(f"{BASE_URL}/sfc/{sfc_id}/routing_state")

# 11. Recupera tutti gli SFC
def get_all_sfcs_tool_func(input: str = ""):
    """Restituisce tutti gli SFC presenti nel sistema."""
    return safe_get(f"{BASE_URL}/sfcs")

# 12. Recupera tutti i routing
def get_all_routings_tool_func(input: str = ""):
    """Restituisce tutti i routing presenti nel sistema."""
    return safe_get(f"{BASE_URL}/routings")

# =======================
# LISTA TOOLS
# =======================
efTools = [
    Tool(name="create_sfc", func=create_sfc_tool_func, description=create_sfc_tool_func.__doc__),
    Tool(name="create_routing", func=create_routing_tool_func, description=create_routing_tool_func.__doc__),
    Tool(name="assign_routing", func=assign_routing_tool_func, description=assign_routing_tool_func.__doc__),
    Tool(name="advance_operation", func=advance_operation_tool_func, description=advance_operation_tool_func.__doc__),
    Tool(name="rollback", func=rollback_tool_func, description=rollback_tool_func.__doc__),
    Tool(name="rollback_single", func=rollback_single_tool_func, description=rollback_single_tool_func.__doc__),
    #Tool(name="force_advance", func=force_advance_tool_func, description=force_advance_tool_func.__doc__),
    Tool(name="complete_operation", func=complete_operation_tool_func, description=complete_operation_tool_func.__doc__),
    Tool(name="get_sfc", func=get_sfc_tool_func, description=get_sfc_tool_func.__doc__),
    Tool(name="get_routing_state", func=get_routing_state_tool_func, description=get_routing_state_tool_func.__doc__),
    Tool(name="get_all_sfcs", func=get_all_sfcs_tool_func, description=get_all_sfcs_tool_func.__doc__),
    Tool(name="get_all_routings", func=get_all_routings_tool_func, description=get_all_routings_tool_func.__doc__),
]

# =======================
# MEMORIA CONVERSAZIONE
# =======================
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# =======================
# CREAZIONE AGENTE
# =======================
agent = initialize_agent(
    tools=efTools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    memory=memory,
    verbose=True
)

# =======================
# =======================
# CHAT INTERATTIVA
# =======================
print("Benvenuto nel tuo agente MES. Digita 'exit' per uscire.\n")
chat_history = []

while True:
    user_input = input("Tu: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Chiusura agente...")
        break

    chat_history.append({"role": "user", "content": user_input})

    try:
        # Costruiamo il contesto con tutta la conversazione
        conversation_text = ""
        for msg in chat_history:
            role = "Utente" if msg["role"] == "user" else "Agente"
            conversation_text += f"{role}: {msg['content']}\n"

        # Passiamo l’intero storico come input all’agente
        response = agent.run(conversation_text)

        chat_history.append({"role": "assistant", "content": response})
        print(f"Agente: {response}\n")

    except Exception as e:
        print(f"Errore durante l'elaborazione: {str(e)}\n")
