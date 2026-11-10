#!/usr/bin/env bash
rc=0
ls terraform/*.tf >/dev/null 2>&1 && echo "- ✅ terraform/ has .tf files" || { echo "- ❌ terraform/ has no .tf files"; rc=1; }
grep -q 'aws_instance' terraform/servers.tf && echo "- ✅ the servers are in servers.tf" || { echo "- ❌ no aws_instance in terraform/servers.tf"; rc=1; }
grep -qE '^plugin: *amazon.aws.aws_ec2' inventory.aws_ec2.yml && echo "- ✅ dynamic inventory (amazon.aws.aws_ec2)" || { echo "- ❌ inventory.aws_ec2.yml does not use the amazon.aws.aws_ec2 plugin"; rc=1; }
if git ls-files | grep -qE '\.tfstate|\.terraform/|\.tfvars$|^keys/'; then echo "- ❌ state, .terraform/, tfvars or keys/ is committed"; rc=1; else echo "- ✅ no state, tfvars or keys committed"; fi
grep -rEq 'AKIA[0-9A-Z]{16}' . --exclude-dir=.git --exclude=handoffcheck.py && { echo "- ❌ an AWS access key is committed"; rc=1; } || echo "- ✅ no AWS access key committed"
grep -qE '^ALL CHECKS PASSED \(' SUBMISSION.md && echo "- ✅ SUBMISSION.md shows ALL CHECKS PASSED" || { echo "- ❌ paste the verify.sh output ('ALL CHECKS PASSED') into SUBMISSION.md"; rc=1; }
exit $rc
