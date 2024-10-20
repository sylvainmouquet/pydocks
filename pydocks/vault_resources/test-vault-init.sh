#!/usr/bin/env sh

# Start vault
vault server -dev -dev-listen-address="0.0.0.0:8200" | tee /tmp/vault.log &

# Export values
export VAULT_ADDR='http://0.0.0.0:8200'
export VAULT_SKIP_VERIFY='true'

# Parse unsealed keys
key=$(grep "Unseal Key: " < /tmp/vault.log | awk -F": " '{print $2}')
vault operator unseal ${key}

export VAULT_TOKEN="00000000-0000-0000-0000-000000000000"

vault auth enable approle

vault write auth/approle/role/my-app-role \
  secret_id_ttl=10m \
  token_num_uses=10 \
  token_ttl=20m \
  token_max_ttl=30m \
  secret_id_num_uses=40


ROLE_ID=$(vault read auth/approle/role/my-app-role/role-id | grep role_id | awk -F ' ' '{print $2}')
SECRET_ID=$(vault write -f auth/approle/role/my-app-role/secret-id | grep secret_id | awk -F ' ' '{print $2}' | head -1)


vault write auth/approle/login \
  role_id=${ROLE_ID} \
  secret_id=${SECRET_ID}

sleep 10000