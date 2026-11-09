# Bounded-domain contradiction debugger

This is an exact, deliberately small ground-EUF diagnosis tool. A selected domain cap stays fixed while assertion occurrences may be removed. It preserves both existing inspectors.

## Request, identities and background

Input is exactly `{"input": <base EUF input>, "limit": k}`. The base validation in METHOD.md applies: 1..8 subterm-closed ordered terms, arity 0..2, one fixed arity per symbol, earlier-ID arguments, one uninterpreted sort. This tool further caps the combined number of equality and disequality **occurrences** at eight. `limit` is a JSON integer 1..8, never a boolean. Native input rejects duplicate keys/nonfinite values; browser JSON.parse has its usual duplicate-key behavior.

Occurrence IDs are zero-based: all equalities in original order, then all disequalities in original order. Duplicate and reversed literals are not deduplicated. Terms, signature semantics, totality, nonempty domain, and the bound `|D| <= k` are fixed background. Removing assertions never removes term records or changes function arity. There is no preference, weight, cost or automatic edit.

The cap is an upper bound, not exact cardinality. Any satisfying model with s realized term values and s<=k is enough. A total interpretation with exactly k elements can also be obtained by extending it as ATLAS.md describes, but displayed witnesses use their smallest domain and never claim to have exactly k elements.

## Complete subset table

Build the complete atlas with no asserted equalities or disequalities, leaving the ordered term signature fixed. Every background partition already obeys function congruence, including duplicate constant/function syntax. For each partition p, evaluate every occurrence, obtaining the bit mask of literals it satisfies.

For each mask S of kept occurrences, consider all background partitions that satisfy S. Select the least pair `(number of blocks, background partition ID)` in numeric lexicographic order. Its block count is the exact **unbounded** minimum domain size for S; null means intrinsic inconsistency. S fits the selected cap exactly when this minimum is not null and is at most k. This follows directly from the two-way term-partition/model completeness argument in ATLAS.md. All 2^m masks are reported, including the empty and full sets.

Native generation first finds minima for each exact satisfaction mask, then uses a superset-minimum dynamic program. JavaScript instead directly scans background partitions for every kept subset. Native verification independently reconstructs the entire background atlas using its subset-cover verifier, then directly scans every kept subset and checks all proper subsets for minimality. It does not call the diagnosis generator, native atlas generator or native model builder. Witness models are rebuilt independently and their original terms and retained literals evaluated.

## All minimal cores and deletion repairs

A core C is a subset of occurrence IDs that does not fit the cap, but every proper subset does. The implementation can check immediate one-occurrence removals because satisfiability is downward closed. The verifier checks all proper subsets instead. C is:

- `intrinsic` if it has no satisfying model at any domain size.
- `cap-only` if it has a model, but its minimum domain exceeds k.

A report may contain cores of both kinds. This classification is about each core, not the cause of the full conjunction in isolation.

A deletion repair R is a set of removed occurrence IDs such that the retained full input fits the cap and no proper subset of R does. Equivalently, its complement is an inclusion-maximal satisfiable subset. Minimal means inclusion-minimal, not minimum cardinality. A one-deletion repair and a two-deletion repair may both be minimal. Results are ordered by length, then lexicographic IDs, for reproducibility, not preference.

For an already satisfiable input there are no cores and the unique minimal repair is `[]`. Empty assertions behave the same way, with a one-value total model. The signature alone is always satisfiable here, so there is no empty core. The cap is never proposed as a removable occurrence.

For every core and each of its one-occurrence removals, supply a total witness model for the remaining core. These are **not** necessarily full-input repairs: other conflicts may survive. For every repair, supply a total minimum-domain model for the entire retained input. Every displayed model satisfies the chosen cap. All unlisted function tuples have an explicit default, not an undefined value.

A minimal full-input repair's deleted literals must all be false in every retained-input model. If a deleted literal held in one such model, that same model would satisfy a smaller deletion set, contradicting minimality. This is a consequence of minimality, not a new negation assertion. Occurrences outside a selected core may still hold in a core-relaxation witness, because those other occurrences are not constrained by that witness.

## Hitting-set duality

Every repair hits every core: otherwise an untouched core would remain. Every minimal hitting set of all cores is a minimal repair: if its deletion left an unsatisfiable retained set, that finite set would contain a minimal core missed by the hitting set. Inclusion minimality then gives the reverse implication. Thus all cores and all repairs are minimal hitting-set duals. The UI matrix counts repair/core intersections; it is not an optimization score. Independent tests enumerate minimal hitting sets and compare the complete repair collection.

We implement complete finite enumeration, not CAMUS, MARCO, a SAT/SMT solver or a new core-extraction algorithm. No source is claimed to validate this code.

## Report, CLI and reproduction

Schema `euflab-cardinality-v1`, exact fields: `schema`, `input`, `limit`, `background`, `assertions`, `satisfiable`, `minimum_domain_size`, `subsets`, `cores`, `repairs`. `background` is the full assertion-free `euflab-atlas-v1` certificate. A subset row records `mask`, `minimum_domain_size` and `witness` (background partition ID). Repair and core-relaxation records include their deterministic total `model`. Core records include kind and every one-removal witness. Repair records include removed/kept IDs and retained minimum domain size.

```sh
python -m euflab.cardinality request.json --output diagnosis.json
python -m euflab.cardinality diagnosis.json --verify
python -m pip install .
euflab-cardinality request.json --output diagnosis.json
euflab-cardinality diagnosis.json --verify
python -m unittest discover -s tests -v
npm test
bash tools/check_wheel.sh
```

Package 0.3.0 retains the previous two CLI families. Atomic output, exit 2 on invalid input, the 64-KiB request cap and 8-MiB verification cap are inherited and tested, including preservation of an existing output after an over-limit verification input. The native module and console entry points work offline after installation. The browser computes locally and exports the complete certificate; there is no server solver or paid API.

## Controls and tests

Thirteen controls cover a triangle at caps two and three, an odd cycle, intrinsic inconsistency, simultaneous intrinsic/cap-only cores, duplicate occurrence deletion, unary backward difference, a unary three-cycle requiring three values despite one explicit difference edge, two independent cores, no assertions, the eight-term/eight-occurrence boundary, non-injectivity and minimal-versus-minimum repairs.

Seven new native tests preserve the existing sixteen. Independent labeled-value assignment references check all 64 four-constant disequality graphs at all four caps and 32 seeded functional DAGs. Tests check full subset minima, core/repair minimality, total-model original-term evaluation, hitting-set duality, occurrence IDs, generator-disabled verification, forged/truncated/type-confused reports, cap monotonicity, deleted-literal falsity and atomic CLI errors. Two new Node tests compare all 269 complete browser/native reports (13 controls plus 256 graph/cap combinations) and native-check every browser report. Actual Chrome checks every subset row, core one-removal action, repair action, total interpretation table and all eight cap changes for every control at 320/390/1280 pixels, plus export, invalid-input stale clearing and overflow. Installed-wheel checks cover all three tool families through module and console entry points outside checkout.

This is exponential work: at most 4,140 background term partitions and 256 assertion subsets. It is not a scalability benchmark, production solver, Boolean formula solver, quantified finder, arithmetic engine, multi-sort logic or SMT-LIB parser.

## Source ledger

Sources were read for the listed claims. The earlier METHOD.md and ATLAS.md ledgers remain in force.

1. Mark H. Liffiton and Karem A. Sakallah, **Algorithms for Computing Minimal Unsatisfiable Subsets of Constraints**, author-hosted manuscript with October 10, 2007 typesetting date. Primary research, sections 2.4-2.5 and 3: inclusion minimality, MUS/MCS/MSS definitions and hitting-set duality. We use these definitions, not their CAMUS algorithm or performance claims. High confidence. https://markliffiton.com/publications/jar_liffiton_CAMUS.pdf
2. Ellen Dasnois and Pascal Fontaine, **A Few Exercises on the Complexity of Congruence Closure with Cardinality Constraints**, SMT 2025 extended abstract. Primary research, sections 2-5: compatible class merging, graph coloring only in the function-free case, function-induced hidden differences and hard bounded-domain reasoning. High confidence. https://ceur-ws.org/Vol-4008/SMT_paper24.pdf
3. CMU 15-414 Spring 2024, **SMT Theories & Deciding Uninterpreted Functions**, lecture notes. Congruence/model background; minimum relation does not mean minimum domain. Teaching source, high confidence. https://www.cs.cmu.edu/~15414/s24/lectures/17-smt-theories.pdf
4. Qiu, Sawada and Williams, **Maximize the Rightmost Digit: Gray Codes for Restricted Growth Strings**, author-hosted research manuscript. Restricted-growth/set-partition bijection; no Gray-code implementation claim. High confidence. https://www.socs.uoguelph.ca/~sawada/papers/RSG.pdf
5. OEIS **A000110**, maintained mathematical registry. Set-partition/Bell counts including 4,140 at eight terms. High confidence. https://oeis.org/A000110
6. SMT-LIB, **Logics**, official registry. QF_UF scope comparison; this bounded conjunction JSON tool is not a full QF_UF parser/solver. High confidence. https://smt-lib.org/logics.shtml

Source papers support semantics and terminology, not empirical claims about this implementation. Independent references and published tests support the bounded implementation claims.
