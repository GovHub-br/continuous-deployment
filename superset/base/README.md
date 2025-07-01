superset
===========

## Secrets

### Secret Key

Execute:

```
openssl rand -base64 42
```

exemplo de saida

``` 
WnsoGvMXoyRYyA/dDtfY7Qmxfjx/M5hETAkUPZyvC6TJpdhoeZa3vwUN
```

Criando a secrets no k8s, substitua pela secret gerada

``` 
kubectl create secret generic superset-secret-key --from-literal=SUPERSET_SECRET_KEY='WnsoGvMXoyRYyA/dDtfY7Qmxfjx/M5hETAkUPZyvC6TJpdhoeZa3vwUN' \  -n <seu-namespace>
```

### Acesso ao Redis e ao Postgres

Substituir expressões que comecem com "SUBSTITUIR_"

```
kubectl -n superset apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: custom-superset-env
type: Opaque
stringData:
  DB_HOST: SUBSTITUIR_POR_HOST
  DB_NAME: SUBSTITUIR_POR_DATABASE
  DB_PASS: SUBSTITUIR_POR_SENHA
  DB_PORT: SUBSTITUIR_POR_PORTA
  DB_USER: SUBSTITUIR_POR_USUARIO_DA_DATABASE
  REDIS_CELERY_DB: '0'
  REDIS_DB: '1'
  REDIS_HOST: superset-redis-headless
  REDIS_PORT: '6379'
  REDIS_PROTO: redis
  REDIS_USER: ''
EOF
```
