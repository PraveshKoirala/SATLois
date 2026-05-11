# SAT-LOIS

This repository contains the implementation for the paper *An Application of SAT Solvers in Integer Programming Games*.

Files:

- `cng.py`: synthetic critical node game generator shared by the SAT-based model.
- `sat_lois.py`: SAT encoding for locally optimal solutions in the critical node game.
- `graph_game/`: graph interdiction benchmark and heuristics.

## Dependencies

Install:

```bash
pip install -r requirements.txt
```

## Usage

Find a SAT-based local solution for a critical node game instance:

```bash
python sat_lois.py --size 50 --seed 6318 --locality 2
```

Run the graph-game benchmark:

```bash
python graph_game/benchmark.py --vertices 50 --budget-d 5 --budget-a 2 --radius 5 --samples 20 --seed 75
```

## Notes

- `sat_lois.py` provides a self-contained SAT-based solver for local solutions in the critical node game.
- The `graph_game` directory contains the benchmark code and heuristic baselines used for the graph-game experiments.
- This repository covers both the SAT-based implementation and the graph-game application discussed in the paper.
