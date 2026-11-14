# EUFLab

Ground equality proofs, congruence-derived contradictions and total finite countermodels.

[Live inspector](https://midya8.github.io/euflab/) · [Exact contract and six-source ledger](METHOD.md)

- Native union-find and proof-forest paths; independent relational closure/certificate/model replay.
- Separate JavaScript relation engine. Every ordered equal pair has a proof DAG. Every non-entailed equality in a consistent input has a separating finite interpretation.
- Explicit controls for non-injectivity, cyclic values, duplicate syntax, ordered arguments, redundant assumptions, multiple disequality conflicts and inconsistency/vacuity.
- No dependencies at runtime. No model API, private data, account execution or new-algorithm claim.

## Choose an inspector

| Question | Page / native module | Result |
| --- | --- | --- |
| Which equalities follow from the assertions? | `index.html` / `euflab` | Proof DAGs, contradictions and separating models |
| Which finite equality patterns are compatible? | `atlas.html` / `euflab.atlas` | All term partitions, minimum domain size and pair classifications |
| Which assertions conflict under a domain cap? | `cardinality.html` / `euflab.cardinality` | Every minimal conflict and deletion repair |
| Which permitted repairs have least cost? | `planner.html` / `euflab.planner` | Cost optima, cost/count frontier and protected-core obstructions |
| When does one changed deletion cost alter the optima? | `sensitivity.html` / `euflab.sensitivity` | Exact integer intervals, ties and regret |

All pages are under `docs/`. Deletion repairs are hypothetical: no input is
edited. Minimal conflicts and repairs need not have minimum size, and one-cost
sensitivity is not simultaneous-input robustness.

## Run

Python 3.10+:

```sh
python -m euflab docs/example.json --output report.json
python -m euflab report.json --verify
python -m unittest discover -s tests -v
bash tools/check_wheel.sh
```

Or install `python -m pip install .` and use `euflab`. Node 22+ and local Chrome run `npm test`. Open the demo via `python -m http.server --directory docs 8000` and visit http://localhost:8000. Browser edits run locally; native verification of downloaded reports runs offline.

Input is a subterm-closed ordered term DAG, not a string parser. IDs are original list positions:

```json
{"terms":[{"symbol":"a","args":[]},{"symbol":"b","args":[]},{"symbol":"f","args":[0]},{"symbol":"f","args":[1]}],"equalities":[[2,3]],"disequalities":[]}
```

This asserts f(a)=f(b). It does not imply a=b. The displayed total model assigns distinct values to a and b and the same output to f on both. Conversely, a=b implies f(a)=f(b). a=f(a) is legal because functions are not free constructors.

## Evidence and limits

The original nine native tests include partition-enumeration references, 27 exhaustive constant conjunctions, 64 four-term assertion subsets plus all added disequality probes, 80 seeded DAGs, proof tampering and atomic CLI rejection. Two Node tests compare 156 semantic reports and native-check every browser proof DAG. Chrome tests all 251 ordered queries and every displayed proof/model row at 320/390/1280. Wheel reproduction runs 12 controls through both entry points outside checkout.

At most eight terms, arity at most two, eight equalities and eight disequalities. One uninterpreted sort; ground conjunctions only. Proofs are valid explanations, not shortest proofs or minimal cores. A separating model does not prove a universal inequality. Inconsistent inputs have no countermodel and entail everything classically, even if a pair is absent from positive closure. Classical congruence closure, not new theory, a scalable solver or a real-code verifier. See [METHOD.md](METHOD.md).

## Finite-model atlas

[Live atlas](https://midya8.github.io/euflab/atlas.html) | [Exact atlas contract and sources](ATLAS.md)

The largest quotient model is not necessarily the smallest domain. Enumerate every compatible term-equality pattern, minimum domain size and realized-value histogram. Classify each pair as forced equal, forced different or flexible, with total model witnesses. Unary result difference forces argument difference; binary result difference generally forces a disjunction, not each difference.

```sh
python -m euflab.atlas docs/example.json --output atlas.json
python -m euflab.atlas atlas.json --verify
# Installed console: euflab-atlas
```

Independent restricted-growth, explicit-block and subset-cover enumerators. Preserves the original nine native tests; adds seven native and three Node/Chrome tests. All 4,317 admitted control patterns, 248 pair queries and 362 pair-witness actions are exercised at each of three widths. Counts are term-equality patterns, not full interpretations. Every finite domain size at least the minimum is possible, using extra unnamed elements; classifications impose no domain-size cap. Exponential search, at most eight terms.

## Bounded-domain contradiction debugger

[Live domain-cap debugger](https://midya8.github.io/euflab/cardinality.html) | [Exact diagnosis contract](CARDINALITY.md)

Fix a finite-domain upper bound and inspect **every minimal conflicting assertion subset** and **every minimal deletion repair**. Distinguish intrinsic contradictions from cap-only conflicts, audit all assertion subsets, and inspect total models for whole-input repairs or individual core relaxations. Duplicate occurrences stay separate; minimal does not mean minimum-size, and fixing one core need not fix the full input. A unary three-cycle control shows why coloring only explicit difference edges is insufficient.

`python -m euflab.cardinality request.json --output diagnosis.json` and `python -m euflab.cardinality diagnosis.json --verify`; installed console: `euflab-cardinality`. Thirteen controls, independent full-subset/duality references, 269 complete cross-engine reports, and actual mobile/desktop Chrome interactions. Eight terms, eight assertion occurrences, one sort, conjunctions only. No paid API or scalability claim. Original proof and atlas tools are retained.

## Costed repair planner

[Live planner](https://midya8.github.io/euflab/planner.html) · [Exact semantics and six-source ledger](PLANNER.md)

Protect occurrence IDs and set explicit nonnegative deletion costs. The fourth inspector returns every permitted deletion mask, every cost-only optimum, a separate cost/count Pareto frontier, protected-core obstructions and total retained-input models. Zero-cost nonminimal ties are preserved; deleting does not mean negating. Costs never override protected assertions. Nothing is actually edited. Eight terms/eight occurrences, not a general MaxSMT optimizer.

`python -m euflab.planner request.json --output plan.json` and `python -m euflab.planner plan.json --verify`; installed `euflab-planner`. Fourteen synthetic controls, independent labeled-domain references, complete native/browser comparisons and full installed/UI reproduction. Earlier inspectors and tests remain intact.

## Exact repair-cost sensitivity

[Live sensitivity inspector](https://midya8.github.io/euflab/sensitivity.html) · [Derivation, contract and seven-source ledger](SENSITIVITY.md)

When does a cheapest repair change? Freeze every other cost, protected ID, assertion and domain cap. The fifth inspector certifies every integer interval in 0..1,000,000, every breakpoint tie, all optimal mask families and the maximal interval preserving the full nominal optimum set. Probe adjusted cost/regret and replay a total model without hiding zero-cost nonminimal optima. Exact two-slope finite planning, not a simultaneous robustness or general parametric-optimization claim.

`python -m euflab.sensitivity request.json --output sensitivity.json`; `python -m euflab.sensitivity sensitivity.json --verify`. Installed `euflab-sensitivity`. All four earlier schemas and inspectors remain intact.
