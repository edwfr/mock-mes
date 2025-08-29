from __future__ import annotations
import requests
from langchain_openai import AzureChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import StructuredTool
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
from pydantic import TypeAdapter

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
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.HTTPError as e:
        return f"HTTPError {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"Errore POST {url}: {str(e)}"

def safe_get(url):
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.HTTPError as e:
        return f"HTTPError {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"Errore GET {url}: {str(e)}"

# =======================
# MODELLI INPUT STRUCTURED
# =======================
class SFCStepInput(BaseModel):
    sfc_id: str
    step: int

class SFCAndRoutingInput(BaseModel):
    sfc_id: str
    routing_id: str

# =======================
# MES TOOLS
# =======================
def create_sfc_tool_func(input: str):
    """Crea un nuovo SFC con ID univoco. Stato iniziale: 'New'."""
    return safe_post(f"{BASE_URL}/sfc")

def create_routing_tool_func(input: str):
    """Crea un routing con un numero specifico di operazioni (1-15). Input JSON: {'operations': n}"""
    data = input if input else "{}"
    return safe_post(f"{BASE_URL}/routing", json.loads(data))

def assign_routing_tool_func(input: SFCAndRoutingInput):
    """
    Assegna un routing a uno SFC.
    Input JSON: {"sfc_id":"SFCMOCK1","routing_id":"ROUTING2"}
    """
    return safe_post(f"{BASE_URL}/sfc/{input.sfc_id}/assign_routing", {"routing_id": input.routing_id})

def advance_operation_tool_func(input: str):
    """Completa l'operazione corrente in 'in work' e avanza alla successiva. Input: ID SFC"""
    sfc_id = input.strip()
    return safe_post(f"{BASE_URL}/sfc/{sfc_id}/advance")

def rollback_wrapper(input_data):
    """
    Wrapper che accetta:
    - un dict
    - un oggetto SFCStepInput
    e chiama rollback_tool_func
    """
    if isinstance(input_data, dict):
        input_obj = SFCStepInput(**input_data)
    elif isinstance(input_data, SFCStepInput):
        input_obj = input_data
    else:
        raise ValueError(f"Tipo input non supportato: {type(input_data)}")
    
    return rollback_tool_func(input_obj)

def rollback_tool_func(input: SFCStepInput):
    """
    Riporta lo SFC a uno step specifico.
    Input JSON: {"sfc_id":"SFCMOCK1","step":3}
    """
    return safe_post(f"{BASE_URL}/sfc/{input.sfc_id}/rollback", {"step": input.step})


def rollback_single_tool_func(input: SFCStepInput):
    """
    Riporta una singola operazione a 'blank'.
    Si può usare questa funziona in maniera sequenziale per portare indietro l'sfc di più operazioni nel caso in cui la funzione di rollback massiva non funzioni.
    Input JSON: {"sfc_id":"SFCMOCK1","step":3}
    """
    return safe_post(f"{BASE_URL}/sfc/{input.sfc_id}/rollback_single", {"step": input.step})

def force_advance_tool_wrapper(input: dict | SFCStepInput):
    """
    Wrapper che accetta dict o SFCStepInput e chiama la funzione reale
    """
    if isinstance(input, dict):
        input_obj = SFCStepInput(**input)
    else:
        input_obj = input
    return force_advance_tool_func(input_obj)

def force_advance_tool_func(input: SFCStepInput):
    """
    Avanza uno SFC a uno step specifico.
    Gli step intermedi non completati diventano 'bypassed'.
    Input JSON: {"sfc_id":"SFCMOCK1","step":5}
    """
    return safe_post(f"{BASE_URL}/sfc/{input.sfc_id}/force_advance", {"step": input.step})

def complete_operation_tool_func(input: str):
    """Completa l'operazione corrente dello SFC. Input: ID SFC"""
    sfc_id = input.strip()
    return safe_post(f"{BASE_URL}/sfc/{sfc_id}/complete")

def get_sfc_tool_func(input: str):
    """Restituisce lo stato completo dello SFC. Input: ID SFC"""
    sfc_id = input.strip()
    return safe_get(f"{BASE_URL}/sfc/{sfc_id}")

def get_routing_state_tool_func(input: str):
    """Restituisce lo stato del routing associato a uno SFC. Input: ID SFC"""
    sfc_id = input.strip()
    return safe_get(f"{BASE_URL}/sfc/{sfc_id}/routing_state")

def get_all_sfcs_tool_func(input: str = ""):
    """Restituisce tutti gli SFC presenti nel sistema."""
    return safe_get(f"{BASE_URL}/sfcs")

def get_all_routings_tool_func(input: str = ""):
    """Restituisce tutti i routing presenti nel sistema."""
    return safe_get(f"{BASE_URL}/routings")

# =======================
# CREAZIONE TOOLS STRUCTURED
# =======================
efTools = [
    StructuredTool.from_function(create_sfc_tool_func, name="create_sfc", description=create_sfc_tool_func.__doc__),
    StructuredTool.from_function(create_routing_tool_func, name="create_routing", description=create_routing_tool_func.__doc__),
    StructuredTool.from_function(assign_routing_tool_func, name="assign_routing", description=assign_routing_tool_func.__doc__),
    StructuredTool.from_function(advance_operation_tool_func, name="advance_operation", description=advance_operation_tool_func.__doc__),
    StructuredTool.from_function(rollback_wrapper, name="rollback", description=rollback_tool_func.__doc__),
    StructuredTool.from_function(rollback_single_tool_func, name="rollback_single", description=rollback_single_tool_func.__doc__),
    StructuredTool.from_function(force_advance_tool_wrapper, name="force_advance", description=force_advance_tool_func.__doc__),
    StructuredTool.from_function(complete_operation_tool_func, name="complete_operation", description=complete_operation_tool_func.__doc__),
    StructuredTool.from_function(get_sfc_tool_func, name="get_sfc", description=get_sfc_tool_func.__doc__),
    StructuredTool.from_function(get_routing_state_tool_func, name="get_routing_state", description=get_routing_state_tool_func.__doc__),
    StructuredTool.from_function(get_all_sfcs_tool_func, name="get_all_sfcs", description=get_all_sfcs_tool_func.__doc__),
    StructuredTool.from_function(get_all_routings_tool_func, name="get_all_routings", description=get_all_routings_tool_func.__doc__),
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
        # Passiamo l'intero storico concatenato come testo
        conversation_text = "\n".join(
            [f"{'Utente' if msg['role']=='user' else 'Agente'}: {msg['content']}" for msg in chat_history]
        )

        response = agent.run(conversation_text)
        chat_history.append({"role": "assistant", "content": response})
        print(f"Agente: {response}\n")

    except Exception as e:
        print(f"Errore durante l'elaborazione: {str(e)}\n")
