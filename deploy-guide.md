````
# Mock MES - Deploy su Azure

Questa guida mostra come effettuare la **build** dell’immagine Docker su **Azure Container Registry (ACR)** e come creare un **Azure Container Instance (ACI)** per esporre il servizio.

---

## 🔧 Prerequisiti

- Azure CLI installata e autenticata (`az login`)
- Risorsa **Azure Container Registry** già esistente (`acrregistrymockservers`)
- Risorsa **Resource Group** già esistente (`it-sbx-mock-ai-test-scenario`)

---

## 🚀 Build dell’immagine con ACR

Il comando seguente effettua la build del container direttamente dal repository GitHub e pubblica l’immagine su **Azure Container Registry**:

```bash
az acr build \
  --registry acrregistrymockservers \
  --image mock-mes:latest \
  https://github.com/edwfr/mock-mes
````

---

## 📦 Creazione del Container Instance

Una volta creata l’immagine, è possibile avviare un container con il seguente comando:

```bash
az container create \
  --resource-group it-sbx-mock-ai-test-scenario \
  --name mock-mes \
  --image acrregistrymockservers.azurecr.io/mock-mes:latest \
  --registry-login-server acrregistrymockservers.azurecr.io \
  --registry-username $(az acr credential show --name acrregistrymockservers --query username -o tsv) \
  --registry-password $(az acr credential show --name acrregistrymockservers --query passwords[0].value -o tsv) \
  --ports 80 \
  --os-type Linux \
  --cpu 1 \
  --memory 1.5 \
  --ip-address Public \
  --dns-name-label mock-mes
```

---

## 🌍 Accesso al servizio

Una volta avviato, il container sarà accessibile pubblicamente tramite DNS:

```
http://mock-mes.westeurope.azurecontainer.io
```

*(La regione `westeurope` può variare in base alla configurazione del tuo ACI).*

---

## 🧹 Pulizia delle risorse

Per eliminare il container:

```bash
az container delete \
  --resource-group it-sbx-mock-ai-test-scenario \
  --name mock-mes \
  --yes
```

Per eliminare anche l’immagine dal registro:

```bash
az acr repository delete \
  --name acrregistrymockservers \
  --image mock-mes:latest \
  --yes
```
