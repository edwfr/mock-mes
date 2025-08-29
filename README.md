````
# Mock Server MES

Questo progetto implementa un **mock server** per simulare un sistema **MES (Manufacturing Execution System)** focalizzato sul tracciamento dell’avanzamento degli SFC (Shop Floor Control).  
Il server gira con **Flask** e fornisce API REST per gestire SFC, routing e avanzamenti di produzione.  

Il server gira sulla porta **80**.

---

## 🚀 Avvio del server

### In locale
```bash
python app.py
````

### Con Docker

Costruisci l'immagine:

```bash
docker build -t mock-mes .
```

Esegui il container:

```bash
docker run -d -p 80:80 mock-mes
```

---

## 📌 API disponibili

### 1. Creazione SFC

**POST** `/sfc`
Crea un nuovo SFC con ID univoco (es. `SFCMOCK1`).

---

### 2. Creazione Routing

**POST** `/routing`
Crea un nuovo routing con un numero di operazioni random (max 15).
Request body:

```json
{ "operations": 10 }
```

---

### 3. Assegnazione Routing a SFC

**POST** `/sfc/<sfc_id>/assign_routing`
Assegna un routing esistente a uno SFC.
Request body:

```json
{ "routing_id": "ROUTING1" }
```

---

### 4. Avanzamento Operazione

**POST** `/sfc/<sfc_id>/advance`
Completa l’operazione in corso e mette in `in work` la successiva.

---

### 5. Rollback dell’intero SFC a uno step specifico

**POST** `/sfc/<sfc_id>/rollback`
Riporta l’SFC a uno step specifico, azzerando le operazioni successive.
Request body:

```json
{ "step": 3 }
```

---

### 6. Avanzamento Forzato

**POST** `/sfc/<sfc_id>/force_advance`
Forza l’avanzamento dello SFC a un certo step.
Le operazioni intermedie vengono segnate come `bypassed`.
Request body:

```json
{ "step": 5 }
```

---

### 7. Rollback di una singola operazione

**POST** `/sfc/<sfc_id>/rollback_single`
Riporta **solo una operazione** a `blank`.

* Se era `in work`, viene riportata `blank` e la precedente diventa `in work`.
* Se era `done`, viene riportata `blank`.

Request body:

```json
{ "step": 2 }
```

---

### 8. Completamento Operazione

**POST** `/sfc/<sfc_id>/complete`
Completa l’operazione attualmente `in work` e mette la successiva in `in work`.

---

### 9. Stato SFC

**GET** `/sfc/<sfc_id>`
Restituisce lo stato completo di uno SFC (routing, operazioni e stato globale).

---

### 10. Stato Routing di un SFC

**GET** `/sfc/<sfc_id>/routing_state`
Restituisce lo stato dettagliato del routing associato a uno SFC.

---

## 📊 Stati possibili

* **SFC**

  * `New`: in attesa di iniziare
  * `In Work`: almeno una operazione in corso
  * `Done`: tutte le operazioni completate

* **Operazioni**

  * `blank`: non iniziata
  * `in work`: in esecuzione
  * `done`: completata
  * `bypassed`: saltata

---

## 🧪 Esempi di chiamate

### Creazione SFC

```bash
curl -X POST http://localhost/sfc
```

### Creazione routing da 8 operazioni

```bash
curl -X POST http://localhost/routing -H "Content-Type: application/json" -d '{"operations": 8}'
```

### Assegnazione routing a SFC

```bash
curl -X POST http://localhost/sfc/SFCMOCK1/assign_routing -H "Content-Type: application/json" -d '{"routing_id": "ROUTING1"}'
```

### Rollback a step 2

```bash
curl -X POST http://localhost/sfc/SFCMOCK1/rollback -H "Content-Type: application/json" -d '{"step": 2}'
```

### Rollback singola operazione step 2

```bash
curl -X POST http://localhost/sfc/SFCMOCK1/rollback_single -H "Content-Type: application/json" -d '{"step": 2}'
```

### Avanzamento forzato a step 5

```bash
curl -X POST http://localhost/sfc/SFCMOCK1/force_advance -H "Content-Type: application/json" -d '{"step": 5}'
```

---

## 📦 Dati mock generati

All’avvio il server genera automaticamente:

* **3 routing** con operazioni casuali
* **5 SFC** già assegnati a un routing casuale

```
