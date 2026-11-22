"""Oddiy .env o'qigich (qo'shimcha kutubxonasiz). Tizim o'zgaruvchilari .env dan ustun turadi."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env(path=None):
    path = path or os.path.join(HERE, ".env")
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:]
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            elif " #" in val:
                val = val.split(" #", 1)[0].strip()
            if key and val:
                os.environ.setdefault(key, val)
    return True
