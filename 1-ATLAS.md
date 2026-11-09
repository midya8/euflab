# Finite-model atlas: exact contract

This adds a complete, deliberately tiny model-pattern search to EUFLab. It does not replace the existing congruence-proof inspector. The least congruence has the fewest required equalities and thus the most distinct values among the listed terms. It need not give a minimum-cardinality domain. The atlas explores every compatible coarser equality pattern.

## Input and canonical patterns

Same input as the base tool: exactly `terms`, `equalities` and `disequalities`; 1..8 subterm-closed ordered term records, function arity 0..2, one fixed arity per symbol, earlier-ID arguments, and at most eight pairs of each sign. See METHOD.md for full validation details. JSON integral endpoint numbers are normalized; booleans are rejected. Native CLI rejects duplicate keys and nonfinite JSON; browser JSON.parse has its usual duplicate-key behavior.

A partition is an array of original term IDs. `partition[i]` is the smallest term ID in the block containing i. Patterns are lexicographically sorted, unique and zero-indexed. These IDs are stable within a report, not across edits. Each candidate must satisfy all input equalities and disequalities. For every pair of same-symbol terms, equal argument-value tuples must imply equal result values. This includes arity-zero duplicate constant records.

Native generation uses restricted-growth strings, then replaces block labels with minimum original IDs. JavaScript uses insertion into explicit blocks. The independent native verifier enumerates subset covers: choose the smallest uncovered term, try every subset of the remaining terms in its block, and recurse. It uses pairwise semantic tests rather than generator function-table signatures. No generator, compatibility helper or model builder is called by verification.

## Completeness and total interpretation

Every structure satisfying the ground conjunction induces an equivalence relation on the listed terms: i and j are related exactly when their evaluated values coincide. Equality makes this a set partition. Asserted literals and functional congruence make it pass the filter. This applies even to infinite structures.

Conversely, every accepted partition gives a satisfying finite structure. Use its block representatives as domain elements. Each observed function argument tuple maps to the block of its result term. Congruence ensures that this is well defined. Assign the smallest block representative as default on every unlisted tuple. This makes each function total. Because every argument is an earlier listed term, induction on the input order evaluates every term to its prescribed block representative. All input literals therefore hold.

Thus the enumeration is complete for **term-equality patterns**, not all interpretations and not all structures up to isomorphism. Different function values on unobserved tuples can give different structures with the same pattern. Domain-element renamings do not produce new patterns. Extra unnamed domain elements do not produce new patterns either.

## Minimum domain versus realized-term spectrum

`histogram` counts admissible patterns at each number of distinct values realized by the listed terms. Each nonzero row supplies the first corresponding partition ID. Its counts are not counts of full interpretations. `minimum_domain_size` is the least row size, or null if no partition exists.

That minimum is also the true minimum size of a nonempty total domain. Any satisfying structure realizes at least this many listed-term values, by the first half of the completeness argument. The construction supplies a model with exactly the minimum, by the other half.

Moreover every finite total-domain size greater than or equal to the minimum is possible. Extend a minimum model with any number of fresh elements, preserving all existing function values and using the default on all new argument tuples. Constants and all listed-term evaluations stay unchanged. This claim depends on the exact ground, one-sort, uninterpreted signature here: there are no quantified, surjectivity, finite-datatype or domain-closure axioms. The histogram of *realized listed-term values* is a different object from the spectrum of *total-domain sizes*. No domain-size constraint is imposed on pair classifications.

## Forced pair classes and witnesses

For each ordered term pair:

- `forced-equal`: every admissible pattern equates it; first equal-value witness supplied, no different-value witness.
- `forced-different`: every admissible pattern separates it; first different-value witness supplied, no equal-value witness.
- `flexible`: at least one pattern equates it and another separates it; first witnesses for both.
- `inconsistent`: there are no admissible patterns. Both equality and disequality are classically entailed, but no satisfying witness exists. We do not mislabel this as flexibility or a concrete proof of either sign.

These are complete answers over all structures, by the pattern completeness argument. A witness is a total interpretation, not an existential guess over an incomplete function table. The report records total models for the union of all first pair witnesses and histogram witnesses, with duplicates removed. Every other enumerated pattern can be selected in the browser; its displayed total interpretation is constructed by the same rule. Arbitrary displayed selections are not separately appended to the downloaded report, which already contains every partition and the deterministic construction rule.

Witness absence is justified by complete enumeration, not a shortest proof or a minimal core. The original inspector supplies proof DAGs for forced equalities. In a consistent input, forced inequality can also be checked independently by adding the opposite equality and checking for contradiction; the native tests use this different route. In the function-free case, minimum domain size reduces to graph coloring after positive equality classes are merged. With functions present, argument and result merges interact, so coloring only the explicit disequality graph is insufficient.

## Report and CLI

Schema `euflab-atlas-v1`, exact fields: `schema`, `input`, `satisfiable`, `candidate_count`, `partitions`, `histogram`, `minimum_domain_size`, `pairs`, `witnesses`. Witness models use the base model format: sorted representative domain, `term_values`, minimum representative `default`, alphabetically sorted functions, and numerically lexicographic argument rows with original term origins. There is no undefined function case. The checker independently reconstructs every field, complete partition list and witness model, and evaluates its original terms.

```sh
python -m euflab.atlas docs/example.json --output atlas.json
python -m euflab.atlas atlas.json --verify
# After python -m pip install .:
euflab-atlas docs/example.json --output atlas.json
euflab-atlas atlas.json --verify
```

CLI input limits and atomic output behavior are inherited from the strict base CLI: 64 KiB generation input, 8 MiB certificate input, error exit 2 without replacing existing output. No network or model service is needed. Package version 0.2.0 includes both CLI families.

## Controls and validation

Twelve controls cover coincident names, a three-clique, a five-cycle, path reuse, unary contrapositive difference, binary disjunction, non-injectivity, cyclic values, duplicate syntax, inconsistency, eight unconstrained names, and a two-value functional swap. The eight-name control has 4,140 patterns; realized-value counts are 1, 127, 966, 1,701, 1,050, 266, 28, 1. The five-cycle has 11 patterns: five with three values, five with four and one with five. The binary control shows that a function-result disequality forces at least one argument difference, not every argument difference.

Seven new native tests preserve the original nine. Independent labeled-value assignment references cover controls up to five terms, all 64 four-constant disequality graphs, and 60 seeded term DAGs. Tests evaluate every admitted control partition, including total-function behavior on an extra-element domain extension, compare pair classifications to ordinary congruence refutation, reject forged/truncated/duplicate/reordered certificates, disable generator helpers during verification, and exercise strict atomic CLI input and the 8 MiB report cap. Two new Node tests compare 76 complete native/browser atlas reports and native-check every browser report. Actual Chrome visits every one of the 4,317 admitted control patterns, all 248 ordered pair queries and 362 available pair-witness actions at each of 320, 390 and 1280 pixels. It checks table rows, histogram selection, matrix cells, invalid pattern IDs, export, stale clearing and horizontal overflow. Every displayed 390px total model is compared to the native model builder. Installed-wheel checks cover both module and console entry points for all 12 atlas controls outside checkout, in addition to the original 12 proof controls.

This is exponential enumeration with a hard eight-term bound, not an efficient general finite-model finder or new algorithm. No benchmarks support a scalability claim. It does not enumerate quantifiers, arithmetic, Boolean formulas, SMT-LIB syntax, multiple sorts or all function interpretations.

## Source ledger

All sources below were read for the stated claims. The broader base congruence/proof ledger remains in METHOD.md.

1. Ellen Dasnois and Pascal Fontaine, **A Few Exercises on the Complexity of Congruence Closure with Cardinality Constraints**, SMT 2025 workshop extended abstract, primary research. Sections 2-3 connect compatible class merging with cardinality and graph coloring; section 5 explains hidden disequalities and unary versus disjunctive binary backward propagation. High confidence. https://ceur-ws.org/Vol-4008/SMT_paper24.pdf
2. **SMT Theories & Deciding Uninterpreted Functions**, CMU 15-414, Spring 2024 lecture notes, teaching source. Congruence relations as models and the distinction between minimum relation and number of domain values. Its "minimal models" heading concerns the relation, not our minimum-cardinality search; the atlas explicitly separates them. High confidence. https://www.cs.cmu.edu/~15414/s24/lectures/17-smt-theories.pdf
3. Y. Qiu, J. Sawada and A. Williams, **Gray Codes for Restricted Growth Strings**, research manuscript, date not exposed in fetched introduction. Section 1.1 gives the standard restricted-growth/set-partition bijection and Bell counts including 4,140 at n=8. We implement simple exhaustive recursion, not their Gray-code algorithm. High confidence for the definitions. https://www.socs.uoguelph.ca/~sawada/papers/RSG.pdf
4. **A000110, Bell or exponential numbers**, OEIS, maintained mathematical registry. Number of partitions of a labeled n-set and restricted-growth representation, independently grounding the boundary count. High confidence. https://oeis.org/A000110
5. **SMT-LIB Logics**, official registry, QF_UF scope context. This tool implements a small JSON ground-conjunction subset and is not an SMT-LIB parser or complete QF_UF Boolean solver. High confidence. https://smt-lib.org/logics.shtml
6. T. Junttila, **Solving EUF**, Aalto 2020 lecture notes, teaching source. Congruence closure and satisfying quotient interpretations ground the base model construction; the explicit partition-completeness and domain-extension arguments above are supplied here for this bounded implementation. High confidence. https://users.aalto.fi/~tjunttil/2020-DP-AUT/notes-smt/euf_solver.html

Additional background read: Vakili and Day, **Finite Model Finding Using the Logic of Equality with Uninterpreted Functions**, 2016, https://cs.uwaterloo.ca/~nday/pdf/refereed/2016-VaDa-fm.pdf . Its general quantified finite-scope translation is not implemented here and its broader EUF complexity statements are not applied to our conjunction-only base solver. No source is claimed to validate this implementation; independent tests and complete checking do that work within the stated bound.
