#!/usr/bin/env python3
import json, os, re, subprocess, sys, time, urllib.request, urllib.error
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
passed = failed = 0
LAB = "terraform-ansible-handoff"


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""))


def aws(*a):
    try:
        return json.loads(subprocess.check_output(("aws",) + a + ("--output", "json"), stderr=subprocess.DEVNULL, timeout=60) or "null")
    except Exception:
        return None


def sh(c, env=None, timeout=900):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, env=env, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def http(url, headers=False, timeout=8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode(errors="replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, "", dict(e.headers)
    except Exception:
        return 0, "", {}


F = "Name=tag:lab,Values=" + LAB
print("== Your code ==")
tf = "\n".join(l for l in sh("cat terraform/servers.tf")[1].split("\n") if not l.lstrip().startswith("#"))
check("terraform fmt -check is clean", sh("terraform -chdir=terraform fmt -check")[0] == 0, "terraform -chdir=terraform fmt")
check("ONE aws_instance resource with for_each builds both servers", len(re.findall(r'resource\s+"aws_instance"', tf)) == 1 and "for_each" in tf)
check("IMDSv2 is required on the servers", re.search(r'http_tokens\s*=\s*"required"', tf) is not None)
inv = "\n".join(l for l in sh("cat inventory.aws_ec2.yml")[1].split("\n") if not l.lstrip().startswith("#"))
check("inventory.aws_ec2.yml uses the amazon.aws.aws_ec2 plugin and has no IP address", re.search(r"^plugin:\s*amazon\.aws\.aws_ec2", inv, re.M) is not None and re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", inv) is None)
site = "\n".join(l for l in sh("cat site.yml templates/*.j2")[1].split("\n") if not l.lstrip().startswith("#"))
check("no IP address written by hand in site.yml or the templates", re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", site) is None)
check("site.yml uses modules only (no shell, command, raw, script)", sh("python3 .lab/no_shell.py")[0] == 0)
tracked = sh("git ls-files")[1].split("\n")
check("no state file, .terraform/, tfvars or keys committed", not [f for f in tracked if re.search(r"\.tfstate|(^|/)\.terraform/|\.tfvars$|^keys/", f)])

print("== The servers in AWS ==")
res = (aws("ec2", "describe-instances", "--filters", F, "Name=instance-state-name,Values=running") or {}).get("Reservations", [])
ins = [i for r in res for i in r["Instances"]]
roles = {}
for i in ins:
    t = {x["Key"]: x["Value"] for x in i.get("Tags", [])}
    roles[t.get("Role")] = (i, t)
check("two running servers tagged lab=%s with Role web and Role app" % LAB, len(ins) == 2 and set(roles) == {"web", "app"})
if len(ins) != 2 or set(roles) != {"web", "app"}:
    print("\nNothing else can be checked without both servers.\n%d check(s) failed, %d passed" % (failed, passed)); sys.exit(1)
web, wt = roles["web"]; app, at = roles["app"]
check("the Name tags are pollie-web and pollie-app", wt.get("Name") == "pollie-web" and at.get("Name") == "pollie-app")
check("both are t3.micro with IMDSv2 required", all(i["InstanceType"] == "t3.micro" and i["MetadataOptions"]["HttpTokens"] == "required" for i in ins))
img = (aws("ec2", "describe-images", "--image-ids", web["ImageId"]) or {}).get("Images", [{}])[0]
check("the image is Ubuntu 24.04", "ubuntu-noble-24.04" in img.get("Name", "") or "24.04" in img.get("Name", ""))
sgs = {s["GroupId"]: s for s in (aws("ec2", "describe-security-groups", "--group-ids", *[g["GroupId"] for i in ins for g in i["SecurityGroups"]]) or {}).get("SecurityGroups", [])}
def rules(i):
    out = []
    for g in i["SecurityGroups"]:
        out += sgs.get(g["GroupId"], {}).get("IpPermissions", [])
    return out
wsg = {g["GroupId"] for g in web["SecurityGroups"]}
ar = rules(app); wr = rules(web)
def cidrs(rl, port):
    return [c["CidrIp"] for p in rl if p.get("FromPort") == port for c in p.get("IpRanges", [])]
check("SSH is open to exactly one /32 on both servers, never to the world", all(len(cidrs(r, 22)) == 1 and cidrs(r, 22)[0].endswith("/32") for r in (ar, wr)))
check("the web server accepts port 80 from the world", "0.0.0.0/0" in cidrs(wr, 80))
a8000 = [p for p in ar if p.get("FromPort") == 8000]
check("the app server accepts port 8000 from the web server's security group only (no CIDR)", len(a8000) == 1 and not a8000[0].get("IpRanges") and {p["GroupId"] for p in a8000[0].get("UserIdGroupPairs", [])} == wsg)
check("the app server has nothing open to the internet except what SSH allows", "0.0.0.0/0" not in cidrs(ar, 22) and not any("0.0.0.0/0" in [c["CidrIp"] for c in p.get("IpRanges", [])] for p in ar))
kp = (aws("ec2", "describe-key-pairs", "--filters", F) or {}).get("KeyPairs", [])
check("a key pair tagged lab=%s exists and both servers use it" % LAB, len(kp) == 1 and all(i.get("KeyName") == kp[0]["KeyName"] for i in ins))

print("== Terraform ==")
cidr = (cidrs(wr, 22) or ["203.0.113.1/32"])[0]
env = dict(os.environ, TF_VAR_my_ip_cidr=cidr)
rc, out = sh("terraform -chdir=terraform plan -detailed-exitcode -input=false -no-color", env=env)
check("terraform plan finds nothing to change (the code and AWS agree)", rc == 0, "plan exit code %d" % rc)
wip = web.get("PublicIpAddress")
check("terraform output web_url prints the web server's address", sh("terraform -chdir=terraform output -raw web_url")[1].strip().rstrip("/") == "http://%s" % wip)
check("terraform output ssh_hint exists", sh("terraform -chdir=terraform output -raw ssh_hint")[0] == 0)

print("== Ansible ==")
rc, out = sh("ansible-inventory --list 2>/dev/null")
try:
    invj = json.loads(out[out.index("{"):])
except Exception:
    invj = {}
check("the dynamic inventory lists groups role_web and role_app with one host each", len(invj.get("role_web", {}).get("hosts", [])) == 1 and len(invj.get("role_app", {}).get("hosts", [])) == 1, "ansible-inventory --graph")
hv = invj.get("_meta", {}).get("hostvars", {})
def plain(v):
    return v.get("__ansible_unsafe") if isinstance(v, dict) else v
for _h in hv.values():
    for _k in list(_h):
        _h[_k] = plain(_h[_k])
check("the inventory host names are pollie-web and pollie-app", "pollie-web" in hv and "pollie-app" in hv)
check("the inventory reaches the servers on their public IPs", hv.get("pollie-web", {}).get("ansible_host") == wip and hv.get("pollie-app", {}).get("ansible_host") == app.get("PublicIpAddress"))
n = 0
while True:
    rc, out = sh("ansible all -m ping", timeout=120)
    if rc == 0 or n >= 12:
        break
    n += 1; time.sleep(10)
check("ansible all -m ping reaches both servers", rc == 0, "the servers boot in about a minute; SSH rule and key?")
rc, out = sh("ansible-playbook site.yml", timeout=900)
m = re.findall(r"^(\S+)\s*:\s*ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)", out, re.M)
check("ansible-playbook site.yml runs without failures on both servers", rc == 0 and len(m) == 2 and all(x[3] == "0" and x[4] == "0" for x in m), out[-400:] if rc else "")
rc, out = sh("ansible-playbook site.yml", timeout=900)
m = re.findall(r"^(\S+)\s*:\s*ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)", out, re.M)
check("a second run changes nothing (changed=0 on both servers: idempotent)", rc == 0 and len(m) == 2 and all(x[2] == "0" for x in m), "changed: " + ", ".join("%s=%s" % (x[0], x[2]) for x in m))

print("== Live ==")
st, body, hd = 0, "", {}
for _ in range(12):
    st, body, hd = http("http://%s/" % wip)
    if st == 200:
        break
    time.sleep(5)
check("GET http://<web>/ serves Pollie's web site", st == 200 and "pollie" in body.lower())
check("the response carries X-Served-By: pollie-web", hd.get("X-Served-By") == "pollie-web")
st, body, _ = http("http://%s/api/status" % wip)
try:
    js = json.loads(body)
except Exception:
    js = {}
check("GET /api/status goes through Nginx to the app server and returns JSON", st == 200 and isinstance(js, dict) and js.get("server") == "pollie-app" and js.get("role") == "app" and js.get("managed_by") == "ansible", "got %s %s" % (st, body[:80]))
check("the JSON carries the app server's real private IP (it came from the inventory, not from a typed value)", js.get("private_ip") == app.get("PrivateIpAddress"))
st, _, _ = http("http://%s:8000/status" % app.get("PublicIpAddress"), timeout=5)
check("the app server's port 8000 is NOT reachable from the internet", st == 0)
rc, out = sh("ansible role_app -b -m command -a 'systemctl is-enabled pollie-status'")
check("the status service is enabled at boot", rc == 0 and "enabled" in out)

print()
print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
sys.exit(1 if failed else 0)
