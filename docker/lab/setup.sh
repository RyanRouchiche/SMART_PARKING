#!/bin/sh
set -e
cd "$(dirname "$0")"
mkdir -p generated/hub generated/site1

keypair() {
  MSYS_NO_PATHCONV=1 docker run --rm alpine:3.20 sh -c 'apk add -q wireguard-tools >/dev/null && k=$(wg genkey) && echo "$k $(echo "$k" | wg pubkey)"'
}

set -- $(keypair); HUB_PRIV=$1; HUB_PUB=$2
set -- $(keypair); SITE_PRIV=$1; SITE_PUB=$2

cat > generated/hub/wg0.conf <<EOF
[Interface]
Address = 10.200.0.1/16
ListenPort = 51820
PrivateKey = $HUB_PRIV

[Peer]
PublicKey = $SITE_PUB
AllowedIPs = 10.200.1.1/32, 10.100.1.0/24
EOF

cat > generated/site1/wg0.conf <<EOF
[Interface]
Address = 10.200.1.1/16
PrivateKey = $SITE_PRIV

[Peer]
PublicKey = $HUB_PUB
Endpoint = hub:51820
AllowedIPs = 10.200.0.1/32
PersistentKeepalive = 25
EOF

chmod 600 generated/hub/wg0.conf generated/site1/wg0.conf
echo "Keys generated in docker/lab/generated (ignored by git)."
