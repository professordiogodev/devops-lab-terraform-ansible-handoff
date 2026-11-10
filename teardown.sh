#!/usr/bin/env bash
# Destroys everything this lab created. Run with: ./teardown.sh
set -u
cd "$(dirname "$0")" || exit 1
aws sts get-caller-identity >/dev/null 2>&1 || { echo "No working AWS credentials." >&2; exit 1; }
if [ -d terraform ] && [ -d terraform/.terraform ]; then
  # destroy does not care about the value of the variable, it only needs one
  ( cd terraform && terraform destroy -auto-approve -input=false -var "my_ip_cidr=203.0.113.1/32" ) || { echo "terraform destroy failed. Read the error, fix it and run ./teardown.sh again." >&2; exit 1; }
fi
rm -rf terraform/.terraform terraform/terraform.tfstate* terraform/.terraform.lock.hcl keys pollie .ansible
echo "Now run ./verify-teardown.sh"
