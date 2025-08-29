from flask import Flask, jsonify, request
import random

app = Flask(__name__)

# ---------------------------
# In-memory data storage
# ---------------------------
sfc_counter = 1
sfcs = {}          # SFC ID -> dict con routing e stato
routings = {}      # Routing ID -> lista di operazioni

# Stati possibili per le operazioni
OPERATION_STATES = ["blank", "in work", "done", "bypassed"]

# ---------------------------
# Helper Functions
# ---------------------------
def generate_operation(i):
    return {
        "id": i,
        "description": f"Operation {i}",
        "state": "blank"
    }

def create_routing(n):
    return [generate_operation(i+1) for i in range(n)]

def get_sfc_state(sfc):
    ops = sfcs[sfc]["operations"]
    if all(op["state"] == "done" for op in ops):
        return "Done"
    elif any(op["state"] == "in work" for op in ops):
        return "In Work"
    else:
        return "New"

# ---------------------------
# API Endpoints
# ---------------------------

@app.route("/sfc", methods=["POST"])
def create_sfc():
    """Crea un nuovo SFC"""
    global sfc_counter
    sfc_id = f"SFCMOCK{sfc_counter}"
    sfc_counter += 1
    sfcs[sfc_id] = {
        "routing": None,
        "operations": [],
    }
    return jsonify({"sfc_id": sfc_id})

@app.route("/routing", methods=["POST"])
def create_routing_endpoint():
    """Crea un nuovo routing"""
    data = request.json
    n = data.get("operations", random.randint(1, 15))
    routing_id = f"ROUTING{len(routings)+1}"
    routings[routing_id] = create_routing(n)
    return jsonify({"routing_id": routing_id, "operations": routings[routing_id]})

@app.route("/sfc/<sfc_id>/assign_routing", methods=["POST"])
def assign_routing(sfc_id):
    """Assegna un routing a uno SFC"""
    data = request.json
    routing_id = data.get("routing_id")
    if sfc_id not in sfcs:
        return jsonify({"error": "SFC not found"}), 404
    if routing_id not in routings:
        return jsonify({"error": "Routing not found"}), 404
    sfcs[sfc_id]["routing"] = routing_id
    sfcs[sfc_id]["operations"] = [op.copy() for op in routings[routing_id]]
    if sfcs[sfc_id]["operations"]:
        sfcs[sfc_id]["operations"][0]["state"] = "in work"
    return jsonify({"sfc_id": sfc_id, "routing": routing_id, "operations": sfcs[sfc_id]["operations"]})

@app.route("/sfc/<sfc_id>/advance", methods=["POST"])
def advance_operation(sfc_id):
    """Avanza l'SFC di una operazione"""
    if sfc_id not in sfcs:
        return jsonify({"error": "SFC not found"}), 404
    operations = sfcs[sfc_id]["operations"]
    for i, op in enumerate(operations):
        if op["state"] == "in work":
            op["state"] = "done"
            if i+1 < len(operations):
                operations[i+1]["state"] = "in work"
            break
    return jsonify({"sfc_id": sfc_id, "operations": operations, "sfc_state": get_sfc_state(sfc_id)})

@app.route("/sfc/<sfc_id>/rollback", methods=["POST"])
def rollback_operation(sfc_id):
    """Rollback SFC a uno step specifico.
    Input JSON: {"step": n} dove n è l'indice dell'operazione a cui riportare lo SFC
    """
    if sfc_id not in sfcs:
        return jsonify({"error": "SFC not found"}), 404
    data = request.json
    target_step = data.get("step")
    if target_step is None:
        return jsonify({"error": "Step not provided"}), 400
    operations = sfcs[sfc_id]["operations"]
    # Controllo validità step
    if not isinstance(target_step, int) or target_step < 1 or target_step > len(operations):
        return jsonify({"error": "Invalid step"}), 400
    # Aggiorna stati delle operazioni
    for i, op in enumerate(operations):
        if i < target_step - 1:
            op["state"] = "done"
        elif i == target_step - 1:
            op["state"] = "in work"
        else:
            op["state"] = "blank"
    return jsonify({
        "sfc_id": sfc_id,
        "operations": operations,
        "sfc_state": get_sfc_state(sfc_id)
    })


@app.route("/sfc/<sfc_id>/force_advance", methods=["POST"])
def force_advance(sfc_id):
    """Avanzamento forzato SFC a uno step specifico"""
    data = request.json
    target_step = data.get("step")
    operations = sfcs[sfc_id]["operations"]
    for i, op in enumerate(operations):
        if i < target_step-1:
            if op["state"] != "done":
                op["state"] = "bypassed"
        elif i == target_step-1:
            op["state"] = "in work"
        else:
            op["state"] = "blank"
    return jsonify({"sfc_id": sfc_id, "operations": operations, "sfc_state": get_sfc_state(sfc_id)})

@app.route("/sfc/<sfc_id>/rollback_single", methods=["POST"])
def rollback_single_operation(sfc_id):
    """Rollback della sola operazione corrente 'in work' dello SFC.
    La corrente diventa 'blank', la precedente (che era 'done') diventa 'in work'.
    Non è possibile fare rollback se la corrente è la prima operazione.
    """
    if sfc_id not in sfcs:
        return jsonify({"error": "SFC not found"}), 404

    operations = sfcs[sfc_id]["operations"]

    # Trova l'operazione corrente in work
    current_idx = None
    for i, op in enumerate(operations):
        if op["state"] == "in work":
            current_idx = i
            break

    if current_idx is None:
        return jsonify({"error": "No operation currently in work"}), 400

    if current_idx == 0:
        return jsonify({"error": "Cannot rollback the first operation"}), 400

    # Imposta corrente a blank
    operations[current_idx]["state"] = "blank"
    # Imposta la precedente (che era done) a in work
    operations[current_idx - 1]["state"] = "in work"

    return jsonify({
        "sfc_id": sfc_id,
        "operations": operations,
        "sfc_state": get_sfc_state(sfc_id)
    })


@app.route("/sfc/<sfc_id>/complete", methods=["POST"])
def complete_operation(sfc_id):
    """Completa l'operazione corrente dello SFC"""
    operations = sfcs[sfc_id]["operations"]
    for i, op in enumerate(operations):
        if op["state"] == "in work":
            op["state"] = "done"
            if i+1 < len(operations):
                operations[i+1]["state"] = "in work"
            break
    return jsonify({"sfc_id": sfc_id, "operations": operations, "sfc_state": get_sfc_state(sfc_id)})

@app.route("/sfc/<sfc_id>", methods=["GET"])
def get_sfc(sfc_id):
    """Stato completo dello SFC"""
    if sfc_id not in sfcs:
        return jsonify({"error": "SFC not found"}), 404
    return jsonify({
        "sfc_id": sfc_id,
        "routing": sfcs[sfc_id]["routing"],
        "operations": sfcs[sfc_id]["operations"],
        "sfc_state": get_sfc_state(sfc_id)
    })

@app.route("/sfc/<sfc_id>/routing_state", methods=["GET"])
def get_routing_state(sfc_id):
    """Stato del routing di uno SFC"""
    if sfc_id not in sfcs:
        return jsonify({"error": "SFC not found"}), 404
    operations = sfcs[sfc_id]["operations"]
    return jsonify({
        "sfc_id": sfc_id,
        "routing": sfcs[sfc_id]["routing"],
        "operations": [{"id": op["id"], "description": op["description"], "state": op["state"]} for op in operations],
        "sfc_state": get_sfc_state(sfc_id)
    })

# ---------------------------
# API per ottenere tutti gli SFC
# ---------------------------
@app.route("/sfcs", methods=["GET"])
def get_all_sfcs():
    """Restituisce tutti gli SFC presenti nel sistema"""
    all_sfcs = {}
    for sfc_id, data in sfcs.items():
        all_sfcs[sfc_id] = {
            "routing": data["routing"],
            "operations": data["operations"],
            "sfc_state": get_sfc_state(sfc_id)
        }
    return jsonify(all_sfcs)

# ---------------------------
# API per ottenere tutti i routing
# ---------------------------
@app.route("/routings", methods=["GET"])
def get_all_routings():
    """Restituisce tutti i routing presenti nel sistema"""
    all_routings = {}
    for routing_id, operations in routings.items():
        all_routings[routing_id] = operations
    return jsonify(all_routings)

# ---------------------------
# Generate random data
# ---------------------------
def generate_mock_data(num_routings=3, num_sfcs=5):
    global sfc_counter
    for i in range(num_routings):
        routing_id = f"ROUTING{i+1}"
        routings[routing_id] = create_routing(random.randint(5, 10))
    for i in range(num_sfcs):
        sfc_id = f"SFCMOCK{sfc_counter}"
        sfc_counter += 1
        routing_id = random.choice(list(routings.keys()))
        sfcs[sfc_id] = {
            "routing": routing_id,
            "operations": [op.copy() for op in routings[routing_id]]
        }
        sfcs[sfc_id]["operations"][0]["state"] = "in work"

generate_mock_data()

# ---------------------------
# Run Server
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
