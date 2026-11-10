#!/usr/bin/env bash
# Checks your Terraform, your Ansible and the real servers. Run with: ./verify.sh
cd "$(dirname "$0")" || exit 1
for c in terraform ansible ansible-playbook ansible-inventory; do command -v "$c" >/dev/null || { echo "$c is not installed." >&2; exit 1; }; done
aws sts get-caller-identity >/dev/null 2>&1 || { echo "No working AWS credentials." >&2; exit 1; }
exec python3 .lab/handoffcheck.py
