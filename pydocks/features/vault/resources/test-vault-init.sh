#!/usr/bin/env sh
set -e

# Start Vault in dev mode (auto-unsealed; no manual unseal required).
vault server -dev -dev-listen-address="0.0.0.0:8200" | tee /tmp/vault.log &

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN="00000000-0000-0000-0000-000000000000"

until vault status >/dev/null 2>&1; do
  sleep 0.2
done

vault auth enable approle

vault write auth/approle/role/my-app-role \
  secret_id_ttl=10m \
  token_num_uses=10 \
  token_ttl=20m \
  token_max_ttl=30m \
  secret_id_num_uses=40

vault policy write my-app-policy - <<EOF
path "secret/data/test" {
    capabilities = ["read", "list"]
}
path "secret/metadata/test" {
    capabilities = ["read", "list"]
}
EOF

vault write auth/approle/role/my-app-role policies=my-app-policy

ROLE_ID=$(vault read -field=role_id auth/approle/role/my-app-role/role-id)
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/my-app-role/secret-id)

echo "ROLE_ID=${ROLE_ID}" > /vault-credentials.env
echo "SECRET_ID=${SECRET_ID}" >> /vault-credentials.env

echo "YES" > /started
sleep 10000
