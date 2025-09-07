# JupyterHub

Implantação do **JupyterHub** em Kubernetes.  
Este diretório/ambiente foi pensado para ser aplicado **automaticamente** pelo **Argo CD** (app-of-apps), mas também há um modo de **aplicação manual** para testes.

- [JupyterHub](#jupyterhub)
  - [Certificados para acesso às APIs (SIAPE/SIAFI)](#certificados-para-acesso-às-apis-siapesiafi)
    - [Secret de certificado](#secret-de-certificado)
  - [Setup](#setup)

---

## Certificados para acesso às APIs (SIAPE/SIAFI)

Para que os notebooks executem **requisições às APIs do SIAPE/SIAFI** com certificado (mTLS/assinado), montamos um Secret com o **certificado** e a **chave** dentro dos pods do JupyterHub.

> ⚠️ **Crítico**: sem este certificado/chave válidos, as requisições às APIs falharão.

### Secret de certificado

Crie o Secret **`extrator-ipea-certificate`** no **namespace `jupyterhub`** contendo **`tls.crt`** (certificado) e **`tls.key`** (chave privada):

## Setup

O ArgoCD faz a implantação da aplicação automaticamente, mas caso queira fazer manualmente, segue as seguintes opções:

```bash
kubectl create namespace jupyterhub --dry-run=client -o yaml | kubectl apply -f -

# Opção 1: se você possui os arquivos 'tls.crt' e 'tls.key'
kubectl -n jupyterhub create secret tls extrator-ipea-certificate \
  --cert=tls.crt \
  --key=tls.key

# Opção 2: via YAML (cole os valores como stringData)
kubectl -n jupyterhub apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: extrator-ipea-certificate
type: kubernetes.io/tls
stringData:
  tls.crt: |
    -----BEGIN CERTIFICATE-----
    COLE_AQUI_O_CERTIFICADO_BASE64_PEM
    -----END CERTIFICATE-----
  tls.key: |
    -----BEGIN PRIVATE KEY-----
    COLE_AQUI_A_CHAVE_PRIVADA_BASE64_PEM
    -----END PRIVATE KEY-----
EOF

## Setup
Há três formas de instalação, documentadas a seguir.

### Via Helm

Clonar este repositório.

```bash
git clone https://github.com/GovHub-br/continuous-deployment.git
```

Navegar até a pasta 'continuous-deployment/jupyterhub'.

```bash
cd continuous-deployment
cd jupyterhub
```

Navegar até a pasta 'homolog' ou 'production', a depender do ambiente.

```bash
cd production
# ou
cd homolog
```

Inflar o Helm chart do jupyterhub.

```bash
kubectl kustomize . --enable-helm --load-restrictor LoadRestrictionsNone
```

Dar permissão para execução do script './helm_post_renderer.sh'.

```bash
chmod +x ./helm_post_renderer.sh
```

Instalar com Helm.

```bash
helm upgrade --install --wait \
  jupyterhub ./charts/jupyterhub --namespace jupyterhub \
  --post-renderer ./helm_post_renderer.sh
```
