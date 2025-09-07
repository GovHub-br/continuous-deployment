# Infra — Gov-Hub (GitOps)

Infraestrutura de dados gerenciada via **Argo CD (GitOps)**.  
Este monorepo contém os manifests/helm charts e os **overlays por ambiente** para:

- **Argo CD** (controle GitOps)
- **App-of-Apps** (gera os Applications filhos)
- **Airflow** (ETL/ELT)
- **MinIO** (objeto storage)
- **Postgres** (metastore/analytics)
- **Superset** (BI)
- **JupyterHub** (notebooks)

> **Importante:** não publicamos **URLs/portas** no README raiz. Endpoints e credenciais são tratados por ambiente e documentados internamente, quando necessário, nos respectivos READMEs.

---

## Sumário

- [Infra — Gov-Hub (GitOps)](#infra--gov-hub-gitops)
  - [Sumário](#sumário)
  - [Estrutura do repositório](#estrutura-do-repositório)
  - [Conceitos](#conceitos)
    - [Overlays por ambiente](#overlays-por-ambiente)
    - [App-of-apps](#app-of-apps)
    - [Sync waves](#sync-waves)
  - [Pré-requisitos](#pré-requisitos)
  - [Bootstrap / Deploy](#bootstrap--deploy)
  - [Segurança: secrets \& acessos](#segurança-secrets--acessos)
  - [Padrões de contribuição](#padrões-de-contribuição)
  - [Referências por componente](#referências-por-componente)

---

## Estrutura do repositório

```text
.
├── airflow/        # README e manifests do Airflow
├── app-of-apps/    # Chart que gera os Applications filhos
├── argocd/         # Instalação do Argo CD + entrypoints (preprod/prod)
├── assets/         # imagens/diagramas
├── jupyterhub/     # README e manifests do JupyterHub
├── minio/          # README e manifests do MinIO (+ overlay prod)
├── postgres/       # README e manifests do Postgres
├── superset/       # README e manifests do Superset
└── README.md       # (este arquivo)
````

Cada pasta possui um **README próprio** com detalhes de setup, pré-requisitos específicos e exemplos.

---

## Conceitos

### Overlays por ambiente

* Arquivos `values.*.yaml` **sobrescrevem apenas** o que muda por ambiente (ex.: `values.prod.yaml`, `values.preprod.yaml`).
* O merge é **por chave** (deep-merge). O que não está no overlay é **herdado** do base.

### App-of-apps

* Um `Application` **raiz** gera/aplica os `Applications` **filhos** (Airflow, MinIO, Postgres, etc.).
* Cada filho pode usar Helm, Kustomize ou plugin (`kustomized-helm`).
* A ordem de bootstrap é definida por **sync waves**.

### Sync waves

* Usamos a anotação `argocd.argoproj.io/sync-wave: "<N>"` para ordenar a aplicação.
* Regra geral:

  * **Infra base/dependências**: waves negativas (ex.: DB/obj storage)
  * **Orquestrador**: `0` (ex.: Airflow)
  * **Visualização/serviços finais**: `1+` (ex.: Superset/JupyterHub)

---

## Pré-requisitos

* Acesso ao **cluster Kubernetes** (kubeconfig).
* **kubectl**, **helm** e (opcional) **argocd CLI** instalados.
* Acesso à **VPN** quando exigido pelo ambiente.
* Secrets exigidos por cada app criados **antes** do deploy (ver README de cada componente).

---

## Bootstrap / Deploy

O fluxo padrão é **declarativo** via Argo CD:

1. **Argo CD**: instale/sincronize conforme `argocd/README.md` (usa `values.yaml` + overlay do ambiente).
2. **App-of-apps**: o `application.<env>.yaml` cria o Application raiz; ao sincronizar, ele gera/aplica os filhos conforme `app-of-apps/values.<env>.yaml`.
3. **Waves** garantem a ordem (ex.: Postgres/MinIO → Airflow → Superset/JupyterHub).

> Para **testes** pontuais, cada componente expõe um comando de **renderização/aplicação manual** (`kubectl kustomize ... | kubectl apply -f - -n <ns>`). Em produção, evite aplicar manualmente para não criar **drift**.

---

## Segurança: secrets & acessos

* **Nunca** commitar credenciais no repositório.
* Criar secrets via `kubectl -n <ns> apply -f - <<'EOF' ... EOF` ou usar gerenciadores (Sealed/External Secrets, se adotados).
* Certificados e chaves (ex.: **SIAFI/SIAPE**) são **críticos**. Os nomes das secrets e chaves esperadas constam nos READMEs de **Airflow** e **JupyterHub**.
* Acesso a painéis/DBs é tratado **por ambiente**; procure a equipe de infra para endpoints e credenciais.

---

## Padrões de contribuição

* **Branches**: prefira prefixos `feat/`, `fix/`, `refactor/`, `docs/`.
* **Commits**: **Conventional Commits** (ex.: `feat(argocd): ...`, `docs(airflow): ...`).
* **MR/PR**: descreva o *porquê* e liste mudanças relevantes (paths/values alterados).
* **Rebase** da branch com `main` antes de abrir o MR:

  ```bash
  git fetch origin
  git rebase origin/main
  git push --force-with-lease
  ```

---

## Referências por componente

* **Argo CD**: [`argocd/README.md`](./argocd/README.md)
* **App-of-apps**: [`app-of-apps/README.md`](./app-of-apps/README.md)
* **Airflow**: [`airflow/README.md`](./airflow/README.md)
* **MinIO**: [`minio/README.md`](./minio/README.md)
* **Postgres**: [`postgres/README.md`](./postgres/README.md)
* **Superset**: [`superset/README.md`](./superset/README.md)
* **JupyterHub**: [`jupyterhub/README.md`](./jupyterhub/README.md)
