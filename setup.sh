#!/usr/bin/env bash
# Prepares your machine for the lab. Run:  ./setup.sh   (creates nothing in AWS)
set -u
cd "$(dirname "$0")"
bad=0
for c in aws terraform ansible ansible-inventory git ssh-keygen curl; do
  command -v "$c" >/dev/null || { echo "MISSING: $c"; bad=1; }
done
[ "$bad" = 0 ] || { echo "Install what is missing and run ./setup.sh again."; exit 1; }
aws sts get-caller-identity >/dev/null 2>&1 || { echo "No working AWS credentials (aws sts get-caller-identity failed)."; exit 1; }

# The inventory plugin runs inside Ansible's own Python. It needs boto3 there.
APY=$(ansible --version | sed -n 's/.*(\(\/[^)]*python[^)]*\)).*/\1/p' | head -1)
if [ -n "$APY" ] && ! "$APY" -c 'import boto3, botocore' 2>/dev/null; then
  echo "boto3 is missing in Ansible's Python ($APY)."
  echo "  pipx:      pipx inject ansible-core boto3 botocore   (or: pipx inject ansible boto3 botocore)"
  echo "  Homebrew:  $APY -m pip install boto3"
  exit 1
fi
ansible-doc -t inventory amazon.aws.aws_ec2 >/dev/null 2>&1 || {
  echo "The amazon.aws collection is missing:  ansible-galaxy collection install amazon.aws"; exit 1; }

echo "Getting the Pollie web app (v0.1.1)..."
if [ ! -d pollie ]; then
  git clone -q -c advice.detachedHead=false --depth 1 --branch v0.1.1 https://github.com/professordiogodev/pollie.git pollie || { echo "could not clone pollie"; exit 1; }
fi

mkdir -p keys
[ -f keys/id_ed25519 ] || ssh-keygen -q -t ed25519 -N '' -C handoff-lab -f keys/id_ed25519
chmod 600 keys/id_ed25519

IP=$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')
[ -n "$IP" ] || { echo "could not detect your public IP"; exit 1; }
printf 'my_ip_cidr = "%s/32"\n' "$IP" > terraform/terraform.tfvars

cat <<TXT

Ready. Account $(aws sts get-caller-identity --query Account --output text), region $(aws configure get region || echo us-east-1).
  SSH key:         keys/id_ed25519 (the servers will accept only this key)
  Your public IP:  $IP  (written to terraform/terraform.tfvars, which is not committed)
  Pollie web app:  pollie/web/

If your IP changes later (new network), update terraform/terraform.tfvars and run terraform apply again.
TXT
