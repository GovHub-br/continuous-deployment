# Airflow

Instalação do Airflow em um cluster Kubernetes a partir do Argo CD.  
Antes, é necessário fazer o deploy do MinIO.

- [Airflow](#airflow)
  - [Secrets](#secrets)
    - [Usuário admin](#usuário-admin)
    - [SMTP](#smtp)
    - [Git (DAGs/Plugins)](#git-dagsplugins)
    - [Webserver Secret Key](#webserver-secret-key)
    - [Redis (Celery/CeleryKubernetes)](#redis-celerycelerykubernetes)
    - [Integrações externas (SIAFI, SERPRO, SIAPE)](#integrações-externas-siafi-serpro-siape)
  - [Bucket](#bucket)
  - [Fernet Key](#fernet-key)
    - [Gerar (sem Python)](#gerar-sem-python)
    - [Gerar (Python)](#gerar-python)
    - [Secret](#secret)
  - [PostgreSQL](#postgresql)
  - [Setup](#setup)
    - [Via Argo CD (recomendado)](#via-argo-cd-recomendado)
    - [Aplicação manual (para testes)](#aplicação-manual-para-testes)

---

## Secrets

Crie o namespace (se ainda não existir):

```bash
kubectl create namespace airflow
````

### Usuário admin

Criação do usuário admin do Airflow. Substitua os campos `USERNAME`, `EMAIL`, `FIRSTNAME`, `LASTNAME`, `PASSWORD`.

```bash
kubectl -n airflow apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: airflow-webserver-admin-credentials
type: Opaque
stringData:
  WEBSERVER_DEFAULT_USER_ROLE: Admin
  WEBSERVER_DEFAULT_USER_USERNAME: USERNAME
  WEBSERVER_DEFAULT_USER_EMAIL: EMAIL
  WEBSERVER_DEFAULT_USER_FIRSTNAME: FIRSTNAME
  WEBSERVER_DEFAULT_USER_LASTNAME: LASTNAME
  WEBSERVER_DEFAULT_USER_PASSWORD: PASSWORD
EOF
```

### SMTP

Secret para envio de e-mails. Substitua `USER`, `PASSWORD` e ajuste host/porta se necessário.

```bash
kubectl -n airflow apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: airflow-smtp
type: Opaque
stringData:
  host: smtp.gmail.com
  starttls: "True"
  ssl: "False"
  user: USER
  password: PASSWORD
  port: "587"
  mail_from: USER
EOF
```

### Git (DAGs/Plugins)

Acesso aos repositórios de DAGs e plugins. Substitua `PERSONAL_ACCESS_TOKEN`.

```bash
kubectl -n airflow apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: airflow-git-credentials
type: Opaque
stringData:
  GIT_SYNC_USERNAME: nonexistant
  GIT_SYNC_PASSWORD: PERSONAL_ACCESS_TOKEN
  GITSYNC_USERNAME: nonexistant
  GITSYNC_PASSWORD: PERSONAL_ACCESS_TOKEN
EOF
```

### Webserver Secret Key

Secret para a chave do webserver. Substitua `SECRET_KEY`.

```bash
kubectl -n airflow apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: airflow-webserver-secret-key
type: Opaque
stringData:
  webserver-secret-key: SECRET_KEY
EOF
```

### Redis (Celery/CeleryKubernetes)

Somente se estiver usando **CeleryExecutor** ou **CeleryKubernetesExecutor**. Substitua `REDIS_PASSWORD`.

```bash
kubectl -n airflow apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: airflow-redis-password
type: Opaque
stringData:
  password: REDIS_PASSWORD
---
apiVersion: v1
kind: Secret
metadata:
  name: airflow-broker-url
type: Opaque
stringData:
  connection: redis://:REDIS_PASSWORD@airflow-redis:6379/0
EOF
```

### Integrações externas (SIAFI, SERPRO, SIAPE)

Essas secrets são **críticas** para as DAGs conseguirem consumir as APIs.
Substitua os valores conforme suas credenciais/certificados:

```bash
kubectl -n airflow apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: siafi-path-cert
type: kubernetes.io/tls
stringData:
  tls.crt: CERTIFICADO_SIAFI
  tls.key: CHAVE_SIAFI
---
apiVersion: v1
kind: Secret
metadata:
  name: siafi-credentials
type: Opaque
stringData:
  username: SIAFI_USER
  password: SIAFI_PASS
---
apiVersion: v1
kind: Secret
metadata:
  name: siafi-serpro-credentials
type: Opaque
stringData:
  SIAFI_CPF_SERPRO: CPF
  SIAFI_BEARER_KEY_SERPRO: BEARER_KEY
  SIAFI_BEARER_SECRET_SERPRO: BEARER_SECRET
---
apiVersion: v1
kind: Secret
metadata:
  name: siape-credentials
type: Opaque
stringData:
  SIAPE_BEARER_PASSWORD: BEARER_PASS
  SIAPE_BEARER_USER: BEARER_USER
  SIAPE_CPF_USER: CPF
  SIAPE_PASSWORD_USER: PASS
EOF
```

> **Importante:** sem essas secrets/certificados válidos, as requisições às APIs tendem a falhar (4xx/5xx).

---

## Bucket

Crie no MinIO/S3 um bucket **`airflow-logs`** e uma service account **`airflow-svcacct`**.
Depois, crie o Secret de conexão AWS para o Airflow:

```bash
kubectl -n airflow apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: minio-airflow-svcacct
type: Opaque
stringData:
  AIRFLOW_CONN_AWS_DEFAULT: '{
    "conn_type": "aws",
    "login": "ACCESS_KEY_ID",
    "password": "SECRET_ACCESS_KEY",
    "extra": {
      "endpoint_url": "http://minio-svc.minio.svc.cluster.local:9000",
      "region_name": "us-east-1"
    }
  }'
EOF
```

---

## Fernet Key

A Fernet key encripta informações sensíveis no metastore do Airflow.

### Gerar (sem Python)

```bash
head -c 32 /dev/urandom | base64 | tr '+/' '-_'
```

### Gerar (Python)

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Secret

Substitua `FERNET_KEY`:

```bash
kubectl -n airflow apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: airflow-fernet-key
type: Opaque
stringData:
  fernet-key: FERNET_KEY
EOF
```

---

## PostgreSQL

Crie a database e o usuário:

```sql
CREATE DATABASE DBNAME;
CREATE USER DBUSER WITH PASSWORD 'PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE DBNAME TO DBUSER;

-- PostgreSQL 15:
GRANT ALL ON SCHEMA public TO DBUSER;
```

Secret de conexão:

```bash
kubectl -n airflow apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: airflow-metadata
type: Opaque
stringData:
  connection: postgresql://DBUSER:PASSWORD@HOST:PORT/DBNAME
EOF
```

---

## Setup

### Via Argo CD (recomendado)

Este diretório é aplicado **automaticamente** pelo Argo CD através do **app-of-apps**.
Quando o `Application` raiz sincroniza, o Argo CD cria/aplica o `Application` do Airflow, respeitando a ordem definida pelas **sync-waves** (ex.: Postgres/MinIO → Airflow → Superset).

* Veja o README do **Argo CD**: `../argocd/README.md`
* Veja o README do **app-of-apps**: `../app-of-apps/README.md`

### Aplicação manual (para testes)

Para testar diretamente no cluster (sem esperar a sync do Argo CD), aplique o comando dentro da pasta prod ou homolog:

```bash
kubectl kustomize . \
  --enable-helm \
  --load-restrictor=LoadRestrictionsNone \
| kubectl apply -f - -n airflow
```
