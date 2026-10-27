#!/usr/bin/env python3
"""
gen_api.py - Generate Starlight documentation pages from Doxygen XML (C++) and Griffe (Python).
Part of ATLAS DiHiggs documentation pipeline.
"""

import os
import sys
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# Workspace Root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SITE_DIR = ROOT_DIR / "site"
API_DOCS_DIR = SITE_DIR / "src" / "content" / "docs" / "api"
TEMP_DIR = SITE_DIR / ".cache"

# Module configurations: repo name, GitHub base, commit hash, git submodule path
SUBMODULE_MAP = {
    "dihiggs": {
        "url": "https://github.com/fbientrigo/dihiggs",
        "commit": "47fcfe8df4858874ca4a7d2ea823dc395f9f3449",
    },
    "dihiggs_boundary": {
        "url": "https://github.com/fbientrigo/dihiggs_boundary",
        "commit": "8f032a7f6c76e7dd5a05d51f93eae8b484ecaa82",
    },
    "dihiggs_hep_cross": {
        "url": "https://github.com/fbientrigo/dihiggs_hep_cross",
        "commit": "df95b4b51f8606085ebff77c3561eb2e7b05f478",
    },
    "dihiggs_llp_recast": {
        "url": "https://github.com/fbientrigo/dihiggs_llp_recast",
        "commit": "4d62c297b17ec7627c0bafea9d7fffd35b98704e",
    },
    "dihiggs_ufo": {
        "url": "https://github.com/fbientrigo/dihiggs_ufo",
        "commit": "9a7ba38deff55360475282edb87e47583efb27a3",
    },
    "recast_viewer": {
        "url": "https://github.com/fbientrigo/atlas_recast_viewer",
        "commit": "b049d37f9f52f97b36d94c283ecbedc119f6c371",
    },
}

def get_git_commit(submodule_name: str) -> str:
    """Read pinned submodule commit from git, fallback to hardcoded."""
    try:
        res = subprocess.run(
            ["git", "submodule", "status", submodule_name],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0 and res.stdout.strip():
            # Format: ' 47fcfe8df4858874ca4a7d2ea823dc395f9f3449 dihiggs (...)'
            parts = res.stdout.strip().split()
            if parts:
                return parts[0].lstrip("+-U")
    except Exception:
        pass
    return SUBMODULE_MAP.get(submodule_name, {}).get("commit", "main")

# Update commits dynamically
for mod in SUBMODULE_MAP:
    SUBMODULE_MAP[mod]["commit"] = get_git_commit(mod)

def get_github_link(filepath: str, lineno: int | str = None) -> str:
    """Build GitHub source link given path relative to ROOT_DIR."""
    norm_path = Path(filepath).as_posix()
    for mod_name, info in SUBMODULE_MAP.items():
        if norm_path == mod_name or norm_path.startswith(mod_name + "/"):
            rel_in_module = norm_path[len(mod_name):].lstrip("/")
            commit = info["commit"]
            url = info["url"]
            link = f"{url}/blob/{commit}/{rel_in_module}"
            if lineno:
                link += f"#L{lineno}"
            return link
    return f"https://github.com/fbientrigo/atlas_dihiggs/blob/main/{norm_path}"

def find_doxygen_binary() -> str:
    """Locate doxygen binary."""
    # Check ~/.local/opt/doxygen/bin/doxygen first
    local_opt = Path.home() / ".local" / "opt" / "doxygen" / "bin" / "doxygen"
    if local_opt.is_file() and os.access(local_opt, os.X_OK):
        return str(local_opt)
    # Check PATH
    which_dox = shutil.which("doxygen")
    if which_dox:
        return which_dox
    raise RuntimeError("doxygen binary not found! Please ensure it is in ~/.local/opt/doxygen or PATH.")

def run_doxygen(xml_out_dir: Path):
    """Execute Doxygen to generate XML."""
    dox_bin = find_doxygen_binary()
    dox_ver = subprocess.run([dox_bin, "-v"], capture_output=True, text=True).stdout.strip()
    print(f"[*] Found Doxygen: {dox_bin} (version {dox_ver})")

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
    doxyfile_path = xml_out_dir / "Doxyfile"
    xml_out_dir.mkdir(parents=True, exist_ok=True)
    doxyfile_path.write_text(doxyfile_content, encoding="utf-8")

    print("[*] Running Doxygen to extract C++ AST XML...")
    res = subprocess.run([dox_bin, str(doxyfile_path)], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] Doxygen error: {res.stderr[:500]}", file=sys.stderr)
    else:
        print("[*] Doxygen XML generation completed.")

def clean_doxygen_text(element: ET.Element | None) -> str:
    """Extract and clean plain text from Doxygen description element."""
    if element is None:
        return ""
    text = "".join(element.itertext()).strip()
    # Replace multiple spaces/newlines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines)

def parse_doxygen_xml(xml_dir: Path):
    """
    Parse Doxygen XML output and group into base vs project groups.
    Returns: dict of groups -> list of files/classes -> symbols
    """
    index_path = xml_dir / "index.xml"
    if not index_path.exists():
        print(f"[!] Warning: {index_path} not found.")
        return {}

    tree = ET.parse(index_path)
    root = tree.getroot()

    # We will organize into specific target pages:
    # cpp/base/2hdmc
    # cpp/base/higgstools
    # cpp/project/dihiggs
    # cpp/project/dihiggs-boundary
    # cpp/project/dihiggs-hep-cross
    # cpp/project/dihiggs-llp-recast
    categories = {
        "cpp_base_2hdmc": {
            "title": "2HDMC Base Library (C++)",
            "module": "dihiggs",
            "group": "base",
            "desc": "Two-Higgs-Doublet Model Calculator base library source reference.",
            "patterns": ["dihiggs/2hdmc/src"],
            "symbols": [],
        },
        "cpp_base_higgstools": {
            "title": "HiggsTools Base Library (C++)",
            "module": "dihiggs",
            "group": "base",
            "desc": "HiggsBounds and HiggsSignals prediction and limits library.",
            "patterns": ["dihiggs/higgstools/src", "dihiggs/higgstools/include"],
            "symbols": [],
        },
        "cpp_project_dihiggs": {
            "title": "dihiggs Evaluators & Scans (C++)",
            "module": "dihiggs",
            "group": "project",
            "desc": "Active 2HDM Type-I point evaluators, parameter scans, and convention executors.",
            "patterns": ["dihiggs/dihiggs/src"],
            "symbols": [],
        },
        "cpp_project_boundary": {
            "title": "dihiggs_boundary Evaluators (C++)",
            "module": "dihiggs_boundary",
            "group": "project",
            "desc": "C++ boundary point evaluators and limit intersection drivers.",
            "patterns": ["dihiggs_boundary/src"],
            "symbols": [],
        },
        "cpp_project_hep_cross": {
            "title": "dihiggs_hep_cross Adapters (C++)",
            "module": "dihiggs_hep_cross",
            "group": "project",
            "desc": "Theory adapter snapshots and cross-section calculation bridges.",
            "patterns": ["dihiggs_hep_cross"],
            "symbols": [],
        },
        "cpp_project_llp_recast": {
            "title": "dihiggs_llp_recast Geometry Drivers (C++)",
            "module": "dihiggs_llp_recast",
            "group": "project",
            "desc": "ATLAS DV+jets geometry drivers and detector acceptance instruments.",
            "patterns": ["dihiggs_llp_recast/src", "recast_viewer/preprocess/instrumentation"],
            "symbols": [],
        },
    }

    def assign_category(filepath: str):
        norm = filepath.replace("\\", "/")
        for cat_id, info in categories.items():
            for pat in info["patterns"]:
                if pat in norm:
                    return cat_id
        return None

    # First, collect all class/struct compounds
    seen_symbols = set()

    for comp in root.findall("compound"):
        kind = comp.attrib.get("kind")
        refid = comp.attrib.get("refid")
        comp_file = xml_dir / f"{refid}.xml"
        if not comp_file.exists():
            continue

        try:
            c_tree = ET.parse(comp_file)
            c_root = c_tree.getroot()
            c_def = c_root.find("compounddef")
            if c_def is None:
                continue

            c_name = c_def.findtext("compoundname", "").strip()
            loc_el = c_def.find("location")
            c_file = loc_el.attrib.get("file", "") if loc_el is not None else ""
            c_line = loc_el.attrib.get("line", "") if loc_el is not None else ""

            cat_id = assign_category(c_file)
            if not cat_id:
                continue

            if kind in ("class", "struct"):
                brief = clean_doxygen_text(c_def.find("briefdescription"))
                detail = clean_doxygen_text(c_def.find("detaileddescription"))
                doc = brief or detail
                
                # Member functions
                methods = []
                for sec in c_def.findall("sectiondef"):
                    for mem in sec.findall("memberdef"):
                        m_kind = mem.attrib.get("kind")
                        if m_kind not in ("function", "variable"):
                            continue
                        m_name = mem.findtext("name", "")
                        m_type = clean_doxygen_text(mem.find("type"))
                        m_args = mem.findtext("argsstring", "")
                        m_brief = clean_doxygen_text(mem.find("briefdescription"))
                        m_detail = clean_doxygen_text(mem.find("detaileddescription"))
                        m_loc = mem.find("location")
                        m_line = m_loc.attrib.get("line", "") if m_loc is not None else ""
                        m_doc = m_brief or m_detail

                        methods.append({
                            "name": m_name,
                            "type": m_type,
                            "args": m_args,
                            "kind": m_kind,
                            "doc": m_doc,
                            "line": m_line,
                            "file": c_file,
                            "documented": bool(m_doc)
                        })

                sym_id = f"class_{c_name}_{c_file}"
                if sym_id not in seen_symbols:
                    seen_symbols.add(sym_id)
                    categories[cat_id]["symbols"].append({
                        "kind": kind,
                        "name": c_name,
                        "doc": doc,
                        "file": c_file,
                        "line": c_line,
                        "documented": bool(doc),
                        "methods": methods
                    })

            elif kind == "file":
                # Extract standalone functions and variables
                for sec in c_def.findall("sectiondef"):
                    for mem in sec.findall("memberdef"):
                        m_kind = mem.attrib.get("kind")
                        if m_kind not in ("function", "variable"):
                            continue
                        m_name = mem.findtext("name", "")
                        m_type = clean_doxygen_text(mem.find("type"))
                        m_args = mem.findtext("argsstring", "")
                        m_brief = clean_doxygen_text(mem.find("briefdescription"))
                        m_detail = clean_doxygen_text(mem.find("detaileddescription"))
                        m_loc = mem.find("location")
                        m_line = m_loc.attrib.get("line", "") if m_loc is not None else ""
                        m_file = m_loc.attrib.get("file", c_file) if m_loc is not None else c_file
                        m_doc = m_brief or m_detail

                        sym_id = f"func_{m_name}_{m_file}_{m_line}"
                        if sym_id not in seen_symbols:
                            seen_symbols.add(sym_id)
                            categories[cat_id]["symbols"].append({
                                "kind": m_kind,
                                "name": m_name,
                                "type": m_type,
                                "args": m_args,
                                "doc": m_doc,
                                "file": m_file,
                                "line": m_line,
                                "documented": bool(m_doc),
                                "methods": []
                            })

        except Exception as e:
            continue

    return categories

def extract_python_symbols():
    """
    Extract Python documentation using Griffe.
    Covers packages and scripts with real functions across modules.
    """
    # Import griffe from venv
    try:
        import griffe
    except ImportError:
        venv_site = SITE_DIR / ".venv-docs" / "lib"
        for p in venv_site.glob("python3.*/site-packages"):
            sys.path.insert(0, str(p))
        import griffe

    targets = {
        "dihiggs": [
            {"type": "pkg", "name": "orchestrator", "search": str(ROOT_DIR / "dihiggs" / "dihiggs" / "app")},
            {"type": "pkg", "name": "lib", "search": str(ROOT_DIR / "dihiggs" / "mlpython")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs" / "scripts"},
        ],
        "dihiggs_boundary": [
            {"type": "pkg", "name": "dhb", "search": str(ROOT_DIR / "dihiggs_boundary" / "python")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs_boundary" / "scripts"},
        ],
        "dihiggs_hep_cross": [
            {"type": "pkg", "name": "llp_recast", "search": str(ROOT_DIR / "dihiggs_hep_cross" / "src")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs_hep_cross" / "scripts"},
        ],
        "dihiggs_llp_recast": [
            {"type": "pkg", "name": "dvrecast", "search": str(ROOT_DIR / "dihiggs_llp_recast" / "src")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs_llp_recast" / "scripts"},
        ],
        "dihiggs_ufo": [
            {"type": "pkg", "name": "pack_aa_kinematic_validation", "search": str(ROOT_DIR / "dihiggs_ufo" / "studies" / "pack_aa_kinematic_validation" / "src")},
            {"type": "pkg", "name": "pack_a_seed_mc", "search": str(ROOT_DIR / "dihiggs_ufo" / "studies" / "pack_a_seed_mc" / "src")},
            {"type": "scripts", "dir": ROOT_DIR / "dihiggs_ufo" / "scripts"},
        ],
        "recast_viewer": [
            {"type": "pkg", "name": "preprocess", "search": str(ROOT_DIR / "recast_viewer")},
        ],
    }

    results = {}

    for mod_name, item_list in targets.items():
        results[mod_name] = {
            "title": f"{mod_name} Python Reference",
            "module": mod_name,
            "symbols": []
        }

        for item in item_list:
            if item["type"] == "pkg":
                pkg_name = item["name"]
                search_path = item["search"]
                try:
                    loader = griffe.GriffeLoader(search_paths=[search_path])
                    mod = loader.load(pkg_name, try_relative_path=False)
                    extract_griffe_members(mod, results[mod_name]["symbols"], mod_name)
                except Exception as e:
                    print(f"[!] Warning: failed to load Python pkg {pkg_name}: {e}")

            elif item["type"] == "scripts":
                sdir = item["dir"]
                if not sdir.exists():
                    continue
                loader = griffe.GriffeLoader(search_paths=[str(sdir)])
                for pyfile in sorted(sdir.glob("*.py")):
                    if pyfile.name.startswith("__"):
                        continue
                    try:
                        script_mod = loader.load(pyfile.stem, try_relative_path=False)
                        extract_griffe_members(script_mod, results[mod_name]["symbols"], mod_name, is_script=True)
                    except Exception as e:
                        # Skip syntax/import errors on legacy scripts
                        continue

    return results

def extract_griffe_members(module, symbol_list, mod_name, is_script=False):
    """Recursively extract functions and classes from Griffe module."""
    for name, member in module.members.items():
        if member.is_alias:
            continue
        # Avoid private/dunder except __init__
        if name.startswith("_") and not name.startswith("__init__"):
            continue

        doc = member.docstring.value.strip() if member.docstring else ""
        has_doc = bool(doc)
        lineno = member.lineno or 1
        filepath = str(member.filepath) if member.filepath else ""
        rel_file = Path(filepath).relative_to(ROOT_DIR).as_posix() if filepath and Path(filepath).is_relative_to(ROOT_DIR) else filepath

        if member.is_function:
            # Format signature
            params = []
            for p in member.parameters:
                p_str = p.name
                if p.annotation:
                    p_str += f": {p.annotation}"
                if p.default:
                    p_str += f" = {p.default}"
                params.append(p_str)
            sig = f"{member.name}({', '.join(params)})"
            if member.returns:
                sig += f" -> {member.returns}"

            symbol_list.append({
                "kind": "function",
                "name": member.canonical_path,
                "sig": sig,
                "doc": doc,
                "file": rel_file,
                "line": lineno,
                "documented": has_doc,
                "is_script": is_script
            })

        elif member.is_class:
            methods = []
            for m_name, m_mem in member.members.items():
                if m_mem.is_alias:
                    continue
                if m_name.startswith("_") and not m_name.startswith("__init__"):
                    continue
                if m_mem.is_function:
                    m_doc = m_mem.docstring.value.strip() if m_mem.docstring else ""
                    m_params = [p.name for p in m_mem.parameters]
                    m_sig = f"{m_name}({', '.join(m_params)})"
                    methods.append({
                        "name": m_name,
                        "sig": m_sig,
                        "doc": m_doc,
                        "line": m_mem.lineno or lineno,
                        "documented": bool(m_doc)
                    })

            symbol_list.append({
                "kind": "class",
                "name": member.canonical_path,
                "sig": f"class {member.name}",
                "doc": doc,
                "file": rel_file,
                "line": lineno,
                "documented": has_doc,
                "methods": methods,
                "is_script": is_script
            })

        elif member.is_module and not is_script:
            # Recurse into submodules
            extract_griffe_members(member, symbol_list, mod_name, is_script=False)

def write_markdown_page(out_path: Path, title: str, description: str, badges: list, stats: dict, symbols: list):
    """Write Starlight MDX page for API documentation."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    badge_html = " ".join([f'<span class="wired-pill {b.get("color", "")}">{b["text"]}</span>' for b in badges])
    total = stats.get("total", len(symbols))
    doc_count = stats.get("documented", sum(1 for s in symbols if s.get("documented", False)))
    pct = (doc_count / total * 100) if total > 0 else 100.0

    lines = [
        "---",
        f"title: \"{title}\"",
        f"description: \"{description}\"",
        "---",
        "",
        '<div style="margin-bottom: 1.5rem; display: flex; gap: 8px; flex-wrap: wrap;">',
        f"  {badge_html}",
        "</div>",
        "",
        '<div class="wired-card">',
        '  <div class="wired-card-header">',
        '    <span>// SYMBOL METRICS & COVERAGE</span>',
        f'    <span class="wired-pill {"green" if pct >= 50 else "red"}">{pct:.1f}% DOCUMENTED</span>',
        '  </div>',
        '  <div class="wired-grid" style="margin: 0; font-size: 0.82rem;">',
        f'    <div><strong>TOTAL SYMBOLS:</strong> {total}</div>',
        f'    <div><strong>WITH DOCSTRINGS:</strong> {doc_count}</div>',
        f'    <div><strong>COVERAGE GAPS:</strong> {total - doc_count}</div>',
        '  </div>',
        '</div>',
        "",
        "## Defined Symbols",
        ""
    ]

    # Group symbols by file
    files_map = {}
    for sym in symbols:
        fname = sym.get("file", "unknown")
        files_map.setdefault(fname, []).append(sym)

    for fname, sym_list in sorted(files_map.items()):
        gh_file_link = get_github_link(fname)
        lines.append(f"### [`{fname}`]({gh_file_link})")
        lines.append("")

        for s in sym_list:
            name = s.get("name", "")
            kind = s.get("kind", "").upper()
            is_doc = s.get("documented", False)
            doc_badge = '<span class="wired-pill green">DOC</span>' if is_doc else '<span class="wired-pill red">UNDOCUMENTED</span>'
            line_no = s.get("line", "")
            gh_sym_link = get_github_link(fname, line_no)
            
            sig = s.get("sig", "")
            if not sig:
                ret_type = s.get("type", "")
                args = s.get("args", "")
                sig = f"{ret_type} {name}{args}".strip()

            lines.append(f"#### `{name}` {doc_badge}")
            lines.append(f"*Source: [{fname}:{line_no}]({gh_sym_link})*")
            lines.append("")
            lines.append("```cpp" if "cpp" in out_path.as_posix() else "```python")
            lines.append(sig)
            lines.append("```")
            lines.append("")

            if s.get("doc"):
                lines.append(f"> {s['doc']}")
                lines.append("")

            # Inner methods if class
            if s.get("methods"):
                lines.append("**Members & Methods:**")
                lines.append("")
                for m in s["methods"]:
                    m_name = m.get("name")
                    m_doc_badge = '<span class="wired-pill green">DOC</span>' if m.get("documented") else '<span class="wired-pill red">GAP</span>'
                    m_sig = m.get("sig") or f"{m.get('type', '')} {m_name}{m.get('args', '')}".strip()
                    m_line = m.get("line", "")
                    m_link = get_github_link(fname, m_line)
                    lines.append(f"- `{m_name}` {m_doc_badge} &mdash; [`L{m_line}`]({m_link})")
                    if m.get("doc"):
                        lines.append(f"  <br/><small>{m['doc']}</small>")
                lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")

def main():
    print("=================================================================")
    print("  WIRED // API REFERENCE GENERATOR (C++ DOXYGEN & PYTHON GRIFFE)")
    print("=================================================================")
    
    xml_cache = TEMP_DIR / "doxygen"
    run_doxygen(xml_cache)

    print("[*] Parsing C++ Doxygen XML...")
    cpp_cats = parse_doxygen_xml(xml_cache / "xml")

    print("[*] Parsing Python AST via Griffe...")
    py_modules = extract_python_symbols()

    # Track overall summary table
    summary_stats = []

    # 1. Generate C++ Pages
    # Base Libraries
    for cat_id, cat_info in cpp_cats.items():
        if cat_info["group"] == "base":
            slug = cat_id.replace("cpp_base_", "")
            out_file = API_DOCS_DIR / "cpp" / "base" / f"{slug}.md"
        else:
            slug = cat_id.replace("cpp_project_", "")
            out_file = API_DOCS_DIR / "cpp" / "project" / f"{slug}.md"

        syms = cat_info["symbols"]
        total_syms = 0
        doc_syms = 0
        for s in syms:
            total_syms += 1
            if s.get("documented"):
                doc_syms += 1
            for m in s.get("methods", []):
                total_syms += 1
                if m.get("documented"):
                    doc_syms += 1

        stats = {"total": total_syms, "documented": doc_syms}
        badges = [
            {"text": "C++", "color": "red"},
            {"text": cat_info["group"].upper(), "color": ""},
            {"text": f"MODULE: {cat_info['module']}", "color": ""},
            {"text": f"COMMIT: {SUBMODULE_MAP[cat_info['module']]['commit'][:7]}", "color": ""}
        ]

        write_markdown_page(
            out_file,
            cat_info["title"],
            cat_info["desc"],
            badges,
            stats,
            syms
        )

        pct = (doc_syms / total_syms * 100) if total_syms > 0 else 0
        summary_stats.append({
            "name": cat_info["title"],
            "lang": "C++",
            "module": cat_info["module"],
            "group": cat_info["group"].capitalize(),
            "total": total_syms,
            "doc": doc_syms,
            "pct": pct,
            "link": f"/api/cpp/{cat_info['group']}/{slug}/"
        })

    # 2. Generate Python Pages
    for mod_name, pinfo in py_modules.items():
        slug = mod_name.replace("_", "-")
        out_file = API_DOCS_DIR / "python" / f"{slug}.md"

        syms = pinfo["symbols"]
        total_syms = 0
        doc_syms = 0
        for s in syms:
            total_syms += 1
            if s.get("documented"):
                doc_syms += 1
            for m in s.get("methods", []):
                total_syms += 1
                if m.get("documented"):
                    doc_syms += 1

        stats = {"total": total_syms, "documented": doc_syms}
        badges = [
            {"text": "PYTHON", "color": "green"},
            {"text": "PROJECT", "color": ""},
            {"text": f"MODULE: {mod_name}", "color": ""},
            {"text": f"COMMIT: {SUBMODULE_MAP[mod_name]['commit'][:7]}", "color": ""}
        ]

        write_markdown_page(
            out_file,
            pinfo["title"],
            f"Python API reference and module exports for {mod_name}.",
            badges,
            stats,
            syms
        )

        pct = (doc_syms / total_syms * 100) if total_syms > 0 else 0
        summary_stats.append({
            "name": pinfo["title"],
            "lang": "Python",
            "module": mod_name,
            "group": "Project",
            "total": total_syms,
            "doc": doc_syms,
            "pct": pct,
            "link": f"/api/python/{slug}/"
        })

    # 3. Generate API Index Page
    total_all = sum(s["total"] for s in summary_stats)
    doc_all = sum(s["doc"] for s in summary_stats)
    overall_pct = (doc_all / total_all * 100) if total_all > 0 else 0

    index_lines = [
        "---",
        "title: \"API Reference & Code Coverage\"",
        "description: \"Comprehensive C++ and Python API index across base libraries and workspace modules.\"",
        "---",
        "",
        '<div class="wired-card">',
        '  <div class="wired-card-header">',
        '    <span>// SYSTEM_AUDIT: TOTAL WORKSPACE CODEBASE COVERAGE</span>',
        f'    <span class="wired-pill {"green" if overall_pct >= 50 else "red"}">{overall_pct:.1f}% GLOBAL COVERAGE</span>',
        '  </div>',
        '  <div class="wired-grid" style="font-size: 0.85rem;">',
        f'    <div><strong>TOTAL SYMBOLS AUDITED:</strong> {total_all}</div>',
        f'    <div><strong>DOCUMENTED SYMBOLS:</strong> {doc_all}</div>',
        f'    <div><strong>DOCUMENTATION GAPS:</strong> {total_all - doc_all}</div>',
        '  </div>',
        '</div>',
        "",
        "## Submodule API Coverage Matrix",
        "",
        "| Module & Library | Language | Category | Pinned Commit | Symbols | Documented | Coverage |",
        "|---|---|---|---|---|---|---|"
    ]

    for s in summary_stats:
        mod_key = s["module"]
        commit_short = SUBMODULE_MAP.get(mod_key, {}).get("commit", "main")[:7]
        pct_str = f"{s['pct']:.1f}%"
        badge_cls = "green" if s['pct'] >= 50 else "red"
        index_lines.append(
            f"| [**{s['name']}**]({s['link']}) | `{s['lang']}` | {s['group']} | `{commit_short}` | {s['total']} | {s['doc']} | <span class=\"wired-pill {badge_cls}\">{pct_str}</span> |"
        )

    index_lines.extend([
        "",
        "## Structure & Methodology",
        "",
        "- **C++ Parsing**: Generated using static Doxygen XML AST parsing, indexing classes, methods, signatures, and inline descriptions.",
        "- **Python Parsing**: Generated using Griffe static inspection, parsing abstract syntax trees without runtime module execution to ensure strict side-effect isolation.",
        "- **Direct GitHub Links**: Every symbol links directly to its definition line on GitHub at the exact pinned submodule commit hash.",
        "- **Coverage Auditing**: Symbols lacking docstrings are explicitly marked with red pills (`UNDOCUMENTED`) to highlight technical debt."
    ])

    (API_DOCS_DIR / "index.md").write_text("\n".join(index_lines), encoding="utf-8")

    # Print Terminal Report
    print("\n" + "=" * 76)
    print(f"{'MODULE / PACKAGE':<32} {'LANG':<8} {'TOTAL':<8} {'DOC':<8} {'COVERAGE':<10}")
    print("-" * 76)
    for s in summary_stats:
        print(f"{s['name'][:30]:<32} {s['lang']:<8} {s['total']:<8} {s['doc']:<8} {s['pct']:.1f}%")
    print("-" * 76)
    print(f"{'OVERALL WORKSPACE':<32} {'--':<8} {total_all:<8} {doc_all:<8} {overall_pct:.1f}%")
    print("=" * 76 + "\n")

if __name__ == "__main__":
    main()
