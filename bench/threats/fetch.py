"""Download the threat set of threats.json from where its warriors were
published, and check each against its SHA-256.

  python3 bench/threats/fetch.py OUTDIR [--archive DIR]

OUTDIR gets NN-file.red, NN being the warrior's rank in ranking.csv. With
--archive, a local copy of our private archive (geibos/corewar-archive) is
tried first, so the set still comes together when a source has gone.
Standard library only.
"""
import argparse
import hashlib
import io
import json
import os
import sys
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "board-warriors-fetch"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def archive_index(root):
    """sha256 -> bytes of every .red in the archive: loose files and tar members."""
    found = {}
    for d, _, files in os.walk(root):
        if ".git" in d.split(os.sep):
            continue
        for f in files:
            p = os.path.join(d, f)
            if f.endswith(".red"):
                data = open(p, "rb").read()
                found[sha(data)] = data
            elif f.endswith(".tar.gz"):
                with tarfile.open(p) as t:
                    for m in t.getmembers():
                        if m.isfile() and m.name.endswith(".red"):
                            data = t.extractfile(m).read()
                            found[sha(data)] = data
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--archive", help="a clone of geibos/corewar-archive")
    a = ap.parse_args()
    doc = json.load(open(os.path.join(HERE, "threats.json")))
    os.makedirs(a.outdir, exist_ok=True)
    local = archive_index(a.archive) if a.archive else {}
    tars = {}
    bad = 0
    for w in doc["warriors"]:
        data, how = local.get(w["sha256"]), "archive"
        if data is None:
            try:
                if "url" in w:
                    data, how = get(w["url"]), w["url"]
                else:
                    if w["archive"] not in tars:
                        tars[w["archive"]] = get(w["archive"])
                    with tarfile.open(fileobj=io.BytesIO(tars[w["archive"]])) as t:
                        data = t.extractfile(w["member"]).read()
                    how = w["archive"]
            except Exception as e:  # a dead source: say which, go on
                print(f"{w['rank']:3} {w['name']}: not fetched ({e})")
                bad += 1
                continue
        if sha(data) != w["sha256"]:
            print(f"{w['rank']:3} {w['name']}: SHA-256 differs from threats.json ({how})")
            bad += 1
            continue
        with open(os.path.join(a.outdir, f"{w['rank']:02d}-{w['file']}"), "wb") as fh:
            fh.write(data)
    print(f"{len(doc['warriors']) - bad} of {len(doc['warriors'])} warriors in {a.outdir}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
