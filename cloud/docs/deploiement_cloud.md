# Déploiement Cloud - Fictional Universe Builder

## Prérequis
1. Créer le fichier `cloudbuild.yaml`
2. Authentification Google Cloud

## 1. Configuration initiale du projet

### Authentification
```bash
gcloud auth login
```

### Création du projet
```bash
gcloud projects create fictional-universe-app --name="Fictional Universe Builder"
```

### Configuration de la facturation
```bash
# Récupérer l'identifiant de facturation
gcloud billing accounts list

# Joindre le projet à la facturation
gcloud billing projects link fictional-universe-app --billing-account=VOTRE_COMPTE_FACTURATION_ID
```

### Activation du projet
```bash
gcloud config set project fictional-universe-app
```

## 2. Activation des APIs nécessaires

```bash
gcloud services enable cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    vpcaccess.googleapis.com \
    storage.googleapis.com \
    sqladmin.googleapis.com \
    compute.googleapis.com
```

## 3. Configuration Docker et Artifact Registry

### Configuration Docker pour la région
```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

### Création du repository Artifact Registry
```bash
gcloud artifacts repositories create fictional-universe \
    --repository-format=docker \
    --location=europe-west1 \
    --description="Repository for Fictional Universe Builder"
```

## 4. Configuration du réseau

### Création du connecteur VPC
```bash
gcloud compute networks vpc-access connectors create fict-univ-con \
    --region=europe-west1 \
    --network=default \
    --range=10.8.0.0/28
```

### Configuration des rôles IAM
> **Note :** Cette étape est nécessaire pour éviter les échecs lors du premier déploiement

```bash
gcloud beta run services add-iam-policy-binding --region=europe-west1 --member=allUsers --role=roles/run.invoker fictional-universe-web
```

## 5. Déploiement de l'application

### Lancement du build
```bash
gcloud builds submit --config=cloudbuild.yaml
```

## 6. Configuration d'Ollama

### Option 1 : Cloud Run (problème de port)
```bash
gcloud run deploy fictional-universe-ollama \
  --image=ollama/ollama:latest \
  --region=europe-west1 \
  --port=11434 \
  --memory=8Gi \
  --cpu=4
```

### Option 2 : VM Compute Engine (recommandée)
```bash
gcloud compute instances create ollama-server \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --machine-type=n1-standard-4 \
  --boot-disk-size=50GB \
  --metadata=startup-script='#! /bin/bash
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    docker run -d -p 11434:11434 ollama/ollama'
```

## 7. Configuration réseau pour Ollama

### Récupération de l'IP de la VM
```bash
gcloud compute instances describe ollama-server --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### Mise à jour de la variable d'environnement
```bash
gcloud run services update fictional-universe-web --region=europe-west1 --set-env-vars=OLLAMA_HOST=http://IP_VM:11434
```

### Autorisation du trafic
```bash
gcloud compute firewall-rules create allow-ollama --allow=tcp:11434 --description="Allow Ollama API access" --direction=INGRESS
```

### Configuration des permissions
```bash
gcloud run services add-iam-policy-binding fictional-universe-ollama --region=europe-west1 --member="user:devarieux.clement@gmail.com" --role="roles/run.invoker"
```

### Alternative de configuration Ollama Host
```bash
gcloud run services update fictional-universe-web --region=europe-west1 --set-env-vars=OLLAMA_HOST=https://fictional-universe-ollama-1069829401679.europe-west1.run.app
```

## 8. Vérifications

### Vérifier que la VM fonctionne
```bash
gcloud compute instances list
```

### Vérifier les variables d'environnement
```bash
gcloud run services describe fictional-universe-web --region=europe-west1 --format="yaml(spec.template.spec.containers[].env)"
```

## 9. Installation et configuration d'Ollama sur la VM

### Connexion à la VM
```bash
gcloud compute ssh ollama-server
```

### Installation dans la VM
```bash
# Mettre à jour les paquets
sudo apt-get update

# Installer les prérequis
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Ajouter la clé GPG Docker
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Ajouter le repository Docker
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Mettre à jour et installer Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Démarrer et activer Docker
sudo systemctl start docker
sudo systemctl enable docker

# Exécuter Ollama
sudo docker run -d -p 11434:11434 ollama/ollama

# Identifier l'ID du conteneur Ollama
CONTAINER_ID=$(sudo docker ps -q --filter ancestor=ollama/ollama)

# Télécharger le modèle
sudo docker exec -it $CONTAINER_ID ollama pull llama3.2
```

### Vérifications finales dans la VM
```bash
# Vérifier que Docker fonctionne
sudo docker ps

# Vérifier que Ollama répond
curl http://localhost:11434/api/version
```

## 10. Configuration finale

### Mise à jour de l'IP après sortie de SSH
```bash
# Récupérer l'IP de la VM
gcloud compute instances describe ollama-server --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# Mettre à jour l'application avec cette IP
gcloud run services update fictional-universe-web --region=europe-west1 --set-env-vars=OLLAMA_HOST=http://VOTRE_IP_RÉELLE:11434
```

### Configuration de la base de données
```bash
gcloud run services update fictional-universe-web \
  --region=europe-west1 \
  --update-env-vars=DB_PATH=/tmp/database.db
```

## 11. Gestion de la VM

### Arrêter la VM
```bash
# Arrêter manuellement la VM quand on a fini
gcloud compute instances stop ollama-server
```

### Redémarrer la VM
```bash
gcloud compute instances start ollama-server
```

> **⚠️ ATTENTION :** Il faut éventuellement mettre à jour l'IP de la VM si elle change après un redémarrage.