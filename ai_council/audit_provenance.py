from __future__ import annotations

import ast
import hashlib
import io
import re
import textwrap
import tokenize
from pathlib import Path
from typing import Any



def derive_behavioral_contract_authority(project: Path, request: str) -> dict[str, Any]:
    """Record an independently matched *declaration* of intended behavior.

    Only trusted control-plane inputs may call this: an explicit authoritative
    requirement in the original user task and the exact same requirement in a
    bounded, local, non-symlink SPEC.md. A test is not a semantic oracle.
    This attests a declared contract, not a mathematical proof of any claim.
    """
    missing = {"status": "NO_AUTHORITY"}
    if not isinstance(request, str) or not isinstance(project, Path):
        return missing
    # This is a tiny positive declaration grammar, not natural-language
    # negation detection. Unknown wording always abstains. The optional
    # read-only/source-location clauses carry no behavioral authority.
    if chr(96) in request or "~~~" in request:
        return missing
    request_lines = request.splitlines()
    if len(request_lines) < 2 or re.fullmatch(
        r"(?:(?i:Read-only audit\.)[ \t]*)?"
        r"(?:(?i:Do not edit files\.)[ \t]*)?"
        r"(?:(?i:The source is) [A-Za-z0-9_./-]+; "
        r"(?i:tests are) [A-Za-z0-9_./-]+\.[ \t]*)?"
        r"(?i:AUTHORITATIVE SPECIFICATION:)[ \t]*",
        request_lines[0],
    ) is None:
        return missing
    allowed_tail = {
        "Do not modify the project.", "Do not edit files.",
        "Return only evidence-grounded findings and explain uncertainty where "
        "evidence does not prove intended behavior.",
    }
    if any(line.strip() and line.strip() not in allowed_tail
           for line in request_lines[2:]):
        return missing
    clause = re.fullmatch(
        r"[ \t]*Requirement[ \t]*:[ \t]*([^\r\n]{1,500})[ \t]*",
        request_lines[1], re.IGNORECASE,
    )
    if clause is None or sum(
        bool(re.search(r"(?i)\bRequirement[ \t]*:", line))
        for line in request_lines
    ) != 1:
        return missing
    clauses = [clause.group(1)]
    spec = project / "SPEC.md"
    try:
        if spec.is_symlink() or not spec.is_file() or spec.stat().st_size > 32768:
            return missing
        raw = spec.read_bytes()
        body = raw.decode("utf-8-sig").strip()
    except (OSError, UnicodeError, ValueError):
        return missing
    lines = re.fullmatch(r"Requirement[ \t]*:[ \t]*([^\r\n]{1,500})",
                         body, re.IGNORECASE)
    if lines is None:
        return missing
    # Python identifiers are case-sensitive: do not casefold their spelling.
    requirement = " ".join(clauses[0].split())
    if requirement != " ".join(lines.group(1).split()):
        return missing
    symbol_match = re.search(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]{0,120}\)", requirement
    )
    if symbol_match is None:
        return missing
    symbol = symbol_match.group(1)
    ignored = {
        "must", "should", "return", "returns", "argument", "arguments",
        "the", "two", "its", "this", "that", "with", "from", "and", "for",
        "function", "value", "values", "output", "result", "behavior", "input",
    }
    semantic_terms = sorted({
        word for word in re.findall(r"\b[a-z][a-z0-9_]{2,}\b", requirement.casefold())
        if word not in ignored and word != symbol.casefold()
    })
    if not semantic_terms:
        return missing
    # The declarative identity alone does not prove a semantic requirement.
    # Only this small, explicitly parsed numeric two-argument contract can
    # authorize deterministic arithmetic comparison in the source verifier.
    # All other natural-language contracts remain unproven, not guessed.
    rule = re.fullmatch(
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)"
        r"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)"
        r"\s+must\s+return\s+the\s+(sum|product)\s+of\s+"
        r"(?:the\s+two|its)\s+arguments\.?",
        requirement, re.IGNORECASE | re.ASCII,
    )
    parsed_rule = None
    if rule is not None and rule.group(2) != rule.group(3):
        parsed_rule = {
            "kind": "DIRECT_NUMERIC_BINARY_OPERATION",
            "symbol": rule.group(1),
            "arguments": [rule.group(2), rule.group(3)],
            "expected_operator": {"sum": "ADD", "product": "MULT"}[rule.group(4).lower()],
        }
    return {
        "status": "USER_SPEC_MATCHED",
        "path": "SPEC.md",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "symbol": symbol,
        "semantic_terms": semantic_terms[:12],
        "verifier_rule": parsed_rule,
    }


# Matching a location/evidence ID proves provenance, NEVER the correctness of
# arbitrary model prose. VERIFIED_BUG requires a separate narrow deterministic
# certificate over the actual local source bytes. There is no keyword bypass.
_TEST_EXPECTATION_BASIS = re.compile(
    r"\b(?:tests?|testcase|assert(?:s|ed|ion|ions)?|expect(?:s|ed|ation)?|expected)\b",
    re.IGNORECASE,
)
_EXPLICIT_BEHAVIOR_CONTRACT = re.compile(
    r"\b(?:specification|spec\.md|behavior(?:al)?\s+contract|"
    r"contract\s+(?:requires|violat\w*|defined|implied)|"
    r"requirements?|required\s+behavio[u]?r|"
    r"must\s+return|should\s+return|intended\s+behavio[u]?r)\b",
    re.IGNORECASE,
)
_ARITHMETIC_PROPOSITION = {
    "ADD": re.compile(r"\b(?:sum|addition|adds|adding)\b|(?<!\w)a\s*\+\s*b\b", re.I),
    "SUB": re.compile(r"\b(?:subtract\w*|subtraction|difference)\b|(?<!\w)a\s*-\s*b\b", re.I),
    "MULT": re.compile(r"\b(?:multipli\w*|product|multiply)\b|(?<!\w)a\s*\*\s*b\b", re.I),
}
_UNRESOLVED_TEST_CONTRACT_LIMIT = (
    "SOURCE_TEST_MISMATCH_UNRESOLVED: a test or alleged output expectation "
    "alone cannot decide whether source or test is wrong. Behavioral bug "
    "attribution requires an independent deterministic proof."
)
_UNPROVEN_BUG_LIMIT = (
    "SEMANTIC_PROOF_UNAVAILABLE: source provenance was observed, but this "
    "auditor cannot independently certify the alleged implementation defect."
)
_UNPROVEN_NONBUG_LIMIT = (
    "NONBUG_SEMANTIC_PROOF_UNAVAILABLE: model-authored improvement or strength "
    "claims without independently certified source facts are withheld, even "
    "when their evidence identifiers and file paths are genuine."
)
_NUMBERED_SOURCE_LINE = re.compile(r"^([1-9]\d{0,5}): (.*)$")
_OPERATOR_TYPES = {
    ast.Add: "ADD",
    ast.Sub: "SUB",
    ast.Mult: "MULT",
}
_OPERATOR_SYMBOLS = {"ADD": "+", "SUB": "-", "MULT": "*"}


def _verified_source_module(
    *,
    project: Path | None,
    location: str,
    evidence_ids: list[str],
    evidence_by_id: dict[str, dict[str, Any]],
) -> tuple[ast.Module, str, set[int]] | None:
    """Read the actual bounded file and compare every cited numbered source line.

    Never execute or import the target code. Do not trust an incomplete snippet
    as if it were a full source, or follow paths outside the selected project.
    """
    if not isinstance(project, Path) or not location.endswith(".py"):
        return None
    rel = Path(location)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        return None
    try:
        root = project.resolve(strict=True)
        candidate = root / rel
        if candidate.is_symlink() or not candidate.is_file():
            return None
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        if resolved.stat().st_size > 131072:
            return None
        raw_bytes = resolved.read_bytes()
        if b"\x00" in raw_bytes:
            return None
        encoding, _ = tokenize.detect_encoding(io.BytesIO(raw_bytes).readline)
        # EvidenceBroker line extraction is UTF-8-based. Abstain on source
        # encodings it cannot represent, instead of parsing a different AST.
        if encoding.lower().replace("_", "-") not in {"utf-8", "utf-8-sig"}:
            return None
        source = raw_bytes.decode("utf-8-sig")
        tree = ast.parse(raw_bytes, filename=location)
        # AST construction skips compiler-only validity checks, e.g. duplicate
        # parameters. Compile to a code object, but NEVER evaluate/import it.
        # Explicit flags prevent this module's future annotations from changing
        # the target's compilation semantics.
        compile(raw_bytes, location, "exec", flags=0, dont_inherit=True, optimize=0)
    except (OSError, ValueError, UnicodeError, SyntaxError, RecursionError, LookupError):
        return None
    source_lines = source.splitlines()
    observed_lines: set[int] = set()
    for evidence_id in evidence_ids:
        record = evidence_by_id.get(evidence_id)
        if not record or not record.get("found"):
            return None
        for hit in record.get("results") or []:
            if not isinstance(hit, dict):
                continue
            path = str(hit.get("file", "")).strip().replace("\\", "/")
            if path != location:
                continue
            snippet = str(hit.get("snippet", ""))
            if not snippet.strip() or len(snippet) > 6000:
                return None
            for text in snippet.splitlines():
                match = _NUMBERED_SOURCE_LINE.fullmatch(text)
                if match is None:
                    return None
                line = int(match.group(1))
                if line > len(source_lines) or source_lines[line - 1] != match.group(2):
                    return None
                observed_lines.add(line)
    if not observed_lines:
        return None
    return tree, hashlib.sha256(raw_bytes).hexdigest(), observed_lines


def _single_function_return(
    tree: ast.Module,
    symbol: str,
) -> tuple[ast.FunctionDef, ast.Return] | None:
    """Prove only bare, single-return, undecorated module-level functions.

    A later rebinding, second definition, decorators or nontrivial control flow
    can change runtime behavior, so conservative proof is refused.
    """
    body = list(tree.body)
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    # One-and-only-one top-level definition: later imports, assignments, or
    # redefinitions can shadow the callable and invalidate a snippet proof.
    if (len(body) != 1 or not isinstance(body[0], ast.FunctionDef)
            or body[0].name != symbol):
        return None
    fn = body[0]
    if (fn.decorator_list or fn.args.posonlyargs or fn.args.kwonlyargs
            or fn.args.kwarg is not None or fn.args.vararg is not None
            or fn.args.defaults or fn.args.kw_defaults
            or fn.returns is not None or getattr(fn, "type_params", [])
            or any(arg.annotation is not None for arg in fn.args.args)
            or len({arg.arg for arg in fn.args.args}) != len(fn.args.args)):
        # Even apparently harmless annotations/type parameters are outside
        # this proof subset; their evaluation can affect exported callables.
        return None
    body = fn.body
    if (len(body) == 2 and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return None
    return fn, body[0]


def _deterministic_source_bug_proof(
    *,
    project: Path | None,
    location: str,
    evidence_ids: list[str],
    evidence_by_id: dict[str, dict[str, Any]],
    reason: str,
    project_facts: dict[str, Any],
) -> dict[str, str] | None:
    """Bounded independent proof. Model words NEVER create semantic authority.

    Contract path: identical declared requirement in original user request and
    source SPEC.md + an AST-demonstrated direct arithmetic contradiction.
    Intrinsic path: a single unconditional return of builtin numeric / zero.
    Everything else ABSTAINS, including arbitrary dynamic Python or other
    programming languages. Model wording merely binds claim to this proof;
    final factual prose is reconstructed deterministically from the proof.
    """
    verified = _verified_source_module(
        project=project, location=location, evidence_ids=evidence_ids,
        evidence_by_id=evidence_by_id,
    )
    if verified is None:
        return None
    tree, source_sha256, observed_lines = verified

    # Recheck the trusted specification identity at the proof boundary,
    # not just once earlier during context construction (TOCTOU fail closed).
    current_spec_sha = None
    if isinstance(project, Path):
        spec_path = project / "SPEC.md"
        try:
            if (not spec_path.is_symlink() and spec_path.is_file()
                    and spec_path.stat().st_size <= 32768):
                current_spec_sha = hashlib.sha256(spec_path.read_bytes()).hexdigest()
        except OSError:
            current_spec_sha = None
    authority = project_facts.get("behavioral_contract_authority")
    rule = authority.get("verifier_rule") if isinstance(authority, dict) else None
    if (isinstance(rule, dict)
            and authority.get("status") == "USER_SPEC_MATCHED"
            and authority.get("path") == "SPEC.md"
            and isinstance(authority.get("sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", authority["sha256"])
            and authority["sha256"] == current_spec_sha
            and rule.get("kind") == "DIRECT_NUMERIC_BINARY_OPERATION"
            and isinstance(rule.get("symbol"), str)
            and isinstance(rule.get("arguments"), list)
            and len(rule["arguments"]) == 2
            and all(isinstance(arg, str) and re.fullmatch(r"[a-zA-Z_]\w*", arg)
                    for arg in rule["arguments"])
            and rule.get("expected_operator") in {"ADD", "MULT"}
            and rule["symbol"] == authority.get("symbol")):
        matched = _single_function_return(tree, rule["symbol"])
        if matched is not None:
            fn, ret = matched
            args = [arg.arg for arg in fn.args.args]
            body = ret.value
            if (fn.lineno in observed_lines and ret.lineno in observed_lines
                    and args == rule["arguments"] and isinstance(body, ast.BinOp)
                    and isinstance(body.left, ast.Name)
                    and isinstance(body.right, ast.Name)
                    and body.left.id == args[0] and body.right.id == args[1]):
                actual = _OPERATOR_TYPES.get(type(body.op))
                expected = rule["expected_operator"]
                if actual is not None and actual != expected:
                    # The claim must identify the proven subject and arithmetic
                    # issue. Synonyms never authorize; source AST + SPEC do.
                    if (re.search(r"\b" + re.escape(fn.name) + r"\b", reason, re.I)
                            and _ARITHMETIC_PROPOSITION[actual].search(reason)
                            and _ARITHMETIC_PROPOSITION[expected].search(reason)):
                        return {
                            "kind": "DECLARED_ARITHMETIC_CONTRACT_MISMATCH",
                            "source_sha256": source_sha256,
                            "authority_sha256": authority["sha256"],
                            "symbol": fn.name,
                            "arguments": ",".join(args),
                            "expected_operator": expected,
                            "observed_operator": actual,
                        }

    # Prove a guaranteed builtin runtime exception, independent of a contract.
    # The statement is about the failure on invocation, not caller intent.
    if not re.search(r"\bZeroDivisionError\b|division\s+by\s+zero",
                     reason, re.IGNORECASE):
        return None
    matches: list[tuple[str, ast.Return]] = []
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        found = _single_function_return(tree, fn.name)
        if found is None:
            continue
        proven_fn, ret = found
        if proven_fn.lineno not in observed_lines or ret.lineno not in observed_lines:
            continue
        body = ret.value
        if not (isinstance(body, ast.BinOp)
                and isinstance(body.op, (ast.Div, ast.FloorDiv, ast.Mod))
                and isinstance(body.left, ast.Constant)
                and isinstance(body.right, ast.Constant)
                and type(body.left.value) in (int, float)
                and type(body.right.value) in (int, float)
                and body.right.value == 0):
            continue
        if re.search(r"\b" + re.escape(fn.name) + r"\b", reason):
            matches.append((fn.name, ret))
    if len(matches) != 1:
        return None
    return {
        "kind": "UNCONDITIONAL_ZERO_DIVISION",
        "source_sha256": source_sha256,
        "symbol": matches[0][0],
        "expression": "constant numeric denominator equals zero",
    }



# Semantic authorization is not limited to VERIFIED_BUG. Both KEEP_AS_IS and
# improvement suggestions must independently establish exactly what is stated.
# A real EvidenceBroker ID is necessary for provenance but not sufficient for
# a factual assertion. The grammar below intentionally accepts a small number
# of *literal, observable* claims, not open-ended model narrative.
_RETURN_OBSERVATION = re.compile(
    r"^(?:Source contains a return|The source uses return)\s+"
    r"([A-Za-z_]\w*)\s*([+\-*])\s*([A-Za-z_]\w*)"
    r"(?: statement)?\.?$",
    re.IGNORECASE,
)
_MODULE_DOCSTRING_ABSENCE = re.compile(
    r"^(?:This short source|The source|This module)\s+"
    r"has no module-level docstring\.?$",
    re.IGNORECASE,
)
_MODULE_DOCSTRING_RECOMMENDATION = re.compile(
    r"^Add a module docstring\.?$",
    re.IGNORECASE,
)


def _nonbug_semantic_proof(
    *,
    kind: str,
    location: str,
    reason: str,
    recommendation: str,
    project: Path | None,
    evidence_ids: list[str],
    evidence_by_id: dict[str, dict[str, Any]],
) -> tuple[dict[str, str], str, str, str] | None:
    """Prove a bounded source structure and replace all model-authored prose.

    An observation of source syntax does not certify intended behavior,
    test success, or a deployment's reliability. Claims outside this small
    grammar remain UNVERIFIED, even with impeccable file/ID provenance.
    """
    verified = _verified_source_module(
        project=project, location=location, evidence_ids=evidence_ids,
        evidence_by_id=evidence_by_id,
    )
    if verified is None or _is_test_file(location):
        return None
    tree, sha, observed_lines = verified

    # KEEP_AS_IS is a preservation/correctness endorsement, not a neutral
    # source syntax observation. This checker has no positive behavioral
    # certificate for general software, so it must abstain on every strength.
    if kind == "strength":
        return None

    if kind in {"IMPROVEMENT", "OPTIONAL_IDEA"}:
        if (_MODULE_DOCSTRING_ABSENCE.fullmatch(reason.strip())
                and _MODULE_DOCSTRING_RECOMMENDATION.fullmatch(recommendation.strip())
                and ast.get_docstring(tree) is None):
            proof = {"kind": "MODULE_DOCSTRING_ABSENT", "source_sha256": sha}
            return (
                proof, f"Module documentation: {location}",
                f"AST inspection of cited source {location} confirms that "
                "the module has no module-level docstring.",
                f"Consider adding a module-level docstring to {location}.",
            )
    return None


def _canonical_bug_claim(proof: dict[str, str]) -> tuple[str, str, str]:
    kind = proof["kind"]
    if kind == "UNCONDITIONAL_ZERO_DIVISION":
        symbol = proof["symbol"]
        return (
            "Deterministic runtime failure",
            f"Function {symbol} unconditionally evaluates a numeric division "
            "with a zero denominator, so invoking it raises ZeroDivisionError.",
            "Review and replace the unconditional zero-denominator expression "
            "if this callable is expected to return normally.",
        )
    symbol, args = proof["symbol"], proof["arguments"]
    actual = _OPERATOR_SYMBOLS[proof["observed_operator"]]
    expected = _OPERATOR_SYMBOLS[proof["expected_operator"]]
    operation = {"ADD": "sum", "MULT": "product"}[proof["expected_operator"]]
    return (
        "Declared arithmetic contract mismatch",
        f"Trust-matched requirement for {symbol}({args}) specifies the {operation}, "
        f"while its cited direct return uses '{actual}' rather than '{expected}'. "
        "This is an AST-verified contradiction in hash-attested local source bytes.",
        f"Review replacing '{actual}' with '{expected}' in the direct return "
        f"of {symbol}({args}) to satisfy the trust-matched requirement.",
    )


_PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
_CONFIDENCE_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
_TYPE_ORDER = {"VERIFIED_BUG": 0, "IMPROVEMENT": 1, "OPTIONAL_IDEA": 2}


def _role_prefix(role_name: str) -> str:
    return {
        "Universe Primer": "UP",
        "LUA Programming GOD": "LUA",
        "Resume": "RES",
    }.get(role_name, "AUD")


def evidence_index(evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    conflicted: set[str] = set()
    for row in evidence:
        if not isinstance(row, dict):
            continue
        evidence_id = str(row.get("evidence_id", "")).strip()
        if not evidence_id or evidence_id in conflicted:
            continue
        previous = out.get(evidence_id)
        if previous is not None and previous != row:
            # Conflicting provenance must never become VERIFIED by list order.
            out.pop(evidence_id)
            conflicted.add(evidence_id)
        else:
            # Exact repeats are harmless; distinct IDs remain usable.
            out[evidence_id] = row
    return out


def evidence_files(row: dict[str, Any]) -> set[str]:
    if not row.get("found"):
        return set()
    files: set[str] = set()
    for hit in row.get("results") or []:
        if not isinstance(hit, dict):
            continue
        rel = str(hit.get("file", "")).strip().replace("\\", "/")
        if rel:
            files.add(rel)
    return files


def _contradicted_by_project_facts(text: str, project_facts: dict[str, Any]) -> str | None:
    t = text.lower()
    checks = [
        ("has_automated_tests", ["no automated test", "not using automated test", "missing automated tests"], "automated tests exist"),
        ("has_git_support", ["no version control", "not using version control", "no git support"], "Git support exists"),
        ("has_sandbox_controls", ["no sandbox", "not using a sandbox", "sandbox is missing"], "sandbox controls exist"),
        ("has_langgraph", ["no langgraph", "not using langgraph", "not using any existing libraries", "not using existing libraries"], "LangGraph is present"),
        ("has_clipboard_bridge", ["no clipboard bridge", "clipboard bridge is missing"], "clipboard bridge exists"),
        ("has_stop_cancel", ["no stop", "no cancel", "stop/cancel is missing"], "STOP/CANCEL exists"),
    ]
    for fact_key, phrases, fact_text in checks:
        if project_facts.get(fact_key) and any(p in t for p in phrases):
            return fact_text
    return None



# These gates reject a narrow class of *observable* test-claim contradictions.
# Cited-file provenance alone is never a proof that a proposed edit is correct.
_CLAIMS_EXPECTATION_ABSENT = re.compile(
    r'\b(?:no|missing|absent|without)\b.{0,110}\bexpected\s+(?:result|output|value)\b'
    r'|\bexpected\s+(?:result|output|value)\b.{0,140}'
    r'\b(?:not\s+(?:provided|specified|included|present)|missing|absent)\b',
    re.IGNORECASE | re.DOTALL,
)
_REWRITES_EXPECTATION = re.compile(
    r'\b(?:change|changing|update|adjust|modify|replace|correct|fix|set)\b'
    # The expected result must be the edit target, not merely the desired
    # outcome of fixing *source/implementation* code.
    r'(?:(?!\b(?:source|implementation|function|code|method)\b).){0,140}'
    r'\b(?:expected\s+(?:output|result|value)'
    r'|assert(?:ion|ed)?\s+(?:value|result))\b',
    re.IGNORECASE | re.DOTALL,
)
_NEGATED_EDIT_LEAD = re.compile(
    r"\b(?:do\s+not|don't|never|avoid)\s*$",
    re.IGNORECASE,
)


def _has_explicit_expected(tree: ast.AST) -> bool:
    """Only AST-executable assertions with literal expected operands count."""
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"assertEqual", "assertEquals", "assertAlmostEqual"}
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)):
            return True
        if isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
            comparison = node.test
            if (any(isinstance(op, (ast.Eq, ast.NotEq)) for op in comparison.ops)
                    and any(isinstance(x, ast.Constant)
                            for x in [comparison.left, *comparison.comparators])):
                return True
    return False


def _requests_expectation_rewrite(text: str) -> bool:
    # Negation applies to each edit clause, not every edit in the message.
    for clause in re.split(r"(?<=[.!?;])\s+", str(text or "")):
        for change in _REWRITES_EXPECTATION.finditer(clause):
            if not _NEGATED_EDIT_LEAD.search(clause[:change.start()]):
                return True
    return False


def _is_test_file(path: str) -> bool:
    parts = str(path).replace("\\", "/").strip("/").lower().split("/")
    name = parts[-1]
    return (
        any(p in {"tests", "test", "__tests__"} for p in parts[:-1])
        or name.startswith(("test_", "spec_"))
        or name.endswith(("_test.py", "_test.go", "_test.rs"))
        or ".test." in name or ".spec." in name
    )


def _test_claim_contradictions(
    location: str,
    evidence_ids: list[str],
    evidence_by_id: dict[str, dict[str, Any]],
    reason: str,
    recommendation: str,
) -> list[str]:
    """Refuse some provably unsafe test assertions; never certify semantics."""
    if not _is_test_file(location):
        return []
    notes: list[str] = []
    matching_snippets: list[str] = []
    independent_evidence = False
    for eid in evidence_ids:
        row = evidence_by_id.get(eid)
        if not isinstance(row, dict) or not row.get("found"):
            continue
        for hit in row.get("results") or []:
            if not isinstance(hit, dict):
                continue
            file = str(hit.get("file", "")).strip().replace("\\", "/")
            snippet = str(hit.get("snippet", ""))
            if file == location:
                matching_snippets.append(snippet)
            elif file and snippet.strip() and not _is_test_file(file):
                independent_evidence = True

    if _CLAIMS_EXPECTATION_ABSENT.search(reason):
        for snippet in matching_snippets:
            # Keep indentation when removing EvidenceBroker's "12: " prefix.
            plain = re.sub(r"(?m)^[ \t]*\d+: ?", "", snippet)
            try:
                parsed = ast.parse(textwrap.dedent(plain))
            except (SyntaxError, ValueError, TypeError, RecursionError):
                # An incomplete snippet cannot be safely used as a proof.
                continue
            # Keep class identity: two independent test classes may both
            # define test_result, yet only one contains an expectation.
            functions: list[tuple[str, ast.AST]] = []
            for node in parsed.body:
                if isinstance(node, ast.ClassDef):
                    functions.extend(
                        (node.name, child) for child in node.body
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and child.name.startswith("test_")
                    )
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                    functions.append(("", node))
            qualified = set(re.findall(
                r"\b([A-Za-z_]\w*)\.(test_[A-Za-z_]\w*)\b", reason,
            ))
            named = set(re.findall(r"\btest_[A-Za-z_]\w*\b", reason))
            if qualified:
                matches = [fn for owner, fn in functions if (owner, fn.name) in qualified]
                scopes = matches if len(qualified) == 1 and len(matches) == 1 else []
            elif named:
                matches = [fn for _, fn in functions if fn.name in named]
                # Multiple methods with the same short name are ambiguous.
                scopes = matches if len(named) == 1 and len(matches) == 1 else []
            elif len(functions) == 1:
                scopes = [functions[0][1]]
            elif not functions:
                scopes = [parsed]
            else:
                # Multiple unnamed cases: do not generalize an expectation
                # from one test to another.
                scopes = []
            if any(_has_explicit_expected(scope) for scope in scopes):
                notes.append("expected_result_present_in_cited_test")
                break

    if _requests_expectation_rewrite(reason) or _requests_expectation_rewrite(recommendation):
        # Current implementation/source behavior is not the intended contract.
        # This validator has neither an independent semantic oracle nor human
        # authorization to rewrite expected test behavior.
        notes.append("test_expectation_change_needs_semantic_authority")
        if not independent_evidence:
            notes.append("test_expectation_change_missing_independent_evidence")
    return notes


# Line-qualified model locations are allowed only when the claimed project file
# AND the actual line(s) are visibly backed by an unconflicted cited evidence ID.
# Evidence identity is authoritative for *provenance*, not claim correctness.
_PATH_LINE_LOCATION = re.compile(r"^(.+):([1-9]\d{0,5})(?:-([1-9]\d{0,5}))?$")
_BARE_LINE_LOCATION = re.compile(r"^line\s+([1-9]\d{0,5})$", re.IGNORECASE)
_SNIPPET_LINE_PREFIX = re.compile(r"(?m)^[ \t]*([1-9]\d{0,5}):")


def _canonical_cited_audit_location(
    location: str,
    evidence_ids: list[str],
    evidence_by_id: dict[str, dict[str, Any]],
    valid_files: set[str],
) -> str:
    """Canonical project path only for an evidence-backed explicit line locator.

    Keep unknown or ambiguous locators unchanged so existing validation rejects
    them. In particular, a generic "line N" must never guess among two files.
    """
    if location == "MULTIPLE" or location in valid_files:
        return location

    qualified = _PATH_LINE_LOCATION.fullmatch(location)
    bare = _BARE_LINE_LOCATION.fullmatch(location)
    if qualified:
        file = qualified.group(1)
        begin = int(qualified.group(2))
        end = int(qualified.group(3) or qualified.group(2))
        if file not in valid_files:
            return location
    elif bare:
        begin = end = int(bare.group(1))
        if not evidence_ids:
            return location
        possible_files: set[str] = set()
        for evidence_id in evidence_ids:
            row = evidence_by_id.get(evidence_id)
            if row is None or not row.get("found"):
                return location
            row_files = evidence_files(row)
            if not row_files:
                return location
            possible_files.update(row_files)
        if len(possible_files) != 1:
            return location
        file = next(iter(possible_files))
        if file not in valid_files:
            return location
    else:
        return location

    # Require each claimed line to appear in the cited, existing file's
    # numbered snippet. Large or reversed ranges are never guessed through.
    if end < begin or end - begin > 10:
        return location
    required = set(range(begin, end + 1))
    for evidence_id in evidence_ids:
        row = evidence_by_id.get(evidence_id)
        if row is None or not row.get("found"):
            continue
        for hit in row.get("results") or []:
            if not isinstance(hit, dict):
                continue
            if str(hit.get("file", "")).strip().replace("\\", "/") != file:
                continue
            snippet = str(hit.get("snippet", ""))
            visible = {int(m.group(1)) for m in _SNIPPET_LINE_PREFIX.finditer(snippet)}
            if required.issubset(visible):
                return file
    return location


def _valid_evidence_for_location(
    location: str,
    evidence_ids: list[str],
    evidence_by_id: dict[str, dict[str, Any]],
) -> tuple[list[str], set[str]]:
    valid_ids: list[str] = []
    files: set[str] = set()
    for evidence_id in evidence_ids:
        row = evidence_by_id.get(evidence_id)
        if row is None or not row.get("found"):
            continue
        row_files = evidence_files(row)
        if not row_files:
            continue
        valid_ids.append(evidence_id)
        files.update(row_files)
    if location == "MULTIPLE":
        return (valid_ids, files) if len(files) >= 2 else ([], files)
    matching = [eid for eid in valid_ids if location in evidence_files(evidence_by_id[eid])]
    return matching, files


def validate_specialist_analysis(
    *,
    role_name: str,
    raw: dict[str, Any],
    valid_files: set[str],
    evidence: list[dict[str, Any]],
    project_facts: dict[str, Any],
    project: Path | None = None,
) -> dict[str, Any]:
    """Turn model audit output into provenance-checked internal records.

    Findings never become synthesis inputs unless a real EvidenceBroker ID resolves to
    the claimed project-relative location and the claim is not contradicted by known
    project facts. Stable IDs are assigned by code, not by the model.
    """
    status = str(raw.get("status", "READY")).upper().strip()
    if status not in {"READY", "NEED_EVIDENCE"}:
        status = "READY"

    by_id = evidence_index(evidence)
    prefix = _role_prefix(role_name)
    findings: list[dict[str, Any]] = []
    for idx, row in enumerate(raw.get("findings") or [], 1):
        if not isinstance(row, dict):
            continue
        finding_type = str(row.get("type", "OPTIONAL_IDEA")).upper().strip()
        if finding_type not in _TYPE_ORDER:
            finding_type = "OPTIONAL_IDEA"
        priority = str(row.get("priority", "LOW")).upper().strip()
        if priority not in _PRIORITY_ORDER:
            priority = "LOW"
        confidence = str(row.get("confidence", "LOW")).upper().strip()
        if confidence not in _CONFIDENCE_ORDER:
            confidence = "LOW"
        location = str(row.get("location", "")).strip().replace("\\", "/")[:240]
        requested_ids = [str(x).strip() for x in (row.get("evidence_ids") or []) if str(x).strip()][:6]
        location = _canonical_cited_audit_location(location, requested_ids, by_id, valid_files)
        matched_ids, evidence_locations = _valid_evidence_for_location(location, requested_ids, by_id)
        reason = str(row.get("reason", "")).strip()[:520]
        recommendation = str(row.get("recommendation", "")).strip()[:520]
        area = str(row.get("area", "")).strip()[:180]

        notes: list[str] = []
        location_exists = location in valid_files or (location == "MULTIPLE" and len(evidence_locations) >= 2)
        if not location_exists:
            notes.append("location_not_in_project")
        if not matched_ids:
            notes.append("no_evidence_id_supports_location")
        if (
            not isinstance(row.get("evidence_ids"), list)
            or len(row.get("evidence_ids") or []) > 6
            or not requested_ids
            or len(matched_ids) != len(requested_ids)
            or any(eid not in by_id for eid in requested_ids)
        ):
            notes.append("invalid_or_conflicted_cited_id")
        contradicted = _contradicted_by_project_facts(f"{area} {reason} {recommendation}", project_facts)
        if contradicted:
            notes.append(f"contradicted_by_project_facts:{contradicted}")
        notes.extend(_test_claim_contradictions(
            location, requested_ids, by_id, reason, recommendation,
        ))
        semantic_proof = None
        if finding_type == "VERIFIED_BUG":
            if _is_test_file(location):
                notes.append("test_file_bug_needs_independent_semantic_proof")
            elif not notes:
                semantic_proof = _deterministic_source_bug_proof(
                    project=project,
                    location=location,
                    evidence_ids=matched_ids,
                    evidence_by_id=by_id,
                    reason=reason,
                    project_facts=project_facts,
                )
                if semantic_proof is None:
                    notes.append("source_bug_lacks_deterministic_proof")
                    # This explanation is NOT the authority decision. The
                    # actual decision above is unconditional fail-closed.
                    if _TEST_EXPECTATION_BASIS.search(reason):
                        notes.append("source_test_mismatch_no_independent_contract")
                        if (isinstance(project_facts.get("behavioral_contract_authority"), dict)
                                and project_facts["behavioral_contract_authority"].get("status") == "USER_SPEC_MATCHED"):
                            notes.append("source_test_claim_not_bound_to_contract")
                    elif _EXPLICIT_BEHAVIOR_CONTRACT.search(reason):
                        notes.append("source_defect_no_independent_behavior_contract")
                else:
                    area, reason, recommendation = _canonical_bug_claim(semantic_proof)
                    if _PRIORITY_ORDER[priority] < _PRIORITY_ORDER["MEDIUM"]:
                        priority = "MEDIUM"
            elif _TEST_EXPECTATION_BASIS.search(reason):
                notes.append("source_test_mismatch_no_independent_contract")
        elif not notes:
            result = _nonbug_semantic_proof(
                kind=finding_type,
                location=location,
                reason=reason,
                recommendation=recommendation,
                project=project,
                evidence_ids=matched_ids,
                evidence_by_id=by_id,
            )
            if result is None:
                notes.append("nonbug_claim_lacks_deterministic_semantic_proof")
            else:
                semantic_proof, area, reason, recommendation = result
                # A docstring opportunity demonstrates no performance,
                # reliability or otherwise-working behavior: it is optional.
                if semantic_proof.get("kind") == "MODULE_DOCSTRING_ABSENT":
                    finding_type = "OPTIONAL_IDEA"
                if _PRIORITY_ORDER[priority] < _PRIORITY_ORDER["LOW"]:
                    priority = "LOW"
        else:
            notes.append("nonbug_claim_lacks_deterministic_semantic_proof")

        verification = "VERIFIED" if not notes else "UNVERIFIED"
        if verification == "UNVERIFIED":
            confidence = "LOW"
            priority = "LOW"

        findings.append({
            "finding_id": f"F-{prefix}-{idx:03d}",
            "specialist": role_name,
            "type": finding_type,
            "priority": priority,
            "area": area,
            "location": location,
            "evidence_ids": matched_ids,
            "reason": reason,
            "recommendation": recommendation,
            "confidence": confidence,
            "verification": verification,
            "validation_notes": notes,
            "semantic_proof": semantic_proof,
        })

    strengths: list[dict[str, Any]] = []
    for idx, row in enumerate(raw.get("keep_as_is") or [], 1):
        if not isinstance(row, dict):
            continue
        location = str(row.get("location", "")).strip().replace("\\", "/")[:240]
        requested_ids = [str(x).strip() for x in (row.get("evidence_ids") or []) if str(x).strip()][:6]
        location = _canonical_cited_audit_location(location, requested_ids, by_id, valid_files)
        matched_ids, evidence_locations = _valid_evidence_for_location(location, requested_ids, by_id)
        notes: list[str] = []
        location_exists = location in valid_files or (location == "MULTIPLE" and len(evidence_locations) >= 2)
        if not location_exists:
            notes.append("location_not_in_project")
        if not matched_ids:
            notes.append("no_evidence_id_supports_location")
        reason = str(row.get("reason", "")).strip()[:420]
        notes.extend(_test_claim_contradictions(
            location, requested_ids, by_id, reason, "",
        ))
        if (
            not isinstance(row.get("evidence_ids"), list)
            or len(row.get("evidence_ids") or []) > 6
            or not requested_ids
            or len(matched_ids) != len(requested_ids)
            or any(eid not in by_id for eid in requested_ids)
        ):
            notes.append("invalid_or_conflicted_cited_id")
        semantic_proof = None
        if not notes:
            # No structural observation can by itself justify KEEP_AS_IS.
            notes.append("strength_lacks_positive_behavioral_proof")
            notes.append("nonbug_claim_lacks_deterministic_semantic_proof")
        if notes and "nonbug_claim_lacks_deterministic_semantic_proof" not in notes:
            # Do not mistake an invalid source reference for proof.
            notes.append("nonbug_claim_not_semantically_authorized")
        confidence = str(row.get("confidence", "LOW")).upper().strip()
        if confidence not in _CONFIDENCE_ORDER:
            confidence = "LOW"
        if notes:
            confidence = "LOW"
        strengths.append({
            "strength_id": f"K-{prefix}-{idx:03d}",
            "specialist": role_name,
            "area": area if semantic_proof is not None else str(row.get("area", "")).strip()[:180],
            "location": location,
            "evidence_ids": matched_ids,
            "reason": reason,
            "confidence": confidence,
            "verification": "VERIFIED" if not notes else "UNVERIFIED",
            "validation_notes": notes,
            "semantic_proof": semantic_proof,
        })

    requests = [x for x in (raw.get("evidence_requests") or []) if isinstance(x, dict)][:3]
    unresolved_test = any(
        "source_test_mismatch_no_independent_contract" in finding["validation_notes"]
        for finding in findings
    )
    missing_proof = any(
        "source_bug_lacks_deterministic_proof" in finding["validation_notes"]
        for finding in findings
    )
    missing_nonbug_proof = any(
        "nonbug_claim_lacks_deterministic_semantic_proof" in row["validation_notes"]
        for row in [*findings, *strengths]
    )
    # Raw specialist audit_limits are unverified model claims, not facts.
    # Retain only deterministic validation limitations in public reports.
    unverified_model_limits = [
        str(x).strip() for x in (raw.get("audit_limits") or [])
        if str(x).strip()
    ][:4]
    limits: list[str] = []
    for note, exists in ((_UNRESOLVED_TEST_CONTRACT_LIMIT, unresolved_test),
                         (_UNPROVEN_BUG_LIMIT, missing_proof),
                         (_UNPROVEN_NONBUG_LIMIT, missing_nonbug_proof)):
        if exists:
            limits = [note] + [item for item in limits if item != note][:3]
    return {
        "status": status,
        "summary": str(raw.get("summary", "")).strip()[:900],
        "findings": findings[:8],
        "keep_as_is": strengths[:6],
        "evidence_requests": requests,
        "audit_limits": limits,
        "unverified_model_limits": unverified_model_limits,
    }


_PENDING_CODES = {
    "EVIDENCE_NOT_FOUND", "REQUEST_NOT_ATTEMPTED", "REQUEST_PENDING",
    "SPECIALIST_NEEDS_EVIDENCE", "INVALID_EVIDENCE_REQUEST",
}


def _request_locator(row: dict[str, Any]) -> dict[str, str]:
    kind = str(row.get("kind", "")).strip().lower()
    raw_query = row.get("query")
    if not isinstance(raw_query, str):
        return {"kind": "unknown", "query": ""}
    query = raw_query.strip()
    # Locator identity is never truncated. In particular, an overlong curated
    # path must not be confused with the existing 160-character prefix file.
    if (kind not in {"path", "symbol", "text"} or not query
            or len(query) > 160 or any(c in query for c in "\x00\r\n")):
        return {"kind": "unknown", "query": ""}
    return {"kind": kind, "query": query}


def _broker_fulfilled_request(loc: dict[str, str], observation: dict[str, Any]) -> bool:
    """Require an exact target and broker-certified successful read, not found=true.

    A fuzzy path hit is useful search context, but cannot satisfy an explicit
    file request. Path spelling is deliberately case-sensitive even on Windows:
    refusing an ambiguous request is safer than certifying the wrong file.
    Only *host-owned* EvidenceBroker records reach this audit boundary.
    """
    if observation.get("found") is not True or not isinstance(observation.get("results"), list):
        return False
    kind, query = loc["kind"], loc["query"]
    for hit in observation["results"]:
        if not isinstance(hit, dict) or hit.get("read_ok") is not True:
            continue
        actual = hit.get("file")
        if not isinstance(actual, str) or not actual or "\x00" in actual:
            continue
        if kind == "path":
            # Broker emits project-relative POSIX paths. Accept slash variants
            # but do not casefold, basename-match, or resolve arbitrary aliases.
            if actual.replace("\\", "/") == query.replace("\\", "/"):
                return True
        elif kind in {"text", "symbol"}:
            line = hit.get("line")
            snippet = hit.get("snippet")
            if (type(line) is int and line > 0 and isinstance(snippet, str)
                    and any(part.startswith(f"{line}: ")
                            and query.casefold() in part[len(f"{line}: "):].casefold()
                            for part in snippet.splitlines())):
                return True
    return False


def unfulfilled_audit_requests(
    requests: list[dict[str, Any]], observations: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Only a successful and relevant broker lookup completes a bounded request."""
    result = []
    for requested in requests:
        loc = _request_locator(requested)
        if loc["kind"] == "unknown":
            code = "INVALID_EVIDENCE_REQUEST"
        else:
            matches = [r for r in observations if isinstance(r, dict)
                       and _request_locator(r)["kind"] == loc["kind"]
                       and (_request_locator(r)["query"] == loc["query"]
                            if loc["kind"] == "path"
                            else _request_locator(r)["query"].casefold() == loc["query"].casefold())]
            if any(_broker_fulfilled_request(loc, r) for r in matches):
                continue
            code = "EVIDENCE_NOT_FOUND" if matches else "REQUEST_NOT_ATTEMPTED"
        result.append({**loc, "reason_code": code})
    return result


def _pending_evidence(analyses: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Separate unfinished evidence work from accepted/rejected factual claims."""
    pending = []
    for role, analysis in analyses.items():
        rows = []
        for row in analysis.get("unfulfilled_evidence_requests") or []:
            code = row.get("reason_code")
            if code not in _PENDING_CODES:
                code = "INVALID_EVIDENCE_REQUEST"
            rows.append({**_request_locator(row), "reason_code": code})
        for row in analysis.get("evidence_requests") or []:
            loc = _request_locator(row)
            rows.append({**loc, "reason_code": "REQUEST_PENDING" if loc["kind"] != "unknown"
                         else "INVALID_EVIDENCE_REQUEST"})
        if analysis.get("status") == "NEED_EVIDENCE":
            rows.append({"kind": "unknown", "query": "",
                         "reason_code": "SPECIALIST_NEEDS_EVIDENCE"})
        for row in rows:
            item = {"specialist": str(role)[:180], **row}
            if item not in pending:
                pending.append(item)
    if len(pending) > 64:
        raise ValueError("AUDIT_PENDING_REQUEST_LIMIT")
    return pending


def _completion_metadata(validated: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
    pending = validated.get("pending_evidence_requests") or []
    if not isinstance(pending, list) or len(pending) > 64:
        raise ValueError("AUDIT_PENDING_REQUEST_INVALID")
    canonical = []
    for row in pending:
        if not isinstance(row, dict) or row.get("reason_code") not in _PENDING_CODES:
            raise ValueError("AUDIT_PENDING_REQUEST_INVALID")
        item = {"specialist": str(row.get("specialist", ""))[:180],
                **_request_locator(row), "reason_code": row["reason_code"]}
        if item not in canonical:
            canonical.append(item)
    return ("INCOMPLETE" if canonical else "COMPLETE"), canonical


def collect_validated(analyses: dict[str, dict[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    strengths: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    limits: list[str] = []
    for role_name, analysis in analyses.items():
        for row in analysis.get("findings") or []:
            if row.get("verification") == "VERIFIED":
                findings.append(dict(row))
            else:
                rejected.append({"kind": "finding", **dict(row)})
        for row in analysis.get("keep_as_is") or []:
            if row.get("verification") == "VERIFIED":
                strengths.append(dict(row))
            else:
                rejected.append({"kind": "strength", **dict(row)})
        # Only validator-owned limitations can become report facts.
        trusted_limits = {
            _UNRESOLVED_TEST_CONTRACT_LIMIT, _UNPROVEN_BUG_LIMIT,
            _UNPROVEN_NONBUG_LIMIT,
        }
        for text in analysis.get("audit_limits") or []:
            t = str(text).strip()
            if t in trusted_limits and t not in limits:
                limits.append(t)
    return {
        "findings": findings,
        "strengths": strengths,
        "rejected": rejected,
        "audit_limits": limits[:8],
        "pending_evidence_requests": _pending_evidence(analyses),
    }


def synthesis_input(validated: dict[str, Any]) -> dict[str, Any]:
    """Only provenance-checked records go to the synthesis model."""
    return {
        "validated_findings": [
            {k: row[k] for k in (
                "finding_id", "specialist", "type", "priority", "area", "location",
                "evidence_ids", "reason", "recommendation", "confidence"
            )}
            for row in validated.get("findings") or []
        ],
        "validated_strengths": [
            {k: row[k] for k in (
                "strength_id", "specialist", "area", "location", "evidence_ids", "reason", "confidence"
            )}
            for row in validated.get("strengths") or []
        ],
    }


def _clean_id_group(values: list[Any], registry: dict[str, dict[str, Any]], max_items: int = 4) -> list[str]:
    out: list[str] = []
    for value in values:
        ident = str(value).strip()
        if ident in registry and ident not in out:
            out.append(ident)
        if len(out) >= max_items:
            break
    return out


def _finding_rank(row: dict[str, Any]) -> tuple[int, int, str]:
    return (_PRIORITY_ORDER[row["priority"]], _TYPE_ORDER[row["type"]],
            str(row["finding_id"]))


def _semantic_issue_identity(row: dict[str, Any]) -> tuple[Any, ...] | None:
    """Only exact same verdict and proof-backed issue may be grouped.

    Location or generic area alone is insufficient. Distinct source symbols
    and a documentation suggestion versus a bug must never be merged.
    """
    proof = row.get("semantic_proof")
    if not isinstance(proof, dict) or not proof.get("kind"):
        return None
    return (
        row.get("type"), row.get("location"), proof.get("kind"),
        proof.get("source_sha256"), proof.get("authority_sha256"),
        proof.get("symbol"), proof.get("arguments"),
        proof.get("expected_operator"), proof.get("observed_operator"),
    )


def _group_is_related(source_ids: list[str], registry: dict[str, dict[str, Any]]) -> bool:
    if len(source_ids) <= 1:
        return True
    keys = [_semantic_issue_identity(registry[x]) for x in source_ids]
    return keys[0] is not None and all(key == keys[0] for key in keys[1:])


def _combine_findings(source_ids: list[str], registry: dict[str, dict[str, Any]], group_no: int) -> dict[str, Any]:
    rows = [registry[x] for x in source_ids]
    types = sorted((r["type"] for r in rows), key=lambda x: _TYPE_ORDER[x])
    priorities = sorted((r["priority"] for r in rows), key=lambda x: _PRIORITY_ORDER[x])
    confidences = sorted((r["confidence"] for r in rows), key=lambda x: _CONFIDENCE_ORDER[x])
    areas: list[str] = []
    locations: list[str] = []
    evidence_ids: list[str] = []
    reasons: list[str] = []
    recommendations: list[str] = []
    for r in rows:
        for area in [r["area"]]:
            if area and area not in areas:
                areas.append(area)
        if r["location"] and r["location"] not in locations:
            locations.append(r["location"])
        for eid in r["evidence_ids"]:
            if eid not in evidence_ids:
                evidence_ids.append(eid)
        reasons.append(f"[{r['finding_id']} / {r['specialist']}] {r['reason']}")
        recommendations.append(f"[{r['finding_id']}] {r['recommendation']}")
    return {
        "finding_id": f"G-{group_no:03d}",
        "type": types[0],
        "priority": priorities[0],
        "area": " / ".join(areas)[:220],
        "location": locations[0] if len(locations) == 1 else "MULTIPLE",
        "evidence_ids": evidence_ids[:12],
        "source_finding_ids": source_ids,
        "reason": " | ".join(reasons)[:1100],
        "recommendation": " | ".join(recommendations)[:1100],
        "confidence": confidences[0],
    }


def _canonical_audit_limits(
    validated: dict[str, Any],
    project_facts: dict[str, Any],
    omitted: list[dict[str, Any]],
) -> list[str]:
    trusted = {
        _UNRESOLVED_TEST_CONTRACT_LIMIT, _UNPROVEN_BUG_LIMIT,
        _UNPROVEN_NONBUG_LIMIT,
    }
    limits = [
        str(x) for x in (validated.get("audit_limits") or [])
        if str(x) in trusted
    ][:8]
    if omitted:
        ids = ", ".join(row["finding_id"] for row in omitted)
        note = (
            f"Audit display cap: {len(omitted)} omitted validated finding IDs: {ids}"
        )[:420]
        limits = [note] + [x for x in limits if x != note]
    provenance_note = (
        "Final findings are restricted to EvidenceBroker-backed specialist claims; "
        "synthesis cannot create new findings, locations, evidence IDs, reasons, "
        "or recommendations."
    )
    if provenance_note not in limits:
        limits.append(provenance_note)
    source_mode = str(project_facts.get("source_mode", "")).strip()
    if source_mode:
        mode_note = f"Repository source mode during audit: {source_mode}."[:420]
        if mode_note not in limits:
            limits.append(mode_note)
    completion, pending = _completion_metadata(validated)
    if completion == "INCOMPLETE":
        limits.insert(0, f"EVIDENCE_INCOMPLETE: {len(pending)} unresolved evidence/status "
                      "records remain after the bounded evidence pass. Accepted "
                      "findings remain valid, but the requested review is incomplete.")
    return limits[:8]


def build_final_report(
    *,
    synthesis: dict[str, Any],
    validated: dict[str, Any],
    project_facts: dict[str, Any],
) -> dict[str, Any]:
    completion, pending = _completion_metadata(validated)
    findings = list(validated.get("findings") or [])
    strengths = list(validated.get("strengths") or [])
    rejected = list(validated.get("rejected") or [])
    # Perform deterministic priority selection BEFORE consulting synthesis.
    # Otherwise ten optional suggestions can consume the report's ten slots
    # and erase a medium-priority proven defect.
    ordered = sorted(findings, key=_finding_rank)
    selected = ordered[:10]
    omitted = ordered[10:]
    finding_registry = {str(r["finding_id"]): r for r in selected}
    strength_registry = {str(r["strength_id"]): r for r in strengths}

    # Synthesis may suggest compatible groups but cannot choose which proved
    # issues survive the display cap or override the deterministic priority.
    used: set[str] = set()
    groups: list[list[str]] = []
    for raw_group in synthesis.get("finding_groups") or []:
        if not isinstance(raw_group, dict):
            continue
        ids = [x for x in _clean_id_group(raw_group.get("source_finding_ids") or [], finding_registry) if x not in used]
        if not ids:
            continue
        candidate_groups = [ids] if _group_is_related(ids, finding_registry) else [[x] for x in ids]
        for candidate in candidate_groups:
            if len(groups) >= 10:
                break
            groups.append(candidate)
            used.update(candidate)
        if len(groups) >= 10:
            break

    # A synthesizer omission must not erase a validated specialist finding.
    remaining = [r for r in selected if r["finding_id"] not in used]
    remaining.sort(key=_finding_rank)
    for row in remaining:
        if len(groups) >= 10:
            break
        groups.append([row["finding_id"]])

    # Neither synthesis group order nor its action ranking is semantic
    # authority. Always display certified defects before optional ideas.
    groups.sort(key=lambda ids: min(_finding_rank(finding_registry[x]) for x in ids))
    final_findings = [_combine_findings(ids, finding_registry, idx)
                      for idx, ids in enumerate(groups, 1)]

    final_strengths: list[dict[str, Any]] = []
    selected_strengths = [str(x).strip() for x in (synthesis.get("strength_ids") or []) if str(x).strip() in strength_registry]
    for ident in strength_registry:
        if ident not in selected_strengths:
            selected_strengths.append(ident)
    for idx, ident in enumerate(selected_strengths[:8], 1):
        row = strength_registry[ident]
        final_strengths.append({
            "strength_id": f"K-{idx:03d}",
            "area": row["area"],
            "location": row["location"],
            "evidence_ids": list(row["evidence_ids"])[:8],
            "source_strength_ids": [ident],
            "reason": f"[{ident} / {row['specialist']}] {row['reason']}"[:900],
            "confidence": row["confidence"],
        })

    disagreements: list[dict[str, Any]] = []
    seen_disagreement_keys: set[tuple[str, ...]] = set()
    for raw_group in synthesis.get("disagreement_groups") or []:
        if not isinstance(raw_group, dict):
            continue
        ids = _clean_id_group(raw_group.get("source_finding_ids") or [], finding_registry)
        if len(ids) < 2:
            continue
        roles = {finding_registry[x]["specialist"] for x in ids}
        if len(roles) < 2 or not _group_is_related(ids, finding_registry):
            continue
        key = tuple(sorted(ids))
        if key in seen_disagreement_keys:
            continue
        seen_disagreement_keys.add(key)
        parts = [f"{x} ({finding_registry[x]['specialist']}): {finding_registry[x]['reason']}" for x in ids]
        disagreements.append({"source_finding_ids": ids, "summary": " | ".join(parts)[:900]})
        if len(disagreements) >= 8:
            break

    # The top five ACTIONS use the same deterministic priority as findings.
    # Never allow model-chosen low-value action order to hide a proven defect.
    action_groups = groups[:5]

    next_actions: list[dict[str, Any]] = []
    for rank, ids in enumerate(action_groups[:5], 1):
        recs = [f"[{x}] {finding_registry[x]['recommendation']}" for x in ids]
        next_actions.append({
            "rank": rank,
            "source_finding_ids": ids,
            "action": " | ".join(recs)[:900],
        })

    counts = {"VERIFIED_BUG": 0, "IMPROVEMENT": 0, "OPTIONAL_IDEA": 0}
    for row in findings:
        counts[row["type"]] += 1
    highest = "NONE"
    if findings:
        highest = sorted((r["priority"] for r in findings), key=lambda x: _PRIORITY_ORDER[x])[0]
    overall = (
        f"Evidence-grounded audit {completion}: {len(findings)} validated specialist finding(s): "
        f"{counts['VERIFIED_BUG']} VERIFIED_BUG, {counts['IMPROVEMENT']} IMPROVEMENT, "
        f"{counts['OPTIONAL_IDEA']} OPTIONAL_IDEA. Highest validated priority: {highest}. "
        f"{len(strengths)} evidence-backed KEEP_AS_IS strength(s). "
        f"{len(rejected)} unverified/contradicted specialist claim(s) were excluded before synthesis. "
        "The synthesis model only grouped/ranked validated IDs; factual report fields were reconstructed deterministically."
    )
    rejected_bug_proof = any(
        row.get("type") == "VERIFIED_BUG"
        and (row.get("kind") == "finding")
        and ("source_bug_lacks_deterministic_proof" in row.get("validation_notes", [])
             or "source_test_mismatch_no_independent_contract" in row.get("validation_notes", []))
        for row in rejected
    )
    rejected_nonbug_proof = any(
        ("nonbug_claim_lacks_deterministic_semantic_proof" in row.get("validation_notes", [])
         or "nonbug_claim_not_semantically_authorized" in row.get("validation_notes", []))
        for row in rejected
    )
    if rejected_bug_proof:
        overall += (
            " INCONCLUSIVE SOURCE/TEST CONTRACT: a model-asserted source defect "
            "was withheld because deterministic semantic proof was unavailable. "
            "This is not evidence that the implementation is correct."
        )
    if rejected_nonbug_proof:
        overall += (
            " INCONCLUSIVE IMPROVEMENT/STRENGTH CLAIMS: some model-authored "
            "nonbug descriptions were withheld because their factual meaning "
            "was not independently established by the cited source."
        )

    limits = _canonical_audit_limits(validated, project_facts, omitted)

    report = {
        "overall_assessment": overall[:1600],
        "completion_status": completion,
        "pending_evidence_requests": pending,
        "findings": final_findings[:10],
        "keep_as_is": final_strengths[:8],
        "disagreements": disagreements[:8],
        "audit_limits": limits[:8],
        "recommended_next_actions": next_actions[:5],
        "rejected_unverified_count": len(rejected),
    }
    assert_final_report_provenance(report, validated, project_facts=project_facts)
    return report


def assert_final_report_provenance(
    report: dict[str, Any],
    validated: dict[str, Any],
    *,
    project_facts: dict[str, Any] | None = None,
) -> None:
    """Second deterministic gate: reject any final object that escapes source provenance."""
    completion, pending = _completion_metadata(validated)
    if (report.get("completion_status") != completion
            or report.get("pending_evidence_requests") != pending):
        raise ValueError("final audit completion metadata changed")
    ordered = sorted(validated.get("findings") or [], key=_finding_rank)
    expected = ordered[:10]
    eligible = {str(r["finding_id"]): r for r in expected}
    finding_registry = {str(r["finding_id"]): r for r in (validated.get("findings") or [])}
    strength_registry = {str(r["strength_id"]): r for r in (validated.get("strengths") or [])}
    observed = [
        str(source_id) for row in (report.get("findings") or [])
        for source_id in (row.get("source_finding_ids") or [])
    ]
    expected_ids = [str(row["finding_id"]) for row in expected]
    if (len(observed) != len(set(observed))
            or len(observed) != len(expected_ids)
            or set(observed) != set(expected_ids)):
        raise ValueError("final audit findings omit or repeat priority-selected IDs")
    for row in report.get("findings") or []:
        ids = [str(x) for x in (row.get("source_finding_ids") or [])]
        if any(x not in eligible for x in ids) or not _group_is_related(ids, eligible):
            raise ValueError("final audit group lacks one certified issue identity")
    group_order = list(report.get("findings") or [])
    if group_order != sorted(
        group_order,
        key=lambda group: min(_finding_rank(eligible[x])
                              for x in group["source_finding_ids"])
    ):
        raise ValueError("final finding order is not priority stable")
    expected_action_ids = [
        list(group["source_finding_ids"]) for group in group_order[:5]
    ]
    actual_action_ids = [
        list(group.get("source_finding_ids") or [])
        for group in (report.get("recommended_next_actions") or [])
    ]
    if actual_action_ids != expected_action_ids:
        raise ValueError("final actions do not preserve priority-selected findings")
    if project_facts is not None:
        expected_limits = _canonical_audit_limits(
            validated, project_facts, ordered[10:]
        )
        if report.get("audit_limits") != expected_limits:
            raise ValueError("final audit limits are not deterministically warranted")

    for row in report.get("findings") or []:
        source_ids = [str(x) for x in (row.get("source_finding_ids") or [])]
        if not source_ids or any(x not in finding_registry for x in source_ids):
            raise ValueError("final audit finding references unknown source_finding_id")
        expected = _combine_findings(source_ids, finding_registry, 1)
        for key in ("type", "priority", "area", "location", "evidence_ids", "source_finding_ids", "reason", "recommendation", "confidence"):
            if row.get(key) != expected.get(key):
                raise ValueError(f"final audit finding changed provenance field: {key}")

    for row in report.get("keep_as_is") or []:
        ids = [str(x) for x in (row.get("source_strength_ids") or [])]
        if len(ids) != 1 or ids[0] not in strength_registry:
            raise ValueError("final KEEP_AS_IS references unknown strength source")
        src = strength_registry[ids[0]]
        expected = {
            "area": src["area"],
            "location": src["location"],
            "evidence_ids": list(src["evidence_ids"])[:8],
            "source_strength_ids": ids,
            "reason": f"[{ids[0]} / {src['specialist']}] {src['reason']}"[:900],
            "confidence": src["confidence"],
        }
        for key, value in expected.items():
            if row.get(key) != value:
                raise ValueError(f"final KEEP_AS_IS changed provenance field: {key}")

    for row in report.get("disagreements") or []:
        ids = [str(x) for x in (row.get("source_finding_ids") or [])]
        if len(ids) < 2 or any(x not in finding_registry for x in ids):
            raise ValueError("final disagreement references invalid source findings")
        roles = {finding_registry[x]["specialist"] for x in ids}
        if len(roles) < 2:
            raise ValueError("final disagreement does not span independent specialists")
        expected_summary = " | ".join(
            f"{x} ({finding_registry[x]['specialist']}): {finding_registry[x]['reason']}" for x in ids
        )[:900]
        if row.get("summary") != expected_summary:
            raise ValueError("final disagreement changed source rationale")

    expected_rank = 1
    for row in report.get("recommended_next_actions") or []:
        ids = [str(x) for x in (row.get("source_finding_ids") or [])]
        if not ids or any(x not in finding_registry for x in ids):
            raise ValueError("final next action references invalid source findings")
        expected_action = " | ".join(f"[{x}] {finding_registry[x]['recommendation']}" for x in ids)[:900]
        if row.get("action") != expected_action:
            raise ValueError("final next action changed source recommendation")
        if row.get("rank") != expected_rank:
            raise ValueError("final next action rank is not sequential")
        expected_rank += 1
