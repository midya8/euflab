# Ground equality with explanations and countermodels

EUFLab implements classical congruence closure for tiny ground conjunctions of equalities and disequalities. It is not a new algorithm or a production SMT solver. Unifylab elsewhere in this portfolio handles syntactic first-order substitution and occurs-check; EUFLab handles ground equality in arbitrary interpretations. In particular a = f(a) is allowed, and equal outputs do not imply equal arguments.

## Input and logic

Exactly `{terms,equalities,disequalities}`. `terms` is a nonempty list of at most 8 records `{symbol,args}`. IDs are positions. Symbols match `[a-z][a-z0-9_]{0,7}`. Every symbol has one fixed arity, 0..2. Arguments reference earlier records, so input syntax is an acyclic, subterm-closed term DAG. Duplicate syntactic records are allowed and merge by congruence, including repeated zero-argument constants. Each assertion list has at most 8 pairs of valid term IDs. All numbers are finite integral-valued endpoint numbers, normalized to native integers; booleans are not endpoints.

All terms inhabit one nonempty uninterpreted sort. Symbols are uninterpreted total functions. There are no variables, substitutions, quantifiers, Boolean connectives beyond conjunction, arithmetic, predicates, sorts beyond this one, rewrite rules, injectivity, commutativity, constructor disjointness, unique names or acyclicity axioms on *values*. Acyclic syntax does not forbid cyclic interpretations. No source code, account or tool is executed by the inference engine.

The least congruence is computed from positive equalities only. Every listed disequality whose endpoints collapse is reported as a conflict. Otherwise the conjunction is satisfiable. For a consistent conjunction, the quotient model separates all different closure classes at once, so it witnesses every equality not entailed by the conjunction. Difference in this model is not a universally entailed disequality: some other model can merge classes. For an inconsistent conjunction, every formula follows classically. A missing closure edge is therefore not a semantic non-entailment or a countermodel. The UI explicitly distinguishes these cases.

## Native generation and proof contract

Schema `euflab-v1` has exactly `schema,input,consistent,classes,equal,proofs,evidence,conflicts,model`.

Native generation uses min-representative union-find, scans term pairs for congruence, and records successful merges as a proof forest. Breadth-first forest paths supply transitivity/symmetry witnesses; congruence premises are proved before their parent merge. `classes` are sorted by smallest original ID, with sorted members. `equal[a][b]` is a strict Boolean matrix for the positive closure. Native generation is deterministic for a fixed normalized input.

`proofs` is a backward-referencing DAG. Each node has exactly `rule,left,right,premises`, plus `assumption` only for an assumption node. Rules:

- `reflexivity`: a=a, no premises.
- `assumption`: exactly the ordered input equality at the given zero-based index, no premises.
- `symmetry`: one premise b=a concludes a=b.
- `transitivity`: premises a=c and c=b conclude a=b.
- `congruence`: same symbol and one premise for each ordered pair of argument IDs. Constants have zero premises.

Every premise is a smaller proof ID. `evidence[a][b]` is a valid proof ID for a=b exactly when the closure matrix is true, and null otherwise. `conflicts` lists every violated disequality in original order as `{index,proof}`. Proofs are not promised shortest, irredundant, canonical across implementations, or minimal assumption cores. Unused sound proof nodes are permitted, up to a verifier cap of 4096. Browser/native proof IDs and DAG shapes intentionally differ.

## Total finite interpretation

`model` is null exactly when inconsistent. Otherwise it contains `domain`, `term_values`, `default`, and `functions`. Domain elements are smallest original IDs of classes, in increasing order. `term_values` maps every original term to its representative. Default is the smallest domain element.

Function records are sorted by symbol, with `symbol,arity,rows`. Each row has `args,value,terms`: a tuple of argument **domain values**, its result value, and every original term with that signature and tuple. Rows are lexicographically sorted by numeric tuples; origins are sorted. Congruence guarantees single-valued rows. Every unlisted tuple over the whole domain returns the default. This implicit completion is part of the interpretation, so functions are total even on tuples absent from the term DAG. Constants have the empty argument tuple. All listed terms are evaluated in original order and every equality/disequality is checked. This is one model, not a minimum-cardinality model or a unique interpretation.

## Independent checking and browser engine

Native verification does not call generation, union-find, the native forest traversal or its model builder. It derives the complete least relation by independent set-based fixed-point saturation, checks every proof locally, requires a proof for every closure pair, reconstructs the expected interpretation independently and evaluates every original term/assertion. Unknown fields, forward references, bad rule arities, wrong conclusions, inconsistent model defaults and strict report-type changes are rejected. It is a complete bounded replay, not a scalable certificate checker.

JavaScript uses a separate dense relation matrix with direct reflexivity, symmetry, transitivity and congruence proof construction, not union-find or forest paths. Semantic fields and model rows agree with native generation; every JavaScript proof report is accepted by the native independent checker. Browser edits run locally. Reports can be checked offline using `euflab report.json --verify`; the browser does not contact a proof-verification server. Native JSON rejects duplicate keys, nonfinite constants and oversized input; the browser editor uses standard JSON.parse duplicate-key behavior. Object-level validation and normalized endpoint semantics agree.

Nine native tests cover all 27 three-constant equality/disequality labelings, all 64 positive assertion subsets on a four-term unary fixture and all six added disequality probes per subset, all 12 controls against an independent **enumeration of all set partitions** (including the 4140 partitions at the eight-term boundary), 80 seeded term DAGs, complete model tuple ranges, proof/field/type forgeries, disabled-generator verification, numeric normalization and atomic CLI rejection. Two Node tests compare 156 semantic reports and pass all JavaScript DAGs through native verification. Actual Chrome tests traverse all 251 ordered control queries, 125 displayed proof-ancestor rows and 34 model rows at each of 320/390/1280 pixels, including inconsistent-query semantics, model completion, stale clearing and JSON export. Installed-wheel reproduction checks every control through module and console generation/verification outside checkout.

## Sources and attribution

1. Greg Nelson and Derek C. Oppen, *Fast Decision Procedures Based on Congruence Closure*, JACM 27(2), 1980. https://people.eecs.berkeley.edu/~necula/Papers/NelsonOppenCong.pdf . Primary research. Section 3 decision procedure and quotient interpretation with arbitrary completion on unobserved tuples. Section 4 adds list axioms which are **not** assumed here. No fast complexity bound from this paper is claimed for EUFLab.
2. Robert Nieuwenhuis and Albert Oliveras, *Proof-Producing Congruence Closure*, RTA 2005. https://www.cs.upc.edu/~roberto/papers/rta05.pdf . Primary research. Ground explanation setting and congruence versus equivalence closure. EUFLab uses a simple bounded proof forest, not their almost-optimal Explain algorithm or implementation.
3. Aalto University, *A Theory Solver for Equality with Uninterpreted Functions*, 2020 course notes. https://users.aalto.fi/~tjunttil/2020-DP-AUT/notes-smt/euf_solver.html . Teaching documentation. Congruence propagation, union-find and disequality checks. No course code or images copied.
4. Ruben Martins, CMU 15-414 Lecture 17, *SMT Theories*, April 6, 2021. https://www.cs.cmu.edu/~15414/s21/lectures/17-smt-theories.pdf . University lecture. Subterm closure, equivalence/congruence distinction and conjunction satisfiability criteria.
5. Robert Nieuwenhuis and Albert Oliveras, *Fast Congruence Closure and Extensions*. https://www.cs.upc.edu/~roberto/papers/IC06.pdf . Primary research. Broader explanation-capable congruence closure context. Its algorithms, performance results and extensions are not implemented or claimed.
6. SMT-LIB, *Logics*. https://smt-lib.org/logics.shtml . Official logic registry. QF_UF naming and the broader quantifier-free uninterpreted-function scope. EUFLab only handles a tiny one-sort ground conjunctive subset. It is **not** an SMT-LIB parser, a complete QF_UF solver, DPLL(T), or a theory-combination implementation.

All sources fetched and governing sections inspected. Original implementation, synthetic fixtures, tests and interface. No external datasets, model/API calls, private records or paid services.
