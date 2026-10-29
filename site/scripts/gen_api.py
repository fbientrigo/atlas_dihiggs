#!/usr/bin/env python3
"""Generate the API reference (src/content/docs/api/) from Doxygen XML (C++) and griffe (Python).

Every page is one source file / Python module; every source link points at the
commit pinned by the root repo's submodule gitlink. Paths are repo-relative.
"""
import html
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
API = SITE / "src" / "content" / "docs" / "api"
CACHE = SITE / ".cache"

for p in (SITE / ".venv-docs" / "lib").glob("python3.*/site-packages"):
    sys.path.insert(0, str(p))
import griffe  # noqa: E402

# --- source links -----------------------------------------------------------


def submodules() -> dict:
    """{name: {url, commit}} from .gitmodules and `git ls-tree HEAD`."""
    urls, name = {}, None
    for line in (ROOT / ".gitmodules").read_text().splitlines():
        line = line.strip()
        if line.startswith("[submodule"):
            name = line.split('"')[1]
        elif line.startswith("url =") and name:
            urls[name] = line.split("=", 1)[1].strip().removesuffix(".git")
    tree = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "HEAD"], capture_output=True, text=True, check=True).stdout
    commits = {l.split()[3]: l.split()[2] for l in tree.splitlines() if l.split()[1] == "commit"}
    return {n: {"url": u, "commit": commits.get(n, "main")} for n, u in urls.items()}


SUBS = submodules()


def source(path, line="") -> tuple[str, str]:
    """(repo-relative path, GitHub URL at the pinned commit) for an absolute or workspace path."""
    p = Path(path).as_posix()
    ws = p.removeprefix(ROOT.as_posix()).lstrip("/")
    for mod, info in SUBS.items():
        if ws.startswith(mod + "/"):
            rel = ws[len(mod) + 1:]
            return rel, f"{info['url']}/blob/{info['commit']}/{rel}" + (f"#L{line}" if line else "")
    return ws, f"https://github.com/fbientrigo/atlas_dihiggs/blob/main/{ws}" + (f"#L{line}" if line else "")


# --- module table -----------------------------------------------------------
# (id, label, group, submodule owning the commit, source patterns, output dir)
CPP = [
    ("2hdmc", "2HDMC", "Base library", "dihiggs", ["dihiggs/2hdmc/src"], "cpp/base/2hdmc"),
    ("higgstools", "HiggsTools", "Base library", "dihiggs", ["dihiggs/higgstools/src", "dihiggs/higgstools/include"], "cpp/base/higgstools"),
    ("dihiggs", "dihiggs", "Project", "dihiggs", ["dihiggs/dihiggs/src"], "cpp/project/dihiggs"),
    ("boundary", "boundary", "Project", "dihiggs_boundary", ["dihiggs_boundary/src"], "cpp/project/boundary"),
    ("hep_cross", "hep_cross", "Project", "dihiggs_hep_cross", ["dihiggs_hep_cross"], "cpp/project/hep_cross"),
]
CPP_INPUT = [
    "dihiggs/dihiggs/src", "dihiggs/2hdmc/src", "dihiggs/higgstools/src", "dihiggs/higgstools/include",
    "dihiggs_boundary/src", "dihiggs_hep_cross/campaigns/20261007_positive_g_envelope/final_review_snapshot",
]
# (output dir, label, submodule, [("pkg", name, search path) | ("scripts", dir)])
PY = [
    ("dihiggs", "dihiggs", "dihiggs", [("pkg", "orchestrator", "dihiggs/dihiggs/app"), ("pkg", "lib", "dihiggs/mlpython"), ("scripts", "dihiggs/scripts")]),
    ("dihiggs-boundary", "boundary", "dihiggs_boundary", [("pkg", "dhb", "dihiggs_boundary/python"), ("scripts", "dihiggs_boundary/scripts")]),
    ("dihiggs-hep-cross", "hep_cross", "dihiggs_hep_cross", [("pkg", "llp_recast", "dihiggs_hep_cross/src"), ("scripts", "dihiggs_hep_cross/scripts")]),
    ("dihiggs-ufo", "ufo", "dihiggs_ufo", [
        ("pkg", "pack_aa_kinematic_validation", "dihiggs_ufo/studies/pack_aa_kinematic_validation/src"),
        ("pkg", "pack_a_seed_mc", "dihiggs_ufo/studies/pack_a_seed_mc/src"), ("scripts", "dihiggs_ufo/scripts")]),
]

# --- C++ (Doxygen) ----------------------------------------------------------


def run_doxygen(out: Path):
    dox = Path.home() / ".local/opt/doxygen/bin/doxygen"
    exe = str(dox) if dox.is_file() else shutil.which("doxygen")
    if not exe:
        sys.exit("doxygen not found")
    out.mkdir(parents=True, exist_ok=True)
    inputs = " \\\n    ".join(str(ROOT / d) for d in CPP_INPUT)
    (out / "Doxyfile").write_text(f"""OUTPUT_DIRECTORY = "{out}"
GENERATE_LATEX = NO
GENERATE_HTML = NO
GENERATE_XML = YES
INPUT = {inputs}
RECURSIVE = YES
FILE_PATTERNS = *.h *.hpp *.hh *.cpp *.cc *.cxx
EXTRACT_ALL = YES
EXTRACT_STATIC = YES
QUIET = YES
WARNINGS = NO
XML_PROGRAMLISTING = NO
""")
    subprocess.run([exe, str(out / "Doxyfile")], check=True, capture_output=True)


def text(e) -> str:
    return " ".join("".join(e.itertext()).split()) if e is not None else ""


def cpp_symbol(mem, fpath) -> dict:
    loc = mem.find("location")
    line = loc.attrib.get("line", "") if loc is not None else ""
    brief = text(mem.find("briefdescription"))
    detail = mem.find("detaileddescription")
    params = [(text(i.find("parameternamelist")), text(i.find("parameterdescription")))
              for i in mem.iter("parameteritem")]
    ret = next((text(s) for s in mem.iter("simplesect") if s.attrib.get("kind") == "return"), "")
    sig = f"{text(mem.find('type'))} {mem.findtext('name', '')}{mem.findtext('argsstring', '')}".strip()
    return dict(name=mem.findtext("name", ""), sig=sig, doc=brief or text(detail).split(" Parameters ")[0],
                params=params, ret=ret, line=line, link=source(fpath, line)[1])


def parse_cpp(xml: Path) -> dict:
    """{source file: {mod, classes, funcs}} for files belonging to a configured module."""
    files = {}

    def entry(fpath):
        if fpath not in files:
            norm = fpath.replace("\\", "/")
            mod = next((m for m in CPP if any(p in norm for p in m[4])), None)
            files[fpath] = dict(mod=mod, classes=[], funcs=[])
        return files[fpath]

    def keep(mem, in_class):
        name, kind = mem.findtext("name", ""), mem.attrib.get("kind")
        if name == "main" or name.startswith(("_", "@")) or "anon" in name or kind == "define":
            return False
        if mem.attrib.get("prot") == "private":
            return False
        if kind == "variable":
            return "const" in text(mem.find("type")) and (not in_class or mem.attrib.get("static") == "yes")
        return not in_class or kind in ("function", "typedef", "enum")

    for comp in ET.parse(xml / "index.xml").getroot().findall("compound"):
        kind, path = comp.attrib["kind"], xml / f"{comp.attrib['refid']}.xml"
        if kind not in ("file", "class", "struct") or not path.exists():
            continue
        cdef = ET.parse(path).getroot().find("compounddef")
        loc = cdef.find("location") if cdef is not None else None
        fpath = loc.attrib.get("file", "") if loc is not None else ""
        if not fpath or cdef.attrib.get("prot") == "private":
            continue
        f = entry(fpath)
        if not f["mod"]:
            continue
        mems = [m for s in cdef.findall("sectiondef") for m in s.findall("memberdef")]
        if kind == "file":
            is_src = fpath.endswith((".cpp", ".cc", ".cxx"))
            f["funcs"] += [cpp_symbol(m, fpath) for m in mems if keep(m, False) and not (is_src and m.attrib.get("static") == "yes")]
        else:
            name = cdef.findtext("compoundname", "").strip()
            if name.startswith(("@", "__")) or "anon" in name:
                continue
            line = loc.attrib.get("line", "")
            c = dict(name=name, sig=f"{kind} {name}", doc=text(cdef.find("briefdescription")) or text(cdef.find("detaileddescription")),
                     params=[], ret="", line=line, link=source(fpath, line)[1])
            c["methods"] = [cpp_symbol(m, fpath) for m in mems if keep(m, True)]
            f["classes"].append(c)
    return files


# --- Python (griffe) --------------------------------------------------------


def py_symbol(mem, repo_rel, kind="def") -> dict:
    doc = mem.docstring.value.strip() if mem.docstring else ""
    params, ret = [], ""
    if mem.docstring:
        try:
            for sec in mem.docstring.parse("google"):
                if sec.kind.value == "parameters":
                    params = [(p.name, p.description.strip()) for p in sec.value]
                elif sec.kind.value == "returns":
                    ret = " ".join(r.description.strip() for r in sec.value)
        except Exception:
            pass
    line = mem.lineno or 1
    if kind == "def":
        args = ", ".join(f"{p.name}{': ' + str(p.annotation) if p.annotation else ''}{' = ' + str(p.default) if p.default else ''}"
                         for p in mem.parameters)
        sig = f"def {mem.name}({args})" + (f" -> {mem.returns}" if mem.returns else "")
    else:
        sig = f"class {mem.name}"
    return dict(name=mem.name, sig=sig, doc=doc.split("\n\n")[0].replace("\n", " "), params=params, ret=ret,
                line=line, link=source(mem.filepath or repo_rel, line)[1])


def parse_py_module(m, repo_rel, is_script) -> dict:
    members = [x for n, x in m.members.items() if not x.is_alias and not n.startswith("_")]
    classes, funcs = [], []
    for x in members:
        if x.is_function:
            funcs.append(py_symbol(x, repo_rel))
        elif x.is_class:
            c = py_symbol(x, repo_rel, "class")
            c["methods"] = [py_symbol(y, repo_rel) for n, y in x.members.items()
                            if not y.is_alias and y.is_function and (not n.startswith("_") or n == "__init__")]
            classes.append(c)
    title = Path(repo_rel).name if is_script else m.canonical_path
    return dict(title=title, repo_rel=repo_rel, classes=classes, funcs=funcs)


def parse_py(label_id, targets) -> list:
    out = []
    for t in targets:
        try:
            if t[0] == "pkg":
                pkg = griffe.GriffeLoader(search_paths=[str(ROOT / t[2])]).load(t[1], try_relative_path=False)
                mods = [(pkg, False)] + [(x, False) for x in pkg.modules.values()]
            else:
                sdir = ROOT / t[1]
                loader = griffe.GriffeLoader(search_paths=[str(sdir)])
                mods = []
                for f in sorted(sdir.glob("*.py")):
                    if not f.name.startswith("__"):
                        try:
                            mods.append((loader.load(f.stem, try_relative_path=False), True))
                        except Exception:
                            pass
            for m, is_script in mods:
                if m.filepath:
                    out.append(parse_py_module(m, source(str(m.filepath))[0], is_script))
        except Exception as e:
            print(f"[!] {t[1]}: {e}", file=sys.stderr)
    return sorted(out, key=lambda d: d["title"])


# --- rendering --------------------------------------------------------------


def stats(classes, funcs):
    syms = classes + [m for c in classes for m in c["methods"]] + funcs
    return len(syms), sum(1 for s in syms if s["doc"])


def e(s) -> str:
    return html.escape(str(s), quote=False)


def anchor(*parts) -> str:
    return "-".join("".join(ch if ch.isalnum() else "-" for ch in str(p)).strip("-") for p in parts).lower()


def render_symbol(s, lang, level, aid) -> list:
    """Signature block first, then brief, params/returns table, source link."""
    tag = "" if s["doc"] else ' <span class="api-tag">undocumented</span>'
    out = [f'<h{level} id="{aid}" class="api-name"><code>{e(s["name"])}</code>{tag}'
           f'<a class="api-src" href="{s["link"]}" target="_blank" rel="noopener">source ↗ L{s["line"]}</a></h{level}>',
           "", f"```{lang}", s["sig"], "```", ""]
    if s["doc"]:
        out += [e(s["doc"]), ""]
    if s["params"] or s["ret"]:
        out += ['<table class="api-params"><thead><tr><th>Name</th><th>Description</th></tr></thead><tbody>']
        out += [f"<tr><td><code>{e(n)}</code></td><td>{e(d)}</td></tr>" for n, d in s["params"]]
        if s["ret"]:
            out.append(f'<tr><td><em>returns</em></td><td>{e(s["ret"])}</td></tr>')
        out += ["</tbody></table>", ""]
    return out


def render_page(title, repo_rel, link, classes, funcs, lang, group) -> str:
    total, doc = stats(classes, funcs)
    pct = f"{100 * doc / total:.0f}%" if total else "n/a"
    base = ' <span class="api-badge">base library</span>' if group == "Base library" else ""
    out = ["---", f'title: "{title}"', f'description: "API of {repo_rel}"', "---", "",
           f'<div class="api-meta"><code>{e(repo_rel)}</code><a href="{link}" target="_blank" rel="noopener">source ↗</a>'
           f"<span>{total} symbols · {pct} documented</span>{base}</div>", ""]
    if not total:
        return "\n".join(out + ["No public API symbols in this file.", ""])
    if classes:
        out += ["## Classes", ""]
        for c in classes:
            cid = anchor(c["name"])
            out += render_symbol(c, lang, 3, cid)
            if c["methods"]:
                out += ["<table class=\"api-members\"><tbody>"]
                out += [f'<tr><td><a href="#{anchor(c["name"], m["name"], m["line"])}"><code>{e(m["name"])}</code></a></td>'
                        f'<td>{e(m["doc"])}</td></tr>' for m in c["methods"]]
                out += ["</tbody></table>", ""]
                for m in c["methods"]:
                    out += render_symbol(m, lang, 4, anchor(c["name"], m["name"], m["line"]))
    if funcs:
        out += ["## Functions & constants", ""]
        for f in funcs:
            out += render_symbol(f, lang, 3, anchor(f["name"], f["line"]))
    return "\n".join(out)


def main():
    for sub in ("cpp", "python"):
        shutil.rmtree(API / sub, ignore_errors=True)
    run_doxygen(CACHE / "doxygen")
    cpp = parse_cpp(CACHE / "doxygen" / "xml")

    rows = []  # (label, lang, group, commit, url, files, total, doc)

    def emit(dirpath, label, lang, group, sub, pages):
        d = API / dirpath
        d.mkdir(parents=True, exist_ok=True)
        total = doc = 0
        for title, slug, repo_rel, link, classes, funcs in pages:
            (d / f"{slug}.md").write_text(render_page(title, repo_rel, link, classes, funcs, "cpp" if lang == "C++" else "python", group))
            t, k = stats(classes, funcs)
            total, doc = total + t, doc + k
        first = f"/api/{dirpath}/{pages[0][1].replace('.', '').lower()}/" if pages else "/api/"
        rows.append((label, lang, group, SUBS[sub]["commit"][:7], first, len(pages), total, doc))

    for mid, label, group, sub, _, dirpath in CPP:
        pages = []
        for fp, f in sorted(cpp.items(), key=lambda kv: source(kv[0])[0]):
            if f["mod"] and f["mod"][0] == mid:
                rel, link = source(fp)
                pages.append((Path(rel).name, Path(rel).name, rel, link, f["classes"], f["funcs"]))
        emit(dirpath, label, "C++", group, sub, pages)

    for dirpath, label, sub, targets in PY:
        pages = [(d["title"], d["title"].replace(".", "_").replace("/", "_"), d["repo_rel"],
                  SUBS[sub]["url"] + "/blob/" + SUBS[sub]["commit"] + "/" + d["repo_rel"], d["classes"], d["funcs"])
                 for d in parse_py(dirpath, targets)]
        emit(f"python/{dirpath}", label, "Python", "Project", sub, pages)

    total, doc = sum(r[6] for r in rows), sum(r[7] for r in rows)
    out = ["---", 'title: "API reference"', 'description: "C++ and Python symbols per source file, with coverage."', "---", "",
           f'<p class="api-lead">{total} public symbols across {sum(r[5] for r in rows)} source files, '
           f"{100 * doc / total:.0f}% with a docstring. Every entry links to its line on GitHub at the pinned commit. "
           "Search any symbol with <kbd>/</kbd> or <kbd>Ctrl</kbd> <kbd>K</kbd>.</p>", "",
           "## Coverage", "",
           "| Module | Language | Origin | Pinned | Files | Symbols | Documented |", "|---|---|---|---|---|---|---|"]
    for label, lang, group, commit, url, files, t, k in sorted(rows, key=lambda r: r[2] != "Project"):
        pct = 100 * k / t if t else 0
        origin = '<span class="api-badge">base library</span>' if group == "Base library" else "project"
        out.append(f'| [{label}]({url}) | {lang} | {origin} | `{commit}` | {files} | {t} | '
                   f'<span class="cov"><i style="width:{pct:.0f}%"></i></span> {f"{pct:.0f}%" if t else "n/a"} |')
    out += ["", "## Conventions", "",
            "- One page per C++ source file or Python module; classes list their members first, details follow.",
            "- Only public classes, methods, enums, typedefs and constants are listed; private helpers and CLI entry points are not.",
            "- Base libraries (2HDMC, HiggsTools) are vendored inside `dihiggs` and carry their own documentation style."]
    (API / "index.md").write_text("\n".join(out) + "\n")
    print(f"[+] {len(rows)} modules, {total} symbols, {100 * doc / total:.0f}% documented")


if __name__ == "__main__":
    main()
