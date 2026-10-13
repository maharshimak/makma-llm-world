"""Untrusted retrieval code runs here, never on the host. Labels stay outside."""
import contextlib
import json
import random
import sys

payload=json.loads(sys.stdin.read(2_000_001))
random.seed(payload["seed"])
namespace={}
with contextlib.redirect_stdout(sys.stderr):
    exec(compile(payload["code"],"candidate.py","exec"),namespace)
    rankings=namespace["retrieve"](payload["documents"],payload["queries"],payload["k"])
print(json.dumps({"rankings":rankings},allow_nan=False))

