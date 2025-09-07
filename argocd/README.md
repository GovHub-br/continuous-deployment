# Argo CD

Este diretório contém a instalação e configuração do **Argo CD** via **Helm + Kustomize**, além dos _entrypoints_ de ambiente e do **Application** raiz do **app-of-apps**.

> **Objetivo**: disponibilizar o Argo CD no cluster e, a partir dele, gerenciar as aplicações (Airflow, MinIO, Postgres, Superset, etc.) com **overlays** por ambiente e **sync waves** para ordenar o bootstrap.

---

## Sumário

- [Argo CD](#argo-cd)
  - [Sumário](#sumário)
  - [Estrutura do diretório](#estrutura-do-diretório)
  - [Conceitos rápidos](#conceitos-rápidos)
    - [Overlays](#overlays)
    - [App-of-apps](#app-of-apps)
  - [CRDs](#crds)
  - [Secrets (acesso ao repositório Git)](#secrets-acesso-ao-repositório-git)
  - [Instalação](#instalação)
    - [Produção](#produção)
  - [Operações comuns](#operações-comuns)

---

## Estrutura do diretório

```text
argocd/
├── application.prod.yaml        # Application do app-of-apps (produção)
├── entrypoints/
│   ├── preprod/entrypoint.yaml  # EntryPoint Argo CD (preprod/homolog)
│   └── prod/entrypoint.yaml     # EntryPoint Argo CD (prod)
├── helm_post_renderer.sh        # Post-renderer do Helm (ajustes pós-render)
├── kustomization.yaml           # Kustomize raiz para instalar Argo CD
├── README.md                    # Este documento
├── values.yaml                  # Valores base do chart argo/argo-cd
├── values.preprod.yaml          # Overlay (preprod)
└── values.prod.yaml             # Overlay (prod)
````

* **`kustomization.yaml`**: usa o **Helm Chart** `argo/argo-cd` com valores do `values.yaml` + overlay do ambiente.
* **`entrypoints/<env>/entrypoint.yaml`**: define o **Application** do Argo CD para aquele ambiente (quem aponta valores/overlays).
* **`application.prod.yaml`**: Application raiz do **app-of-apps** em produção (bootstrap do restante do stack).
* **`helm_post_renderer.sh`**: script chamado após o `helm template` para ajustes finos no manifesto renderizado (ex.: labels, anotações, policies).

---

## Conceitos rápidos

### Overlays

Os **overlays** são *arquivos de valores* específicos por ambiente que **sobrescrevem apenas as chaves necessárias** do `values.yaml`.

* **Base**: `values.yaml`
* **Ambiente**: `values.preprod.yaml` (homolog), `values.prod.yaml` (produção)
* **Merge**: *deep merge* por chave; o que **não** estiver no overlay é **herdado** do `values.yaml`.

Isso permite:

* Ajustar **URLs**, **replicas**, **recursos**, **flags** e **permissões** por ambiente.
* Manter uma **fonte única** de verdade no `values.yaml` + difs mínimos no overlay.

### App-of-apps

O **app-of-apps** é um padrão em que um `Application` Argo CD **raiz** (o “app-mãe”) **cria e sincroniza** outros `Applications` (os “apps-filhos”), cada um apontando para um componente (Airflow, MinIO, Postgres, Superset…).

* **Ordem** de instalação é controlada por **sync waves** (`argocd.argoproj.io/sync-wave`).
* Cada filho pode usar **Helm**, **Kustomize**, **plugins** ou uma combinação deles.
* Você gerencia **tudo** versionado no Git, e o Argo CD mantém o **estado desejado** no cluster.

> Neste repo, o `application.prod.yaml` é o **Application raiz** do app-of-apps para produção.

---

## CRDs

As **CRDs do Argo CD** são instaladas junto com o **Helm Chart**.

> ⚠️ **Cuidado ao atualizar/remover CRDs**: deletar CRDs remove **todos os recursos** daquele `kind` em **todos** os namespaces.

Permissões:

* A instalação/atualização das CRDs exige privilégios de **cluster-admin**.

---

## Secrets (acesso ao repositório Git)

Crie o **namespace** (se ainda não existir):

```bash
kubectl create namespace argocd
```

Crie um **Personal Access Token** com `read_repository` no seu Git provider (GitLab/GitHub) e **adicione o repositório** ao Argo CD via Secret:

> Substitua `REPO_URL` (terminando com `.git`) e `PERSONAL_ACCESS_TOKEN`.

```bash
kubectl -n argocd apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: repo-access
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  url: REPO_URL
  username: nonexistant
  password: PERSONAL_ACCESS_TOKEN
EOF
```

> Dica: prefira **nomes de Secret por repositório** (ex.: `repo-infra-cd`, `repo-apps`), principalmente se usar múltiplos remotos.

---

## Instalação

### Produção

> Execute **dentro** do contexto do cluster de produção (kubeconfig correto).

1. **Adicionar repositório Helm do Argo**:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create ns argocd
```

2. **Instalar o Argo CD** com overlays de produção:

```bash
helm -n argocd install argocd argo/argo-cd --version 6.4.1 \
  -f https://gitlab.com/lappis-unb/gest-odadosipea/infra-lappis-ipea/-/raw/main/argocd/values.yaml \
  -f https://gitlab.com/lappis-unb/gest-odadosipea/infra-lappis-ipea/-/raw/main/argocd/values.prod.yaml
```

3. **Criar o app-of-apps (produção)**:

```bash
kubectl -n argocd apply -f \
  https://gitlab.com/lappis-unb/gest-odadosipea/infra-lappis-ipea/-/raw/main/argocd/application.prod.yaml
```

> Para **atualizar**, troque `install` por `upgrade`.
> Para **remover**, use: `helm -n argocd uninstall argocd`.

> 🔐 É necessário acesso **global** no cluster para aplicar/atualizar as **CRDs** do Argo CD.

---

## Operações comuns

* **Atualizar chart/valores** (produção):

  ```bash
  helm -n argocd upgrade argocd argo/argo-cd \
    -f argocd/values.yaml \
    -f argocd/values.prod.yaml
  ```
* **Ver estado dos Applications** pelo CLI do Argo CD:

  ```bash
  # autentique com argocd login <host> --username <user> --password <pass>
  argocd app list
  argocd app get <nome-do-app>
  argocd app sync <nome-do-app>
  ```
* **Logs do controller**:

  ```bash
  kubectl -n argocd logs deploy/argocd-application-controller
  ```
