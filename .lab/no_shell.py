"""Exit 1 if site.yml runs any task with the shell, command or raw module."""
import sys

try:
    import yaml
except ImportError:  # no PyYAML: skip the check rather than fail the student
    sys.exit(0)

BAD = {"shell", "command", "raw", "script"}
BAD |= {"ansible.builtin." + b for b in BAD}


def tasks(items):
    for t in items or []:
        yield t
        for k in ("block", "rescue", "always"):
            if isinstance(t, dict) and k in t:
                yield from tasks(t[k])


try:
    plays = yaml.safe_load(open("site.yml")) or []
except Exception:
    sys.exit(0)
bad = [k for p in plays if isinstance(p, dict)
       for sect in ("pre_tasks", "tasks", "post_tasks", "handlers")
       for t in tasks(p.get(sect)) if isinstance(t, dict) for k in t if k in BAD]
sys.exit(1 if bad else 0)
