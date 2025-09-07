# App of Apps

Helm chart que **renderiza múltiplos `Applications` do Argo CD** a partir de um único arquivo de valores.  
Cada item em `values.yaml` (ou overlay) gera **um `Application` filho** com configurações herdadas de `global` e sobrescritas por app.

> Objetivo: padronizar criação/ordem de instalação (via **sync waves**) e facilitar overlays por ambiente.

---

## Sumário

- [App of Apps](#app-of-apps)
  - [Sumário](#sumário)
  - [Estrutura do diretório](#estrutura-do-diretório)
  - [Como funciona](#como-funciona)
    - [Template](#template)
    - [Waves (ordem de sync)](#waves-ordem-de-sync)
    - [Helm x `kustomized-helm`](#helm-x-kustomized-helm)
  - [Valores (schema)](#valores-schema)
    - [Global](#global)
    - [Aplicações](#aplicações)
    - [Overlays (preprod/prod)](#overlays-preprodprod)
  - [Fluxo de deploy](#fluxo-de-deploy)
  - [Testes locais (opcional)](#testes-locais-opcional)
  - [Como adicionar um novo app](#como-adicionar-um-novo-app)
  - [Dicas e troubleshooting](#dicas-e-troubleshooting)

---

## Estrutura do diretório

```text
app-of-apps/
├── Chart.yaml
├── templates/
│   ├── applications.yaml     # gera N Applications a partir de argocdApplications
│   └── _helpers.tpl
├── values.yaml               # base
├── values.preprod.yaml       # overlay homolog/preprod
└── values.prod.yaml          # overlay produção
````

---

## Como funciona

### Template

* Para **cada** entrada em `.Values.argocdApplications`, o template gera um `argoproj.io/Application`.
* Campos comuns (**repoURL**, **targetRevision**, **project**, **destination**) vêm de `.Values.global.*` e podem ser **sobrescritos por app**.
* O template já define:

  * `syncPolicy.automated` (a menos que `disableAutomated: true`)
  * `syncOptions` com `CreateNamespace=true` e `ApplyOutOfSyncOnly=true`
  * **Anotação** `argocd.argoproj.io/sync-wave` (se `syncWave` não existir no app, herda `global.syncWave`).

### Waves (ordem de sync)

* Use `metadata.annotations.argocd.argoproj.io/sync-wave: "<N>"` (inteiro; pode ser negativo).
* O Argo CD aplica **wave por wave** (ordem crescente) e **só avança** quando os recursos da wave atual estão `Healthy`.
* Regra prática:

  * **Dependências** (DB/obj storage/CRDs): waves **negativas** (ex.: `-5`).
  * **Orquestradores** (Airflow): `0`.
  * **Apps de visualização** (Superset/JHub): `1+`.
  * Se **dois apps não dependem** entre si, podem ficar **na mesma wave** para paralelizar.

### Helm x `kustomized-helm`

* Se `helm: true` (ou `global.helmDefault: true`), o filho usa **Helm** com `valueFiles` (herda `global.defaultValueFiles` se não especificado).
* Se `helm: false`, o filho usa **plugin** `kustomized-helm` (adequado a diretórios com Kustomize/Helm combinados via plugin no Argo CD).

---

## Valores (schema)

### Global

```yaml
global:
  helmDefault: false                  # default para apps que não definirem .helm
  defaultValueFiles:                  # arquivos de valores padrão quando .helm = true
    - values.yaml
  spec:
    project: default                  # Argo CD Project
    destination:
      server: https://kubernetes.default.svc
      name: default                   # opcional; namespace é definido por app
    source:
      repoURL: https://<repo>.git
      targetRevision: HEAD            # branch/tag/sha padrão
  syncWave: "0"                       # wave default (string) se o app não definir
```

### Aplicações

Cada chave em `argocdApplications` representa um `Application` filho:

```yaml
argocdApplications:
  airflow:
    name: airflow                     # metadata.name do Application
    namespace: airflow                # destination.namespace
    disable: false                    # se true, NÃO renderiza o Application
    disableAutomated: false           # se true, remove syncPolicy.automated
    path: airflow                     # source.path
    targetRevision: HEAD              # source.targetRevision (override do global)
    helm: false                       # true=Helm; false=plugin kustomized-helm
    valueFiles:                       # opcional, se helm=true; senão herda global
      - values.yaml
      - values.prod.yaml
    syncWave: "-5"                    # opcional; senão herda global.syncWave
```

Campos resolvidos no template:

* `spec.source.repoURL` ← `global.spec.source.repoURL`
* `spec.source.targetRevision` ← `app.targetRevision` **ou** `global.spec.source.targetRevision`
* `spec.destination.namespace` ← `app.namespace`
* `spec.project` ← `global.spec.project`

### Overlays (preprod/prod)

* `values.yaml` define a **base** compartilhada.
* `values.preprod.yaml` e `values.prod.yaml` **sobrescrevem apenas o necessário** (paths, waves, habilitar/desabilitar apps, etc.).
* **Exemplo** (prod paralelizando DB/MinIO e ordenando o resto):

  * `postgres`: `syncWave: "-5"`
  * `minio`: `syncWave: "-5"`
  * `airflow`: `syncWave: "0"`
  * `superset`: `syncWave: "1"`
  * `jupyterhub`: `syncWave: "2"` (ou desabilitado no overlay)

---

## Fluxo de deploy

Este chart é aplicado pelo **Argo CD** através do `Application` de **entrypoint** do ambiente (ver diretório `argocd/entrypoints/<env>`).

1. O **Argo CD** sincroniza o `Application` do **app-of-apps**.
2. O chart renderiza os **Applications filhos** (um por app em `argocdApplications`).
3. As waves determinam a **ordem de bootstrap** entre os filhos.
4. Cada filho aplica **seu próprio** Helm/Kustomize/plugin.

> Evite aplicar manualmente os `Applications` gerados se o Argo CD já gerencia esse estado (para não criar **drift**).

---

## Testes locais (opcional)

Para **visualizar** o que será gerado a partir de `values.yaml` + overlay:

```bash
helm template app-of-apps . \
  -f values.yaml \
  -f values.prod.yaml
```

Para **aplicar manualmente** (ex.: em um cluster de teste; namespace do Argo CD é `argocd`):

```bash
helm template app-of-apps . \
  -f values.yaml \
  -f values.prod.yaml \
| kubectl apply -n argocd -f -
```

> **Produção**: prefira o fluxo declarativo pelo Argo CD (entrypoint + sync).

---

## Como adicionar um novo app

1. Crie a pasta do app no repositório **de manifests** (Helm chart ou diretório com Kustomize/plugins).
2. Em `values.(pre)prod.yaml`, adicione um bloco em `argocdApplications`:

   * `name`, `namespace`, `path`, `helm` (true/false),
   * `valueFiles` (se Helm),
   * `syncWave` (ordem),
   * `disable` (se ainda não quiser habilitar).
3. **Opcional**: defina `targetRevision` específico (senão herda do `global`).
4. `argocd app sync <app-of-apps>` (ou sincronize o entrypoint no Argo CD UI/CLI).

---

## Dicas e troubleshooting

* **Sem ordem aparente entre apps?**
  Garanta que **cada app** tenha `syncWave` **distinto** quando houver dependência entre eles.
  Mesma wave ⇒ execução paralela **sem ordem garantida**.

* **Namespace não existe?**
  O template já passa `CreateNamespace=true`. Se ainda falhar, verifique RBAC/Policies do cluster.

* **Drift entre manual e Argo CD?**
  Evite `kubectl apply` direto em `Applications` que o Argo gerencia. Ajuste valores e **sincronize**.

* **Plugin x Helm**
  Se o diretório do app contém Kustomize/Helm híbrido exigindo o plugin do Argo CD, mantenha `helm: false` (usa `kustomized-helm`).
  Se é **chart Helm puro**, use `helm: true` e configure `valueFiles`.
