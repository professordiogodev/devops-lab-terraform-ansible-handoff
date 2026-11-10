#!/usr/bin/env bash
# Proves the lab left nothing in AWS. Run with: ./verify-teardown.sh
set -u
ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) || { echo "No working AWS credentials." >&2; exit 1; }
echo "Checking account $ACCOUNT, region $(aws configure get region)"
pass=0; failn=0
check() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS  $d"; pass=$((pass+1)); else echo "FAIL  $d"; failn=$((failn+1)); fi; }
empty() { local r; r=$(eval "$1" 2>/dev/null); [ -z "$r" ] || [ "$r" = None ]; }
T="Name=tag:lab,Values=terraform-ansible-handoff"
check "no running EC2 instance tagged lab=terraform-ansible-handoff" empty "aws ec2 describe-instances --filters $T Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[].Instances[].InstanceId' --output text"
check "no VPC tagged lab=terraform-ansible-handoff" empty "aws ec2 describe-vpcs --filters $T --query 'Vpcs[].VpcId' --output text"
check "no internet gateway tagged lab=terraform-ansible-handoff" empty "aws ec2 describe-internet-gateways --filters $T --query 'InternetGateways[].InternetGatewayId' --output text"
check "no security group tagged lab=terraform-ansible-handoff" empty "aws ec2 describe-security-groups --filters $T --query 'SecurityGroups[].GroupId' --output text"
check "no key pair tagged lab=terraform-ansible-handoff" empty "aws ec2 describe-key-pairs --filters $T --query 'KeyPairs[].KeyName' --output text"
check "no Elastic IP tagged lab=terraform-ansible-handoff" empty "aws ec2 describe-addresses --filters $T --query 'Addresses[].PublicIp' --output text"
check "the lab SSH key and the cloned Pollie source are gone from this folder" bash -c '[ ! -d keys ] && [ ! -d pollie ]'
echo
if [ "$failn" -eq 0 ]; then echo "TEARDOWN VERIFIED ($pass/$pass) in account $ACCOUNT"; else echo "NOT CLEAN: $failn leftover(s). Remove them and run this again."; fi
exit "$failn"
