# MinIO

Implantação do **MinIO** em Kubernetes para armazenamento de objetos (logs/artefatos).  
Este diretório/ambiente foi pensado para ser aplicado **automaticamente** pelo **Argo CD** (app-of-apps), com overlays por ambiente (`values.yaml`, `prod/values.yaml`).

- [MinIO](#minio)
  - [Requisitos](#requisitos)
  - [Secret de Admin (existingSecret)](#secret-de-admin-existingsecret)
    - [Bitnami (mais comum)](#bitnami-mais-comum)
  - [Setup](#setup)
    - [Via Argo CD (recomendado)](#via-argo-cd-recomendado)

---

## Requisitos

- **Namespace** `minio` existente (ou crie: `kubectl create ns minio`).
- **StorageClass** padrão funcional para PVCs, ou configuração explícita de `storageClassName` no chart.
- Em produção, o **overlay** (`prod/values.yaml`) define:
  ```yaml
  existingSecret: "minio-credentials"
  ```
  (o chart lerá as credenciais de admin dessa Secret).

---

## Secret de Admin (existingSecret)

Crie **ANTES** do deploy a Secret **`minio-credentials`** no namespace `minio`.  

### Bitnami (mais comum)

Nos charts Bitnami, quando usamos `auth.existingSecret`, as **chaves esperadas** são:
- `root-user`
- `root-password`

Exemplo:

```bash
kubectl -n minio apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: minio-credentials
type: Opaque
stringData:
  root-user: ADMIN_USERNAME
  root-password: ADMIN_PASSWORD
EOF
```

> Substitua `ADMIN_USERNAME` e `ADMIN_PASSWORD`.  
> O `values.yaml`/`prod/values.yaml` do seu chart deve apontar para essa Secret (ex.: `auth.existingSecret: minio-credentials` ou campo equivalente).

## Setup

### Via Argo CD (recomendado)

Este componente é gerenciado pelo **app-of-apps**:
- O `Application` do MinIO é renderizado a partir deste diretório (ex.: `app-of-apps` aponta `path: minio` no base e `path: minio/prod` no overlay de produção).
- A ordem de instalação é controlada por **sync-waves** (ex.: MinIO na mesma wave do Postgres para paralelizar, ou em wave anterior ao Airflow).

Passos:
1. Garanta a Secret **`minio-credentials`** criada em `minio`.
2. Sincronize o **app-of-apps** no Argo CD (CLI/UI).  
3. O Argo CD aplicará o `Application` do MinIO conforme seus `values`.
