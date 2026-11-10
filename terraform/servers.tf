# TODO 1: an aws_key_pair "lab" from the public key file (file(var.public_key_path)).
#         Name it "handoff-key".
#
# TODO 2: two security groups in the VPC from main.tf
#   "web": port 80 from anywhere, port 22 from var.my_ip_cidr only, all traffic out
#   "app": port 8000 ONLY from the web security group (security_groups = [...], not a CIDR),
#          port 22 from var.my_ip_cidr only, all traffic out
#   Use the newer rule style or inline blocks, as you prefer.
#
# TODO 3: ONE aws_instance resource with for_each over a local map that has two entries:
#   web and app. Both: Ubuntu AMI from data.aws_ssm_parameter.ubuntu.value, t3.micro,
#   the public subnet, the key pair, the right security group for the role,
#   IMDSv2 required (metadata_options { http_tokens = "required" }).
#   Tags: Name = "pollie-<role>"  and  Role = "<role>"   (the lab tag comes for free from the provider)
#   The inventory in part 2 will build its groups from those two tags.
#
# TODO 4: outputs: "web_url" (http://<public ip of web>) and "ssh_hint" (a ready ssh command for the web server).
