# Superset Guest Token Issuer (mini)

Serviço **minimalista** em FastAPI que emite **Guest Tokens** do Superset para **embed de dashboards** com o SDK (`@superset-ui/embedded-sdk`).

> Por que existe?
> O Superset não recomenda gerar o token no front-end. Este serviço roda no **backend**, autentica no Superset e retorna um **JWT** de convidado (curta duração) válido para um **dashboard específico** (UUID passado via querystring).

---

## Como funciona

Fluxo de cada requisição a `GET /guest-token?dash=<UUID>`:

1. Faz **login** no Superset → recebe `access_token`.
2. Busca **CSRF token** (cookie fica guardado no client HTTP).
3. Chama `POST /api/v1/security/guest_token/` passando `resources=[{ type: "dashboard", id: <UUID> }]`.
4. Retorna `{ "token": "<JWT>" }`.

Esse JWT é usado pelo front:

```js
import { embedDashboard } from "@superset-ui/embedded-sdk";

embedDashboard({
  id: "<DASHBOARD-UUID>",
  supersetDomain: "https://superset.lappis.ipea.gov.br",
  mountPoint: document.getElementById("mount"),
  fetchGuestToken: async () => (await fetch(`/guest-token?dash=<UUID>`)).json().then(r => r.token),
  dashboardUiConfig: { hideTitle: true, hideChartControls: true },
});
```

---

## Variáveis de ambiente

| VAR            | Obrigatória | Default                               | Descrição                                                                                                       |
| -------------- | ----------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `SUP_URL`      | ✅           | `https://superset.lappis.ipea.gov.br` | Base URL do Superset.                                                                                           |
| `SUP_USERNAME` | ✅           | `admin`                               | Usuário para login no Superset (ideal: uma conta **de serviço** com permissão mínima para emitir guest tokens). |
| `SUP_PASSWORD` | ✅           | *(vazio)*                             | Senha do usuário acima.                                                                                         |
| `VERIFY_TLS`   | opcional    | `true`                                | Use `false` para ignorar TLS self-signed em ambientes de teste.                                                 |

> ⚠️ No Superset, garanta:
>
> * `ENABLE_GUEST_TOKEN = True`
> * CSP libera o host que hospeda seu front (`frame-ancestors`)
> * O **Embed** do dashboard (no UI) permite o domínio que hospeda o **iframe** (pode ser `*` em teste)

---

## Endpoints

* `GET /guest-token?dash=<UUID>&username=<opcional>`

  * Retorna `{ "token": "<JWT>" }`
  * `dash` é **obrigatório**. `username` default = `viewer-app`.
* `GET /health` → `{ "ok": true }`

---

## Publicação automática no GHCR (CI)

Há um workflow em `.github/workflows/embed-superset-image.yml` que:

* **Só dispara** em pushes na `main` **se** mudarem:

  * `embed-superset/docker/Dockerfile`
  * `embed-superset/docker/main.py`
  * (opcional) `requirements.txt` — basta adicionar no `paths` do workflow
* Faz login no **GHCR** usando `GITHUB_TOKEN`
* Builda e **push** as tags:

  * `ghcr.io/<org>/embed-superset:latest`
  * `ghcr.io/<org>/embed-superset:<commit-sha>`
