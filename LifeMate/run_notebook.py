import os, sys, io, json, time, traceback, contextlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(str(BASE_DIR))

nb_path = BASE_DIR / "baseline.ipynb"
print(f"Loading {nb_path} ...", flush=True)
nb = json.loads(nb_path.read_text(encoding="utf-8"))

ns = {"__name__": "__main__"}
exec_count = 0
total_cells = len(nb["cells"])

print(f"Starting execution of {total_cells} cells in {BASE_DIR} ...", flush=True)

for idx, cell in enumerate(nb["cells"]):
    c_type = cell.get("cell_type")
    cid = cell.get("id", f"cell_{idx}")
    if c_type != "code":
        continue
    src = "".join(cell.get("source", []))
    if not src.strip():
        continue
    exec_count += 1
    cell["execution_count"] = exec_count
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    t0 = time.time()
    first_line = src.strip().splitlines()[0][:70]
    print(f"[{idx+1}/{total_cells}] (exec #{exec_count}, id={cid}) \"{first_line}\" ...", flush=True)
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            exec(compile(src, f"<cell-{idx}-{cid}>", "exec"), ns)
    except Exception as e:
        tb = traceback.format_exc()
        buf_err.write(tb)
        print(f"ERROR in Cell {idx} ({cid}):\n{tb}", flush=True)
        cell["outputs"] = [{"name": "stderr", "output_type": "stream", "text": buf_err.getvalue().splitlines(True)}]
        nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        sys.exit(1)

    out_str = buf_out.getvalue()
    err_str = buf_err.getvalue()
    outputs = []
    if out_str:
        outputs.append({"name": "stdout", "output_type": "stream", "text": out_str.splitlines(True)})
        lines = out_str.strip().splitlines()
        if len(lines) <= 8:
            for l in lines: print(f"   {l}", flush=True)
        else:
            for l in lines[:4]: print(f"   {l}", flush=True)
            print(f"   ... ({len(lines)-8} lines omitted) ...", flush=True)
            for l in lines[-4:]: print(f"   {l}", flush=True)
    if err_str:
        outputs.append({"name": "stderr", "output_type": "stream", "text": err_str.splitlines(True)})
        for l in err_str.strip().splitlines()[:5]: print(f"   [stderr] {l}", flush=True)
    cell["outputs"] = outputs
    print(f"   -> Done in {time.time()-t0:.2f}s", flush=True)

nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("=== NOTEBOOK EXECUTION COMPLETE & SAVED ===", flush=True)

sub_path = BASE_DIR / "result" / "submission.jsonl"
if sub_path.exists():
    lines = [l for l in sub_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"=== SUBMISSION VERIFIED: {len(lines)} rows at {sub_path} ===", flush=True)
    for i, l in enumerate(lines[:3]):
        print(f"Row {i+1}: {l}", flush=True)
    if len(lines) > 3:
        print(f"Row {len(lines)}: {lines[-1]}", flush=True)
else:
    print(f"WARNING: {sub_path} not found!")
