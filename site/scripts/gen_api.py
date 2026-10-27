#!/usr/bin/env python3
"""
gen_api.py - Generate per-source-file / per-module Starlight documentation
from Doxygen XML (C++) and Griffe (Python). Part of ATLAS DiHiggs.
"""

import os
import sys
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SITE_DIR = ROOT_DIR / "site"
API_DOCS_DIR = SITE_DIR / "src" / "content" / "docs" / "api"
TEMP_DIR = SITE_DIR / ".cache"

# Add venv to sys.path for Griffe
for p in (SITE_DIR / ".venv-docs" / "lib").glob("python3.*/site-packages"):
    sys.path.insert(0, str(p))
import griffe

def load_submodule_info() -> dict:
    """Read repo URLs from .gitmodules and pinned SHAs from git ls-tree HEAD."""
    urls = {}
    gitmodules = ROOT_DIR / ".gitmodules"
    if gitmodules.exists():
        curr = None
        for line in gitmodules.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith('[submodule "') and line.endswith('"]'):
                curr = line[12:-2]
            elif line.startswith("url =") and curr:
                u = line.split("=", 1)[1].strip()
                urls[curr] = u[:-4] if u.endswith(".git") else u

    commits = {}
    try:
        res = subprocess.run(
            ["git", "-C", str(ROOT_DIR), "ls-tree", "HEAD"],
            capture_output=True, text=True, check=True
        )
        for line in res.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[1] == "commit":
                commits[parts[3]] = parts[2]
    except Exception as e:
        print(f"[!] Warning reading git ls-tree: {e}", file=sys.stderr)

    return {name: {"url": url, "commit": commits.get(name, "main")} for name, url in urls.items()}

SUBMODULE_INFO = load_submodule_info()

def get_file_info(filepath: str, lineno: int | str = ""):
    """Return (repo_rel_path, github_link) with no local absolute paths."""
    norm = Path(filepath).as_posix()
    root_str = ROOT_DIR.as_posix()
    ws_rel = norm[len(root_str):].lstrip("/") if norm.startswith(root_str) else norm.lstrip("/")

    for mod_name, info in SUBMODULE_INFO.items():
        if ws_rel == mod_name or ws_rel.startswith(mod_name + "/"):
            repo_rel = ws_rel[len(mod_name):].lstrip("/")
            link = f"{info['url']}/blob/{info['commit']}/{repo_rel}"
            if lineno:
                link += f"#L{lineno}"
            return repo_rel, link

    link = f"https://github.com/fbientrigo/atlas_dihiggs/blob/main/{ws_rel}"
    if lineno:
        link += f"#L{lineno}"
    return ws_rel, link

def find_doxygen() -> str:
    local_opt = Path.home() / ".local" / "opt" / "doxygen" / "bin" / "doxygen"
    if local_opt.is_file() and os.access(local_opt, os.X_OK):
        return str(local_opt)
    dox = shutil.which("doxygen")
    if dox:
        return dox
    raise RuntimeError("doxygen binary not found!")

def run_doxygen(xml_out_dir: Path):
    dox_bin = find_doxygen()
    doxyfile_content = f"""
PROJECT_NAME           = "ATLAS DiHiggs C++ API"
OUTPUT_DIRECTORY       = "{xml_out_dir}"
GENERATE_LATEX         = NO
GENERATE_HTML          = NO
GENERATE_XML           = YES
XML_OUTPUT             = xml
INPUT                  = {ROOT_DIR}/dihiggs/dihiggs/src \\
                         {ROOT_DIR}/dihiggs/2hdmc/src \\
                         {ROOT_DIR}/dihiggs/higgstools/src \\
                         {ROOT_DIR}/dihiggs/higgstools/include \\
                         {ROOT_DIR}/dihiggs_boundary/src \\
                         {ROOT_DIR}/dihiggs_hep_cross/campaigns/20261007_positive_g_envelope/final_review_snapshot \\
                         {ROOT_DIR}/dihiggs_llp_recast/src \\
                         {ROOT_DIR}/recast_viewer/preprocess/instrumentation
RECURSIVE              = YES
FILE_PATTERNS          = *.h *.hpp *.hh *.cpp *.cc *.cxx
EXTRACT_ALL            = YES
EXTRACT_PRIVATE        = NO
EXTRACT_STATIC         = YES
QUIET                  = YES
WARNINGS               = NO
XML_PROGRAMLISTING     = NO
"""
    xml_out_dir.mkdir(parents=True, exist_ok=True)
    (xml_out_dir / "Doxyfile").write_text(doxyfile_content, encoding="utf-8")
    subprocess.run([dox_bin, str(xml_out_dir / "Doxyfile")], check=True, capture_output=True)

def clean_xml_text(elem) -> str:
    if elem is None:
        return ""
    text = "".join(elem.itertext()).strip()
    return " ".join(line.strip() for line in text.splitlines() if line.strip())

# Module definitions
CPP_MODULES = [
    {
        "id": "2hdmc", "name": "2HDMC", "group": "Base", "lang": "C++", "module": "dihiggs",
        "dir": API_DOCS_DIR / "cpp" / "base" / "2hdmc", "patterns": ["dihiggs/2hdmc/src"],
        "url_prefix": "/api/cpp/base/2hdmc",
    },
    {
        "id": "higgstools", "name": "HiggsTools", "group": "Base", "lang": "C++", "module": "dihiggs",
        "dir": API_DOCS_DIR / "cpp" / "base" / "higgstools", "patterns": ["dihiggs/higgstools/src", "dihiggs/higgstools/include"],
        "url_prefix": "/api/cpp/base/higgstools",
    },
    {
        "id": "dihiggs", "name": "dihiggs (C++)", "group": "Project", "lang": "C++", "module": "dihiggs",
        "dir": API_DOCS_DIR / "cpp" / "project" / "dihiggs", "patterns": ["dihiggs/dihiggs/src"],
        "url_prefix": "/api/cpp/project/dihiggs",
    },
    {
        "id": "boundary", "name": "dihiggs_boundary (C++)", "group": "Project", "lang": "C++", "module": "dihiggs_boundary",
        "dir": API_DOCS_DIR / "cpp" / "project" / "boundary", "patterns": ["dihiggs_boundary/src"],
        "url_prefix": "/api/cpp/project/boundary",
    },
    {
        "id": "hep_cross", "name": "dihiggs_hep_cross (C++)", "group": "Project", "lang": "C++", "module": "dihiggs_hep_cross",
        "dir": API_DOCS_DIR / "cpp" / "project" / "hep_cross", "patterns": ["dihiggs_hep_cross"],
        "url_prefix": "/api/cpp/project/hep_cross",
    },
    {
        "id": "llp_recast", "name": "dihiggs_llp_recast (C++)", "group": "Project", "lang": "C++", "module": "dihiggs_llp_recast",
        "dir": API_DOCS_DIR / "cpp" / "project" / "llp_recast", "patterns": ["dihiggs_llp_recast/src", "recast_viewer/preprocess/instrumentation"],
        "url_prefix": "/api/cpp/project/llp_recast",
    },
]

PYTHON_MODULES = [
    {
        "id": "dihiggs", "name": "dihiggs (Python)", "group": "Project", "lang": "Python", "module": "dihiggs",
        "dir": API_DOCS_DIR / "python" / "dihiggs", "url_prefix": "/api/python/dihiggs",
        "targets": [
            {"type": "pkg", "name": "orchestrator", "search": str(ROOT_DIR / "dihiggs" / "dihiggs" / "app")},
            {"type": "pkg", "name": "lib", "search": str(ROOT_DIR / "dihiggs" / "mlpython")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs" / "scripts"},
        ],
    },
    {
        "id": "dihiggs-boundary", "name": "dihiggs_boundary (Python)", "group": "Project", "lang": "Python", "module": "dihiggs_boundary",
        "dir": API_DOCS_DIR / "python" / "dihiggs-boundary", "url_prefix": "/api/python/dihiggs-boundary",
        "targets": [
            {"type": "pkg", "name": "dhb", "search": str(ROOT_DIR / "dihiggs_boundary" / "python")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs_boundary" / "scripts"},
        ],
    },
    {
        "id": "dihiggs-hep-cross", "name": "dihiggs_hep_cross (Python)", "group": "Project", "lang": "Python", "module": "dihiggs_hep_cross",
        "dir": API_DOCS_DIR / "python" / "dihiggs-hep-cross", "url_prefix": "/api/python/dihiggs-hep-cross",
        "targets": [
            {"type": "pkg", "name": "llp_recast", "search": str(ROOT_DIR / "dihiggs_hep_cross" / "src")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs_hep_cross" / "scripts"},
        ],
    },
    {
        "id": "dihiggs-llp-recast", "name": "dihiggs_llp_recast (Python)", "group": "Project", "lang": "Python", "module": "dihiggs_llp_recast",
        "dir": API_DOCS_DIR / "python" / "dihiggs-llp-recast", "url_prefix": "/api/python/dihiggs-llp-recast",
        "targets": [
            {"type": "pkg", "name": "dvrecast", "search": str(ROOT_DIR / "dihiggs_llp_recast" / "src")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs_llp_recast" / "scripts"},
        ],
    },
    {
        "id": "dihiggs-ufo", "name": "dihiggs_ufo (Python)", "group": "Project", "lang": "Python", "module": "dihiggs_ufo",
        "dir": API_DOCS_DIR / "python" / "dihiggs-ufo", "url_prefix": "/api/python/dihiggs-ufo",
        "targets": [
            {"type": "pkg", "name": "pack_aa_kinematic_validation", "search": str(ROOT_DIR / "dihiggs_ufo" / "studies" / "pack_aa_kinematic_validation" / "src")},
            {"type": "pkg", "name": "pack_a_seed_mc", "search": str(ROOT_DIR / "dihiggs_ufo" / "studies" / "pack_a_seed_mc" / "src")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs_ufo" / "scripts"},
        ],
    },
    {
        "id": "recast-viewer", "name": "recast_viewer (Python)", "group": "Project", "lang": "Python", "module": "recast_viewer",
        "dir": API_DOCS_DIR / "python" / "recast-viewer", "url_prefix": "/api/python/recast-viewer",
        "targets": [
            {"type": "pkg", "name": "preprocess", "search": str(ROOT_DIR / "recast_viewer")},
        ],
    },
]

def parse_cpp_doxygen(xml_dir: Path):
    """Parse Doxygen XML and organize symbols strictly per source file."""
    index_path = xml_dir / "index.xml"
    if not index_path.exists():
        return {}

    root = ET.parse(index_path).getroot()
    files = {}

    def get_or_create_file(fpath: str):
        if fpath not in files:
            repo_rel, link = get_file_info(fpath)
            mod_cfg = None
            norm = fpath.replace("\\", "/")
            for m in CPP_MODULES:
                for pat in m["patterns"]:
                    if pat in norm:
                        mod_cfg = m
                        break
                if mod_cfg:
                    break
            files[fpath] = {
                "file_path": fpath, "repo_rel": repo_rel, "github_link": link,
                "module": mod_cfg, "classes": [], "free_symbols": [],
            }
        return files[fpath]

    for comp in root.findall("compound"):
        kind = comp.attrib.get("kind")
        refid = comp.attrib.get("refid")
        comp_file = xml_dir / f"{refid}.xml"
        if not comp_file.exists():
            continue

        if kind == "file":
            c_def = ET.parse(comp_file).getroot().find("compounddef")
            if c_def is None:
                continue
            loc = c_def.find("location")
            fpath = loc.attrib.get("file", "") if loc is not None else ""
            if not fpath:
                continue
            fdata = get_or_create_file(fpath)
            if not fdata["module"]:
                continue

            is_cpp = fpath.endswith((".cpp", ".cc", ".cxx"))
            for sec in c_def.findall("sectiondef"):
                for mem in sec.findall("memberdef"):
                    m_kind = mem.attrib.get("kind")
                    m_name = mem.findtext("name", "")
                    if m_name == "main" or m_name.startswith(("_", "@")) or "anon" in m_name:
                        continue
                    if m_kind == "define":
                        continue
                    if is_cpp and mem.attrib.get("static") == "yes":
                        continue
                    if m_kind == "variable":
                        v_type = clean_xml_text(mem.find("type"))
                        if "const" not in v_type:
                            continue

                    m_loc = mem.find("location")
                    line = m_loc.attrib.get("line", "") if m_loc is not None else ""
                    m_type = clean_xml_text(mem.find("type"))
                    m_args = mem.findtext("argsstring", "")
                    doc = clean_xml_text(mem.find("briefdescription")) or clean_xml_text(mem.find("detaileddescription"))
                    _, m_link = get_file_info(fpath, line)

                    fdata["free_symbols"].append({
                        "kind": m_kind, "name": m_name, "sig": f"{m_type} {m_name}{m_args}".strip(),
                        "doc": doc, "line": line, "link": m_link, "documented": bool(doc),
                    })

        elif kind in ("class", "struct"):
            c_def = ET.parse(comp_file).getroot().find("compounddef")
            if c_def is None or c_def.attrib.get("prot") == "private":
                continue
            c_name = c_def.findtext("compoundname", "").strip()
            if c_name.startswith(("@", "__")) or "anon" in c_name:
                continue

            loc = c_def.find("location")
            fpath = loc.attrib.get("file", "") if loc is not None else ""
            c_line = loc.attrib.get("line", "") if loc is not None else ""
            if not fpath:
                continue
            fdata = get_or_create_file(fpath)
            if not fdata["module"]:
                continue

            c_doc = clean_xml_text(c_def.find("briefdescription")) or clean_xml_text(c_def.find("detaileddescription"))
            _, c_link = get_file_info(fpath, c_line)

            methods = []
            for sec in c_def.findall("sectiondef"):
                for mem in sec.findall("memberdef"):
                    if mem.attrib.get("prot") == "private":
                        continue
                    m_kind = mem.attrib.get("kind")
                    m_name = mem.findtext("name", "")
                    if m_name.startswith(("@", "__")):
                        continue
                    if m_kind == "variable":
                        v_type = clean_xml_text(mem.find("type"))
                        if mem.attrib.get("static") != "yes" or "const" not in v_type:
                            continue
                    elif m_kind not in ("function", "typedef", "enum"):
                        continue

                    m_loc = mem.find("location")
                    line = m_loc.attrib.get("line", "") if m_loc is not None else ""
                    m_type = clean_xml_text(mem.find("type"))
                    m_args = mem.findtext("argsstring", "")
                    doc = clean_xml_text(mem.find("briefdescription")) or clean_xml_text(mem.find("detaileddescription"))
                    _, m_link = get_file_info(fpath, line)

                    methods.append({
                        "kind": m_kind, "name": m_name, "sig": f"{m_type} {m_name}{m_args}".strip(),
                        "doc": doc, "line": line, "link": m_link, "documented": bool(doc),
                    })

            fdata["classes"].append({
                "kind": kind, "name": c_name, "doc": c_doc, "line": c_line,
                "link": c_link, "documented": bool(c_doc), "methods": methods,
            })

    return files

def extract_python_modules():
    """Extract Python symbols per module via Griffe static AST inspection."""
    results = defaultdict(list)

    for mod_cfg in PYTHON_MODULES:
        mod_id = mod_cfg["id"]

        for item in mod_cfg["targets"]:
            if item["type"] == "pkg":
                pkg_name = item["name"]
                search = item["search"]
                try:
                    loader = griffe.GriffeLoader(search_paths=[search])
                    pkg = loader.load(pkg_name, try_relative_path=False)
                    all_mods = [pkg] + list(pkg.modules.values())
                    for m in all_mods:
                        m_file = str(m.filepath) if m.filepath else ""
                        if not m_file:
                            continue
                        repo_rel, link = get_file_info(m_file)
                        mod_data = parse_griffe_module(m, repo_rel, link, mod_cfg)
                        if mod_data:
                            results[mod_id].append(mod_data)
                except Exception as e:
                    print(f"[!] Warning loading Python package {pkg_name}: {e}", file=sys.stderr)

            elif item["type"] == "scripts":
                sdir = item["dir"]
                if not sdir.exists():
                    continue
                loader = griffe.GriffeLoader(search_paths=[str(sdir)])
                for pyfile in sorted(sdir.glob("*.py")):
                    if pyfile.name.startswith("__"):
                        continue
                    try:
                        sm = loader.load(pyfile.stem, try_relative_path=False)
                        repo_rel, link = get_file_info(str(pyfile))
                        mod_data = parse_griffe_module(sm, repo_rel, link, mod_cfg, is_script=True)
                        if mod_data:
                            results[mod_id].append(mod_data)
                    except Exception:
                        continue

    return results

def parse_griffe_module(module, repo_rel: str, link: str, mod_cfg: dict, is_script: bool = False):
    """Parse a single Griffe module into classes and functions with junk filtered."""
    classes = []
    functions = []
    has_public = any(not name.startswith("_") for name, mem in module.members.items() if not mem.is_alias)

    for name, mem in module.members.items():
        if mem.is_alias:
            continue
        if has_public and name.startswith("_") and name != "__init__":
            continue
        if name.startswith("__") and name != "__init__":
            continue

        doc = mem.docstring.value.strip() if mem.docstring else ""
        lineno = mem.lineno or 1
        _, m_link = get_file_info(str(mem.filepath or repo_rel), lineno)

        if mem.is_function:
            params = [f"{p.name}{f': {p.annotation}' if p.annotation else ''}{f' = {p.default}' if p.default else ''}" for p in mem.parameters]
            sig = f"def {name}({', '.join(params)})"
            if mem.returns:
                sig += f" -> {mem.returns}"
            functions.append({
                "name": name, "sig": sig, "doc": doc, "line": lineno, "link": m_link, "documented": bool(doc),
            })

        elif mem.is_class:
            methods = []
            for m_name, m_mem in mem.members.items():
                if m_mem.is_alias or (m_name.startswith("_") and m_name != "__init__"):
                    continue
                if m_mem.is_function:
                    m_doc = m_mem.docstring.value.strip() if m_mem.docstring else ""
                    m_params = [f"{p.name}{f': {p.annotation}' if p.annotation else ''}" for p in m_mem.parameters]
                    m_sig = f"def {m_name}({', '.join(m_params)})"
                    if m_mem.returns:
                        m_sig += f" -> {m_mem.returns}"
                    _, sub_link = get_file_info(str(m_mem.filepath or repo_rel), m_mem.lineno or lineno)
                    methods.append({
                        "name": m_name, "sig": m_sig, "doc": m_doc, "line": m_mem.lineno or lineno, "link": sub_link, "documented": bool(m_doc),
                    })
            classes.append({
                "name": name, "sig": f"class {name}", "doc": doc, "line": lineno, "link": m_link, "documented": bool(doc), "methods": methods,
            })

    title = f"{module.canonical_path}" if not is_script else f"{Path(repo_rel).name}"
    return {
        "title": title, "repo_rel": repo_rel, "github_link": link,
        "module": mod_cfg, "classes": classes, "functions": functions, "is_script": is_script,
    }

def render_file_markdown(title: str, repo_rel: str, github_link: str, classes: list, free_symbols: list, lang: str) -> str:
    """Render a single source file page without coverage clutter, grouping overloads."""
    total_classes = len(classes)
    total_funcs = sum(len(c["methods"]) for c in classes) + len(free_symbols)
    doc_count = sum(1 for c in classes if c["documented"]) + \
                sum(1 for c in classes for m in c["methods"] if m["documented"]) + \
                sum(1 for s in free_symbols if s["documented"])
    total_syms = total_classes + total_funcs
    pct = (doc_count / total_syms * 100) if total_syms > 0 else 100.0

    lines = [
        "---",
        f"title: \"{title}\"",
        f"description: \"API documentation for {repo_rel}\"",
        "---",
        "",
        '<div class="file-header">',
        f'  <div><strong>Path:</strong> <code>{repo_rel}</code></div>',
        f'  <div><strong>Source:</strong> <a href="{github_link}" target="_blank" rel="noopener">GitHub</a></div>',
        f'  <div><strong>Symbols:</strong> {total_classes} classes, {total_funcs} functions ({pct:.1f}% documented)</div>',
        '</div>',
        "",
    ]

    if not classes and not free_symbols:
        lines.append("*No public API symbols defined in this source file.*")
        lines.append("")
        return "\n".join(lines)

    if classes:
        lines.append("## Classes & Structs\n")
        for c in classes:
            c_doc_badge = "" if c["documented"] else ' <span class="wired-pill red">UNDOCUMENTED</span>'
            lines.append(f"### `{c['name']}`{c_doc_badge}\n*Source: [{repo_rel}:{c['line']}]({c['link']})*\n")
            if c.get("doc"):
                lines.append(f"> {c['doc']}\n")

            methods_by_name = defaultdict(list)
            for m in c.get("methods", []):
                methods_by_name[m["name"]].append(m)

            if methods_by_name:
                lines.append("#### Methods\n")
                for m_name, m_list in sorted(methods_by_name.items()):
                    if len(m_list) == 1:
                        m = m_list[0]
                        m_badge = "" if m["documented"] else ' <span class="wired-pill red">UNDOCUMENTED</span>'
                        lines.append(f"- **`{m_name}`**{m_badge} &mdash; [`L{m['line']}`]({m['link']})\n```{lang.lower()}\n{m['sig']}\n```")
                        if m.get("doc"):
                            lines.append(f"  > {m['doc']}")
                    else:
                        lines.append(f"- **`{m_name}`** *(overloads: {len(m_list)})*")
                        for idx, m in enumerate(m_list, 1):
                            m_badge = "" if m["documented"] else ' <span class="wired-pill red">UNDOCUMENTED</span>'
                            lines.append(f"  - Overload {idx}{m_badge} &mdash; [`L{m['line']}`]({m['link']})\n    ```{lang.lower()}\n    {m['sig']}\n    ```")
                            if m.get("doc"):
                                lines.append(f"    > {m['doc']}")
                lines.append("")

    if free_symbols:
        lines.append("## Free Functions & Constants\n")
        funcs_by_name = defaultdict(list)
        for s in free_symbols:
            funcs_by_name[s["name"]].append(s)

        for s_name, s_list in sorted(funcs_by_name.items()):
            if len(s_list) == 1:
                s = s_list[0]
                s_badge = "" if s["documented"] else ' <span class="wired-pill red">UNDOCUMENTED</span>'
                lines.append(f"### `{s_name}`{s_badge}\n*Source: [{repo_rel}:{s['line']}]({s['link']})*\n\n```{lang.lower()}\n{s['sig']}\n```\n")
                if s.get("doc"):
                    lines.append(f"> {s['doc']}\n")
            else:
                lines.append(f"### `{s_name}` *(overloads: {len(s_list)})*\n")
                for idx, s in enumerate(s_list, 1):
                    s_badge = "" if s["documented"] else ' <span class="wired-pill red">UNDOCUMENTED</span>'
                    lines.append(f"#### Overload {idx}{s_badge}\n*Source: [{repo_rel}:{s['line']}]({s['link']})*\n\n```{lang.lower()}\n{s['sig']}\n```\n")
                    if s.get("doc"):
                        lines.append(f"> {s['doc']}\n")

    return "\n".join(lines)

def clean_api_dirs():
    for base_subdir in ["cpp", "python"]:
        target = API_DOCS_DIR / base_subdir
        if target.exists():
            shutil.rmtree(target)

def main():
    print("[*] WIRED // API Generator (AST Per-File)")
    clean_api_dirs()

    xml_cache = TEMP_DIR / "doxygen"
    run_doxygen(xml_cache)

    print("[*] Parsing C++ Doxygen AST...")
    cpp_files = parse_cpp_doxygen(xml_cache / "xml")

    print("[*] Parsing Python Griffe AST...")
    python_by_mod = extract_python_modules()

    module_stats = []
    cpp_by_mod = defaultdict(list)
    for fdata in cpp_files.values():
        if fdata["module"]:
            cpp_by_mod[fdata["module"]["id"]].append(fdata)

    for m in CPP_MODULES:
        m_id = m["id"]
        out_dir = m["dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        flist = sorted(cpp_by_mod.get(m_id, []), key=lambda x: x["repo_rel"])

        m_total, m_doc = 0, 0
        first_url = None

        for fdata in flist:
            fname = Path(fdata["repo_rel"]).name
            md_name = f"{fname}.md"
            out_file = out_dir / md_name

            c_cnt = len(fdata["classes"])
            f_cnt = sum(len(c["methods"]) for c in fdata["classes"]) + len(fdata["free_symbols"])
            d_cnt = sum(1 for c in fdata["classes"] if c["documented"]) + \
                    sum(1 for c in fdata["classes"] for method in c["methods"] if method["documented"]) + \
                    sum(1 for s in fdata["free_symbols"] if s["documented"])

            m_total += (c_cnt + f_cnt)
            m_doc += d_cnt

            page_url = f"{m['url_prefix']}/{fname.replace('.', '').lower()}/"
            if not first_url:
                first_url = page_url

            content = render_file_markdown(
                title=fname, repo_rel=fdata["repo_rel"], github_link=fdata["github_link"],
                classes=fdata["classes"], free_symbols=fdata["free_symbols"], lang="cpp"
            )
            out_file.write_text(content, encoding="utf-8")

        pct = (m_doc / m_total * 100) if m_total > 0 else 100.0
        module_stats.append({
            "name": m["name"], "lang": m["lang"], "group": m["group"],
            "commit": SUBMODULE_INFO.get(m["module"], {}).get("commit", "main")[:7],
            "total": m_total, "doc": m_doc, "pct": pct,
            "url": first_url or f"{m['url_prefix']}/", "files": len(flist),
        })

    for m in PYTHON_MODULES:
        m_id = m["id"]
        out_dir = m["dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        mod_list = sorted(python_by_mod.get(m_id, []), key=lambda x: x["title"])

        m_total, m_doc = 0, 0
        first_url = None

        for pdata in mod_list:
            slug = pdata["title"].replace(".", "_").replace("/", "_")
            md_name = f"{slug}.md"
            out_file = out_dir / md_name

            c_cnt = len(pdata["classes"])
            f_cnt = sum(len(c["methods"]) for c in pdata["classes"]) + len(pdata["functions"])
            d_cnt = sum(1 for c in pdata["classes"] if c["documented"]) + \
                    sum(1 for c in pdata["classes"] for method in c["methods"] if method["documented"]) + \
                    sum(1 for s in pdata["functions"] if s["documented"])

            m_total += (c_cnt + f_cnt)
            m_doc += d_cnt

            page_url = f"{m['url_prefix']}/{slug.lower()}/"
            if not first_url:
                first_url = page_url

            content = render_file_markdown(
                title=pdata["title"], repo_rel=pdata["repo_rel"], github_link=pdata["github_link"],
                classes=pdata["classes"], free_symbols=pdata["functions"], lang="python"
            )
            out_file.write_text(content, encoding="utf-8")

        pct = (m_doc / m_total * 100) if m_total > 0 else 100.0
        module_stats.append({
            "name": m["name"], "lang": m["lang"], "group": m["group"],
            "commit": SUBMODULE_INFO.get(m["module"], {}).get("commit", "main")[:7],
            "total": m_total, "doc": m_doc, "pct": pct,
            "url": first_url or f"{m['url_prefix']}/", "files": len(mod_list),
        })

    total_all = sum(s["total"] for s in module_stats)
    doc_all = sum(s["doc"] for s in module_stats)
    overall_pct = (doc_all / total_all * 100) if total_all > 0 else 100.0

    index_lines = [
        "---",
        "title: \"API Reference & Code Coverage\"",
        "description: \"Comprehensive C++ and Python API index across base libraries and workspace modules.\"",
        "---",
        "",
        '<div class="wired-card">',
        '  <div class="wired-card-header">',
        '    <span>// CODEBASE_AUDIT: WORKSPACE SYMBOL COVERAGE</span>',
        f'    <span class="wired-pill">{doc_all}/{total_all} DOCUMENTED ({overall_pct:.1f}%)</span>',
        '  </div>',
        '  <p style="font-size: 0.85rem; margin-bottom: 0; color: var(--sl-color-gray-1);">',
        '    Static code inspection parses Doxygen XML AST for C++ and Griffe AST for Python. Every symbol links directly to its source line on GitHub at the pinned submodule commit.',
        '  </p>',
        '</div>',
        "",
        "## Submodule Coverage Matrix",
        "",
        "| Module | Language | Base / Project | Pinned Commit | Files | Symbols | % Documented |",
        "|---|---|---|---|---|---|---|",
    ]

    for s in module_stats:
        index_lines.append(
            f"| [**{s['name']}**]({s['url']}) | `{s['lang']}` | {s['group']} | `{s['commit']}` | {s['files']} | {s['total']} | {s['pct']:.1f}% |"
        )

    index_lines.extend([
        "",
        "## Navigation Architecture",
        "",
        "- **Per-File Documentation**: Each C++ source file and Python module has its own dedicated documentation page.",
        "- **Clean Symbol Filters**: Only public classes, methods, enums, typedefs, and constants are cataloged; local variables, internal helpers, and CLI entry points are excluded.",
        "- **Direct Pinned Provenance**: All paths are repository-relative and link directly to pinned submodule commits on GitHub.",
    ])

    (API_DOCS_DIR / "index.md").write_text("\n".join(index_lines), encoding="utf-8")

    total_pages = sum(s["files"] for s in module_stats) + 1
    gen_lines = len(Path(__file__).read_text(encoding="utf-8").splitlines())
    print(f"\n[+] Generated {total_pages} API documentation pages across {len(module_stats)} modules.")
    print(f"[+] Total symbols audited: {total_all} ({overall_pct:.1f}% documented).")
    print(f"[+] Generator line count: {gen_lines} lines.\n")

if __name__ == "__main__":
    main()
