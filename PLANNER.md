# Costed repair planner

[Live planner](https://midya8.github.io/euflab/planner.html) · [All minimal conflicts/repairs](https://midya8.github.io/euflab/cardinality.html)

This is complete bounded **deletion-set planning**, not an editor or general MaxSMT solver. The earlier proof, atlas and domain-cap diagnosis inspectors are preserved. The objective is explicit: minimize the sum of the costs of deleted assertion occurrences, with selected protected occurrences forbidden from deletion. A separate Pareto view considers deletion cost and deletion count together.

## Exact request and bounds

```
{"input":{"terms":[{"symbol":"a","args":[]},{"symbol":"b","args":[]}],"equalities":[[0,1]],"disequalities":[[0,1],[0,1]]},"limit":2,"costs":[9,2,2],"protected":[]}
```

The strict request has exactly input, limit, costs and protected. Input and cap follow [CARDINALITY.md](CARDINALITY.md): 1..8 ordered subterm-closed terms, symbol arity 0..2, at most eight combined equality/disequality occurrences, one uninterpreted sort, ground conjunctions, nonempty total models with at most k values, k an integer 1..8. Signature, congruence, totality, cap and protected assertions are hard background. Assertion IDs are equalities first, then disequalities in original order. Duplicate and reversed occurrences stay distinct.

Costs has exactly one integer in 0..1,000,000 per occurrence; protected is a strictly increasing list of unique in-range integer occurrence IDs. Booleans are not integers in native input. Protected costs remain visible but are never charged because those occurrences cannot be deleted. No costs, pins or preferences are inferred from syntax. No assertion is actually changed.

For deletion mask D, bit j means delete occurrence j. D is permitted iff D contains no protected ID and the whole retained input has a model within the cap. The report lists **every permitted mask**, not only inclusion-minimal repairs. Plan cost is the exact integer sum of costs[j] over D; count is |D|. At most 256 masks and total cost at most 8,000,000 fit exactly in Python and JavaScript integers. A plan's witness minimizes retained-input domain size, then assertion-free atlas partition ID, with total default-completed functions. This is one deterministic model per retained input, not all models.

## Optima, zero costs and omission

Minimum cost is null iff no permitted mask exists; optimal_masks lists every permitted mask at the minimum cost, in increasing mask order. There is **no hidden edit-count tie-break**. The example above chooses deleting both disequalities (mask 6, cost 4) instead of deleting the equality (mask 1, cost 9), although the latter uses fewer edits. At equality cost 4, both masks are cost-optimal.

Zero costs are an explicit extension of this planner's nonnegative deletion-set objective. Some conventional solver interfaces describe positive soft weights; this tool does not claim to parse or reproduce those interfaces. All nonempty deletions of an all-zero-cost triangle are optimal, including nonminimal supersets. Filtering to the diagnosis tool's minimal repairs would omit valid optimal deletion sets. Even an already satisfiable input can have nonempty zero-cost optima alongside the empty plan.

Deleting a literal does not assert its negation. A nonminimal plan's omitted literal can still hold in its displayed model. For an inclusion-minimal repair, every deleted literal must be false in every model of the retained input; otherwise restoring that literal leaves a model and the deletion was unnecessary. Similarly, in any cost-optimal plan, an omitted strictly positive-cost literal cannot hold in any retained-input model: restoring it would reduce cost. With all deletion costs strictly positive, every optimum is minimal. With zeros, a minimal optimum still exists, but nonminimal optima can exist too.

The optimum value agrees with minimizing violated soft-literal weights over models satisfying the protected background. For any feasible D, a retained-input model's violated literals form a subset of D, so their nonnegative total weight is no greater. Conversely, the violated literals of any protected-background model are a feasible deletion set with that cost. Taking minima in both directions gives equality. The **sets returned are deletion plans**, not all falsified-literal sets or all optimizing models. With zero costs, an optimal deletion plan can also omit satisfied zero-cost literals. There is no Boolean connective language, arithmetic, SMT-LIB parser, external Z3 dependency or general MaxSAT encoding.

## Cost/count Pareto frontier

A permitted plan Q dominates P iff cost(Q) <= cost(P), count(Q) <= count(P), and at least one inequality is strict. frontier_masks retains every plan not dominated by another permitted plan, including all plans at tied nondominated coordinates. It is neither lexicographic optimization nor a preference-weighted sum. The cost-only and Pareto lists are separate: a same-cost smaller deletion plan can remove a cost-optimum from the frontier without removing it from optimal_masks.

Every Pareto plan is inclusion-minimal: deleting a proper feasible subset has no higher cost and strictly smaller count. The strictly-positive/nonminimal distinction is therefore visible without claiming either policy is objectively right.

## Protected infeasibility and completeness

The report embeds a complete independently verifiable domain-cap diagnosis. blocked_cores lists every diagnosis core contained wholly in protected. These cores may be intrinsic or cap-only. No permitted plan exists iff at least one such core exists. Proof: if protected assertions are inconsistent under the cap, their finite set contains an inclusion-minimal unsatisfiable subset, which is one of the complete diagnosis cores. Conversely, a protected core survives every permitted deletion. If the protected subset is satisfiable, deleting all other occurrences is a permitted plan. Thus a high deletion cost never acts as a substitute for protection.

Completeness follows from the diagnosis subset table's two-way finite-term-partition/model argument and complete enumeration of all 2^m deletion masks. Each mask is checked against the hard exclusion and retained subset satisfiability. Enumerating all costs then taking their minimum returns every optimum. Pairwise componentwise domination defines the complete frontier. Empty assertions yield one permitted empty plan, cost/count zero, minimum domain one, no blocked core. Blocked instances yield no feasible rows, null optimum and empty objective lists.

## Implementation and certificate checks

Native generation uses the existing native diagnosis engine, incremental low-bit cost sums, minimal-repair membership and a per-edit-count minimum-cost frontier calculation. Browser generation uses its existing independent partition/subset engine, direct removed-cost sums, immediate restoration checks for minimality and pairwise plan domination.

`euflab-planner-v1` contains exactly schema, diagnosis, costs, protected, feasible, optimum_cost, optimal_masks, frontier_masks and blocked_cores. Each feasible row includes mask, ordered removed/kept IDs, exact cost/count, inclusion-minimal flag, minimum_domain_size, partition ID and total model. Native verification first independently verifies the complete diagnosis. It then scans every mask, recomputes direct cost sums, checks all proper deletion subsets for minimality, rebuilds canonical function rows without the native model builder, evaluates term/literal values, and tests pairwise domination. Exact JSON comparison rejects changed types, missing/extra rows, changed order, objectives, models and policies. It never calls either report generator or its native model builder. Exponential certificate checking is intentional at this bound, not an industrial proof checker or performance claim.

## Reproduce

Python 3.10+; no runtime packages:

```
python -m euflab.planner request.json --output plan.json
python -m euflab.planner plan.json --verify
python -m unittest discover -s tests -v
bash tools/check_wheel.sh
npm test
```

Installed command: `euflab-planner`. Module/console generation and verification are checked outside checkout for every control of all four families. Generation accepts at most 64 KiB, verification at most 8 MiB, writes atomically, exits 2 on invalid input and preserves an existing output on failure. Node 22+ and actual Chrome run the browser tests. Local UI: `python -m http.server --directory docs 8000`; open planner.html. Downloaded certificates can be checked offline with the native verifier.

Seven new native tests preserve the original 23. Labeled-domain assignments independently check all 64 four-name disequality graphs, every protected subset at caps 1/2 (1,458 requests), all 216 cost/protection policies for the duplicate-conflict example, and 40 seeded functional DAG policies. Tests cover zero costs, all tied optima, Pareto ties/tradeoffs, hard-core obstructions, costs/pins monotonicity, positive-cost minimality, strict types, disabled-generator verification, report forgery and CLI size/atomic errors. Complete native/browser comparisons and native verification cover 358 reports: 14 controls, 216 cost/protection policies and 128 graph/cap requests. Actual Chrome tests every feasible control plan and its term/literal/function rows, all four objective views, all caps, policy edits, blocked/recovery transitions, invalid-cost recovery, export and stale clearing at phone and desktop widths.

These are synthetic bounded controls, not an industrial benchmark or measured claim of practical speed.

## Source ledger

Primary/official sources inform definitions; local independent tests establish implementation behavior. No source is attributed as this code's author. No claim to implement CAMUS, Z3, an industrial MaxSAT solver or a novel optimization algorithm.

1. Morgado, Heras, Liffiton, Planes and Marques-Silva, *Iterative and Core-Guided MaxSAT Solving: A Survey and Assessment*, author-hosted survey. Introduction and MaxSMT discussion define hard/soft constraints and minimum violated-weight objectives. Used for context, not a copied algorithm or benchmark claim. https://markliffiton.com/publications/constraints_morgado_maxsat_survey.pdf
2. Official Online Z3 Guide, *Soft Constraints*, undated documentation. Positive soft-weight convention and repeated occurrences counting separately. Our zero-cost deletion-set semantics is explicit rather than attributed to this interface. https://microsoft.github.io/z3guide/docs/optimization/softconstraints/
3. Official Online Z3 Guide, *Combining Objectives*, undated documentation. Distinguishes lexicographic, Pareto and independent objectives. Our two-coordinate frontier and complete tied-plan output are defined above; no Z3-equivalence of all returned plans is claimed. https://microsoft.github.io/z3guide/docs/optimization/combiningobjectives/
4. Liffiton and Sakallah, *Algorithms for Computing Minimal Unsatisfiable Subsets of Constraints*, author-hosted manuscript, typeset October 10, 2007. Sections 2.4, 2.5 and 3 give MUS/MCS/MSS definitions, inclusion versus minimum and hitting-set duality underlying the diagnosis background. https://markliffiton.com/publications/jar_liffiton_CAMUS.pdf
5. Dasnois and Fontaine, *A Few Exercises on the Complexity of Congruence Closure with Cardinality Constraints*, SMT 2025 extended abstract, CEUR. Background on cardinality-compatible congruence merging and why coloring just explicit disequalities is insufficient when functions interact. https://ceur-ws.org/Vol-4008/SMT_paper24.pdf
6. Official SMT-LIB logic catalogue, undated. QF_/UF naming scope; our conjunction-only one-sort ground input is narrower and is not an SMT-LIB parser or general QF_UF solver. https://smt-lib.org/logics.shtml
