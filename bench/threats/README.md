# Threats: published warriors stronger than the hill

The warriors a newcomer could bring to the board's hill tomorrow. On
2026-09-29 we played 677 published warriors against the hill as it stood
after job 186 (king Позитив): four position seeds, 250-round matches, points
3/1/0 from each of the 20 members. The best of them take 12–13.5 thousand
points from that hill; its own king took about 11.2 thousand.

- `ranking.csv` — all 677, best first: score, `;name`, `;author`, the
  collection, where the file is, its SHA-256.
- `threats.json` — the 30 strongest and the three warriors of the pMARS
  distribution (Rave, Aeka, Flash Paper), with the same data and how to get
  each file.
- `fetch.py` — downloads them from where they were published and checks
  every file against its SHA-256: `python3 bench/threats/fetch.py OUTDIR`.

## Why the files are not here

Most of these warriors carry no license: their authors own them, and we do
not republish them. Sources:

- [Koenigstuhl](https://asdflkj.net/COREWAR/koenigstuhl.html), Christoph C.
  Birk's infinite hills: the Pspace and 94nop TOP-50 archives.
- [n1LS/redcode-warriors](https://github.com/n1LS/redcode-warriors), a
  collection of warriors from various hills, commit `615f2f3`.
- [pMARS](https://github.com/mbarbon/pMARS) 0.9.2, commit `e7e8d08`, GPL-2.0.

Sources disappear: the whole Pspace archive of Koenigstuhl was already gone
(404) when we looked. We keep a private copy of everything we screened in
`geibos/corewar-archive`; `fetch.py --archive DIR` takes files from a clone
of it first.

## How the screen was made

cw 2.3.0, the engine's library on its own thread pool (`cw pair` semantics:
the listed warrior is pMARS's first, `--seed` is `-F` minus the distance),
seeds 101, 2203, 4405 and 6607 against every member of the hill after job
186. A score is the sum over the 20 members, averaged over the four seeds.
Four seeds per pair are enough to screen; a decision about a warrior plays the
set on more seeds, and pairs the matches against the warrior it replaces.
