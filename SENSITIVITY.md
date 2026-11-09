# Exact repair-cost sensitivity

[Live inspector](https://midya8.github.io/euflab/sensitivity.html) · [Underlying planner](PLANNER.md)

The fifth EUFLab inspector explains **when a cheapest repair changes** as one deletion price varies. It certifies every inclusive integer interval in 0..1,000,000, all optimum deletion-mask families, exact crossing ties and the maximal interval preserving the complete nominal optimum set. This is a complete bounded one-coordinate calculation, not slider sampling, a new optimization algorithm or a simultaneous-uncertainty guarantee.

## Fixed request and scope

The request is exactly the planner's input, limit, costs and protected fields. All [planner bounds and occurrence-ID rules](PLANNER.md) apply: one uninterpreted sort, ground conjunctions, 1..8 ordered terms of arity 0..2, at most eight combined equality/disequality occurrences, nonempty total models of at most k values, k in 1..8, integer deletion costs 0..1,000,000, increasing unique protected IDs. Equalities precede disequalities; duplicate and reversed occurrences remain distinct.

Every profile varies one occurrence's deletion cost x over the complete integer domain [0,1,000,000], holding **all other costs, protected IDs, logical assertions and the cap fixed**. It does not toggle protection. Costs never override a protected occurrence. No assertion is actually deleted. Profile values are policy counterfactuals, not learned preferences, confidence, causal effects or probabilities.

The complete underlying planning certificate is embedded without changing its schema. All four previous inspectors and schemas remain available.

## Derivation: just two slopes, all tied plans

Let F be the complete permitted deletion-mask set. For occurrence j, write each plan's cost as:

- K(D), if j is kept, where K is the sum of fixed costs of its deleted occurrences;
- K(D)+x, if j is deleted, with j excluded from K.

All keep-class lines have slope zero and all delete-class lines slope one. Within each class only the minimum fixed intercept can ever be globally optimal. Let A=min K over keep-class plans and B=min K over delete-class plans. A missing class is unavailable, represented by null, not infinity or a large fake penalty. The certificate preserves **all** masks attaining A or B. A nonminimal zero-cost mask cannot be silently removed.

If both classes exist, the optimum value is min(A,B+x). The algebraic crossing t=A-B is an exact integer:

- x<t: every B-class minimizing mask wins;
- x=t: the union of both minimizing families wins;
- x>t: every A-class minimizing mask wins.

Intersect these ranges with [0,1,000,000], preserving singleton endpoints. t is reported even when outside the allowed domain. If just one class exists, it wins over the whole domain. If no plan exists, one blocked segment covers the domain and has no optimal masks. Every profile therefore has at most three segments. Segments cover the whole integer domain without holes or overlaps and adjacent segments never have identical optimum sets.

The nominal cost lies in exactly one segment. Its complete optimum-mask family equals the original planner's optimal_masks. That segment is the maximal contiguous integer interval preserving **the full family**, not merely one selected plan or the optimum value. A tie singleton may change the full optimum family even when the value has no jump. The optimum value is nondecreasing and concave in x, with slopes one then zero when both regimes occur; this is a **minimization objective-coefficient** lower envelope. Do not copy convex right-hand-side sensitivity statements into this different setting. On the integer grid the adjacent value increments are in {0,1} and nonincreasing.

Protected j has no delete-class plan. An unprotected j may instead be forced deleted because every keep-j retained input is inconsistent under the cap. Empty assertions give an empty profile list, although the underlying empty plan remains feasible at cost zero. Protected inconsistency cannot be fixed by repricing: all profiles stay blocked.

## Query and witnesses

The UI queries an integer x against the precomputed intervals. It shows every feasible mask's adjusted cost and regret above the optimum, every tied optimal mask, and the selected plan's total retained-input model. Regret is adjusted plan cost minus optimum, never a probability or a global preference rank. If no feasible plan exists, there are no audit rows or model; optimum is null.

The original planning certificate's per-mask cost remains its **nominal** cost. The UI explicitly computes adjusted cost by replacing only j's contribution. Models and retained-input minimum domains stay valid because repricing changes no logical assertion or cap. A deleted literal is not negated; an omitted zero-cost literal can hold in a nonminimal optimal plan. Model values, total function rows and protected/kept/omitted literal truth are displayed. One canonical minimum-domain witness per plan is not an enumeration of all interpretations.

Invalid probe values clear probe audit/model output while leaving the still-valid all-cost certificate available. Editing the logical policy clears every result and download until a valid full run. Download exports all profiles and the full original planning certificate, not just the selected probe.

## Certificate and independent checking

`euflab-sensitivity-v1` has exactly schema, planning, cost_max and profiles. Each profile has assertion, keep, delete, crossing, segments and current_segment. keep/delete contain base and ordered masks. Each segment has lo, hi, kind (keep/delete/tie/blocked) and ordered optimal_masks. IDs and cost arithmetic are exact bounded integers.

Native generation splits all feasible plans into the two classes and uses only the two minimum-intercept crossing cuts. Browser generation independently sweeps **all** opposite-slope affine-line intersections, computes all minimizing masks on each cell and merges identical adjacent optimum families. The native verifier first independently checks the complete embedded planner, then independently builds all plan lines, checks all cross-slope intersection cells and both integer endpoints, merges identical families and compares the exact canonical report including JSON types, ordering and fields. It does not call either sensitivity or planner report generator. Between consecutive line-intersection cuts no pairwise line order changes, so endpoint winners certify the entire integer cell. This establishes completeness without iterating one million values or trusting the generator's minimal two-line cut set.

This is an exponential bounded certificate check, not an industrial MaxSMT proof system or performance claim.

## Reproduce and controls

```
python -m euflab.sensitivity request.json --output sensitivity.json
python -m euflab.sensitivity sensitivity.json --verify
python -m unittest discover -s tests -v
bash tools/check_wheel.sh
npm test
```

Python 3.10+, no runtime dependencies; installed command `euflab-sensitivity`. All five families' module/console generation and verification are checked outside checkout with six imported site-packages origins. Generation accepts at most 64 KiB and verification at most 8 MiB; atomic outputs, exit-2 failures and size limits remain tested. Node 22+ and actual Chrome run UI tests. Serve docs locally and open sensitivity.html; downloaded reports verify offline.

Fourteen original synthetic controls cover interior/zero/upper-endpoint/out-of-domain crossings, all tied classes, cost-versus-count choices, protected/forced/blocked cases, functional cardinality, empty assertions and maximum occurrence boundaries. Seven new native tests preserve the previous 30. All 216 small cost/protection policies are checked against explicit repricing at small integer values; 24 functional policies use an independent labeled-domain assignment oracle. Maximum 256 feasible all-free plans test retained nonminimal ties. Checks cover interval coverage and maximality, endpoints/neighbors, nominal consistency, value concavity, strict validation, disabled-generator verification, forged fields/types/missing masks and atomic CLI caps. Native/browser equality and independent native verification cover 230 complete reports. Actual Chrome checks every coordinate, all interval endpoints/neighbors, every optimum's term/literal/function rows, adjusted costs/regrets, invalid probe recovery, export and stale clearing at 320/390/1280 pixels.

These are complete tiny synthetic controls, not industrial benchmark results. One-coordinate invariance intervals must not be combined into a simultaneous robustness box.

## Source ledger

The two-slope derivation above follows directly from the finite deletion-set objective; no algorithmic novelty is claimed. Primary and official sources support terminology and scope, not validation of this code.

1. MOSEK Optimization Toolbox 11.2.8, *Sensitivity Analysis*, official documentation, undated. Defines parameter perturbation, fixed-other-parameters reasoning and cautions that basis sensitivity may not describe complete optimum behavior. Its continuous LP/right-hand-side examples are context only; our finite objective-coefficient lower envelope is concave, and no MOSEK algorithm or API is used. https://docs.mosek.com/latest/toolbox/sensitivity-shared.html
2. Guanglin Xu and Samuel Burer, *Robust Sensitivity Analysis of the Optimal Value of Linear Programming*, arXiv:1509.04682, revised November 4, 2015, research article. Contrasts single-element ordinary sensitivity with simultaneous uncertainty-set analysis. Used to limit this project's claims; no robust-LP method implemented. https://ar5iv.labs.arxiv.org/html/1509.04682
3. Morgado, Heras, Liffiton, Planes and Marques-Silva, *Iterative and Core-Guided MaxSAT Solving: A Survey and Assessment*, author-hosted survey. Minimum violated-weight, hard/soft and MaxSMT context for the underlying cost planner. No surveyed algorithm implemented. https://markliffiton.com/publications/constraints_morgado_maxsat_survey.pdf
4. Official Online Z3 Guide, *Soft Constraints*. Repeated occurrences count independently; documented positive-weight convention differs from this planner's explicit nonnegative deletion-set extension. https://microsoft.github.io/z3guide/docs/optimization/softconstraints/
5. Official Online Z3 Guide, *Combining Objectives*. Distinguishes cost-only, lexicographic and Pareto choices. Sensitivity here is cost-only, not secretly a count tie-break. https://microsoft.github.io/z3guide/docs/optimization/combiningobjectives/
6. Liffiton and Sakallah, *Algorithms for Computing Minimal Unsatisfiable Subsets of Constraints*, author-hosted manuscript, typeset October 10, 2007. Inclusion-minimal repairs are distinct from minimum-cost and all cost-optimal deletion sets. Not a CAMUS implementation. https://markliffiton.com/publications/jar_liffiton_CAMUS.pdf
7. Official SMT-LIB logic catalogue. Ground one-sort conjunction input here is narrower than general QF_UF and not an SMT-LIB parser. https://smt-lib.org/logics.shtml
