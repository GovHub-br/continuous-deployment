
argocd
===========

# Ambiente de homologação

Instalação do Argo CD em um cluster Kubernetes a partir do Helm/Kustomize. Necessário para usar o app of apps e para instalar o Airflow com Kustomize.

- [CRDs](#crds)
- [Secrets](#secrets)
- [Setup](#setup)

## CRDs

As CRDs já são instaladas junto com o chart.

> :warning: Muito cuidado ao atualizar CRDs. Caso as CRDs sejam deletadas, serão deletados todos os recursos — cujo campo "kind" for a CRD — de todos os namespaces do cluster Kubernetes.

## Secrets

Criar namespace onde a ferramenta será instalada. Pular etapa caso namespace já exista.

```bash
kubectl create namespace argocd
```

Configurar acesso a um repositório do GitLab com 'Personal Access Tokens'. Antes, é necessário criar um 'personal access token' com a permissão 'read_repository' no GitLab. Então, substitua os valores dos campos `metadata.name`, `stringData.url` e `stringData.password`. Lembrar de usar o final '.git' no campo `stringData.url`.

```
kubectl -n argocd apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: gitlab-lappis-unb-decidimbr-infra-continuous-deployment
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  url: https://gitlab.com/lappis-unb/decidimbr/infra/continuous-deployment.git
  username: nonexistant
  password: glpat-SJdjaknsdjnakJ
EOF
```

Obs: o token 'glpat-SJdjaknsdjnakJ' é só um exemplo, não funciona.

## Setup

Criar namespace onde a ferramenta será instalada. Pular etapa caso namespace já exista.

```bash
kubectl create namespace argocd
```

Clonar este repositório.

```bash
git clone git@gitlab.com:lappis-unb/decidimbr/infra/continuous-deployment.git
```

Navegar até a pasta continuous-deployment/argocd.

```bash
cd continuous-deployment
cd argocd
```

Inflar o Helm chart com o Kustomize.

```bash
kubectl kustomize . --enable-helm --load-restrictor LoadRestrictionsNone
```

Dar permissão para execução do script './helm_post_renderer.sh'.

```bash
chmod +x ./helm_post_renderer.sh
```

Instalar com Helm.

```bash
helm upgrade --install \
  argocd ./charts/argo-cd --namespace argocd \
  --post-renderer ./helm_post_renderer.sh
```

# Ambiente de produção

Para instalar o argocd na infraestrutura de produção é preciso entrar no shell do ambiente e rodar os seguintes comandos

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create ns argocd
# para instalar o argo em si
helm -n argocd install argocd argo/argo-cd --version 6.4.1 \
    -f https://gitlab.com/lappis-unb/gest-odadosipea/infra-lappis-ipea/-/raw/main/argocd/values.yaml \
    -f https://gitlab.com/lappis-unb/gest-odadosipea/infra-lappis-ipea/-/raw/main/argocd/values.prod.yaml
# para criar o app of apps
kubectl -n argocd apply \ 
    -f https://gitlab.com/lappis-unb/gest-odadosipea/infra-lappis-ipea/-/raw/main/argocd/application.prod.yaml
```

Para atualizar basta trocar o comando de `install` por `upgrade` e para desinstalar é `helm -n argocd uninstall argocd`

Obs.: Para a instalação funcionar é necessário acesso global no cluster para aplicar os CRDs do argo
