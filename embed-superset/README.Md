# Embed Superset – emissor de Guest Token (FastAPI)

Backend mínimo que **gera tokens de convidado** do Apache Superset para **embedar dashboards/charts** via SDK (`@superset-ui/embedded-sdk`) com segurança.

> Por que isso existe?
> O guest token **deve** ser emitido no **servidor** (nunca no browser). Este serviço autentica no Superset e retorna o token pronto para o front-end.

## Arquivos

```
embed-superset/
├── argocd.yaml        # (opcional) Application do Argo CD
├── deployment.yaml    # Deployment (usa imagem ghcr.io/govhub-br/embed-superset)
├── secrets.yaml       # Secret com SUP_URL/USER/PASS
├── service.yaml       # Service (NodePort) para expor a API
└── README.md          # este arquivo
```

## Variáveis (no `secrets.yaml`)

Edite **antes de aplicar**:

* `SUP_URL` – URL do Superset (ex.: `https://superset.seu.gov.br`)
* `SUP_USERNAME` – usuário do Superset (ideal: conta de serviço com permissão de emitir guest token)
* `SUP_PASSWORD` – senha
* `VERIFY_TLS` – `true` (padrão). Use `false` apenas se o Superset tiver TLS interno inválido.

> O `secrets.yaml` usa `stringData:` — não precisa base64.

## Deploy (kubectl “puro”)

```bash
# namespace (se quiser outro, ajuste nos manifests)
kubectl create ns embed-superset

kubectl -n embed-superset apply -f embed-superset/secrets.yaml
kubectl -n embed-superset apply -f embed-superset/deployment.yaml
kubectl -n embed-superset apply -f embed-superset/service.yaml

kubectl -n embed-superset get pods,svc
```

O `service.yaml` publica via **NodePort** (porta externa definida no YAML).
Exemplo de teste:

```bash
# healthcheck
curl "http://<NODE_IP>:<NODE_PORT>/health"

# emitir guest token (UUID do dashboard)
curl "http://<NODE_IP>:<NODE_PORT>/guest-token?dash=<DASH_UUID>"
```

## Deploy via Argo CD (opcional)

Aplique `argocd.yaml` **ou** inclua-o no seu *App-of-Apps*:

```bash
kubectl -n argocd apply -f embed-superset/argocd.yaml
```

> Se preferir *App-of-Apps*: adicione um filho apontando para `embed-superset/` no repositório, semelhante a outros componentes.

## Como o front usa isso

Exemplo mínimo no browser (renova token a cada 4 min):

```html
<script src="https://unpkg.com/@superset-ui/embedded-sdk"></script>
<div id="mount" style="position:fixed;inset:0"></div>
<script>
  const SUPERSET_DOMAIN = "https://superset.seu.gov.br";
  const EMBED_ID = "<UUID_DO_DASH>";
  const TOKEN_API = "http://<NODE_IP>:<NODE_PORT>/guest-token?dash=" + EMBED_ID;

  async function getToken() {
    const r = await fetch(TOKEN_API, { cache: "no-store" });
    if (!r.ok) throw new Error("token api " + r.status);
    const { token } = await r.json();
    return token;
  }

  window.supersetEmbeddedSdk.embedDashboard({
    id: EMBED_ID,
    supersetDomain: SUPERSET_DOMAIN,
    mountPoint: document.getElementById("mount"),
    fetchGuestToken: getToken,
    dashboardUiConfig: { hideTitle: true, hideChartControls: true },
  });

  setInterval(() => getToken().catch(console.warn), 4 * 60 * 1000);
</script>
```

> **CORS**: o backend já responde com `Access-Control-Allow-Origin: *`. Ajuste no código se precisar restringir.
