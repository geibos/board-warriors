"""Warriors against a hill: the average over random placements against every
member, the result against Позитив, and `cw hill challenge` on a copy.

  NSEEDS=32 SALT=777 python3 experiments/evalf.py HILL a.red b.red ...

HILL as for tools/field.py; cw is $CW or `cw` on PATH.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import field
from concurrent.futures import ProcessPoolExecutor
if __name__ == "__main__":
    hill = sys.argv[1]; files = sys.argv[2:]
    opp = field.members(hill); seeds = field.seeds(int(os.environ.get("NSEEDS", "16")), salt=int(os.environ.get("SALT", "999")))
    poz = [f for _, n, f in opp if n == "Позитив"][0]
    jobs = [(p, f, s) for p in files for _, _, f in opp for s in seeds]
    with ProcessPoolExecutor() as ex:
        res = list(ex.map(field.pair, jobs, chunksize=8))
        per = len(opp) * len(seeds)
        chal = list(ex.map(field.challenge, [hill] * len(files), files))
    for i, p in enumerate(files):
        chunk = res[i * per:(i + 1) * per]
        tot = sum(3 * r["w1"] + r["ties"] for r in chunk) / len(seeds)
        pz = [chunk[j] for j in range(per) if jobs[i * per + j][1] == poz]
        c = chal[i]
        print(f"{os.path.basename(p):12} fresh {tot:6.0f} | Позитив {sum(r['w1'] for r in pz)/len(seeds):3.0f}:{sum(r['w2'] for r in pz)/len(seeds):3.0f} | hill {c['place']} {c['score']} (Позитив {dict((t['name'], t['score']) for t in c['table']).get('Позитив')})")
