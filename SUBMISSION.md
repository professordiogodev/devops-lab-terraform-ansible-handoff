# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `terraform/servers.tf`: key pair, security groups, the two servers and the outputs (the network in `main.tf` is provided)
- [ ] `inventory.aws_ec2.yml`: the dynamic inventory
- [ ] `ansible.cfg`, `site.yml` and the templates in `templates/`

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Paste `terraform output` and `ansible-inventory --graph`. Nobody typed an IP address into the inventory: where does Ansible get its list of servers, and which tags make the groups?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. Show the security group rules of the two servers. Why is port 8000 of the app server open to the web server's security group and not to a CIDR? What happens to that rule when the web server is replaced?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Paste the `PLAY RECAP` of your first run and of the second. Why must the second say `changed=0`? Which of your tasks would have broken that?

**Your answer:**

<!-- replace this line with your answer -->

### Q4. The Nginx template needs the private IP of the app server. Paste the line and say where that value comes from (Terraform, AWS, Ansible?) and what happens to it when the app server is rebuilt.

**Your answer:**

<!-- replace this line with your answer -->

### Q5. Replace the app server (`terraform apply -replace=...`), run the playbook again and `curl` the web server's `/api/status`. Paste both. What did you have to edit by hand? If the answer is "nothing", which two design choices made that true?

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Your SSH rule allows one /32. You come back tomorrow from another network. What fails first, Terraform or Ansible, and how do you fix it without opening SSH to the world?

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
