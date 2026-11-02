import argparse
import base64
import json
import os
import random

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

members = {
}

rng = random.SystemRandom()


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def assign():
    names = list(members)
    for _ in range(100000):
        targets = names[:]
        rng.shuffle(targets)
        if all(t != m and t != members[m]['last'] for m, t in zip(names, targets)):
            for m, t in zip(names, targets):
                members[m]['current'] = t
            return
    raise SystemExit("no valid assignment exists")


def make_link(base_url, target):
    # fresh key + nonce per person; the key rides in the URL fragment, which
    # browsers never send to the server
    key = AESGCM.generate_key(bit_length=128)
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, target.capitalize().encode(), None)
    return f"{base_url}#{b64(key)}.{b64(nonce + ct)}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("hist")
    parser.add_argument("--url", default="https://example.com/decrypt.html",
                        help="where decrypt.html is hosted")
    parser.add_argument("--out", default="links",
                        help="directory to write one link file per person")
    parser.add_argument("--save", default="assignments.new.json",
                        help="assignments for next year's history")

    args = parser.parse_args()

    with open(args.hist, "r") as fd:
        hist = json.load(fd)
    for member, assignment in hist.items():
        members[member] = { "last": assignment, "current": None }

    assign()

    os.makedirs(args.out, exist_ok=True)
    for member, info in members.items():
        with open(os.path.join(args.out, f"{member}.txt"), "w") as fd:
            fd.write(make_link(args.url, info['current']) + "\n")

    # needed next year to avoid repeats; don't open it if you want to stay surprised
    with open(args.save, "w") as fd:
        json.dump({m: i['current'] for m, i in members.items()}, fd, indent=4)

    print(f"wrote {len(members)} links to {args.out}/ (assignments not displayed)")
