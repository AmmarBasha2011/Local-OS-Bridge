import os
import shutil
import sys
import time
import subprocess
import platform
import urllib.request
import urllib.error
import base64
import hashlib
import re
import csv
import json
import difflib
import gzip
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request

# --- CONFIGURATION ---
BASE_DIR = os.path.abspath("/home/ammar/Desktop/A Tech")
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

API_KEY = "ammar123" # Keep this secret! AI must use this in the URL.

app = FastAPI(
    title="Ultimate Local OS Bridge (V5 RAT)", 
    description="The absolute most advanced API for AI to control a Linux machine safely. 50+ Endpoints.",
    version="5.0.0"
)

# --- REAL-TIME CMD LOGGING ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 [{request.method}] {request.url.path}?{request.url.query}")
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    status_color = "🟢" if response.status_code == 200 else "🔴"
    print(f"{status_color} [STATUS: {response.status_code}] | Time: {process_time:.3f}s")
    return response

# --- SECURITY & UTILS ---
def get_safe_path(path: str):
    """Securely resolves paths and prevents Symlink Directory Traversal attacks."""
    # realpath resolves all symlinks, preventing jumping out of BASE_DIR
    safe_path = os.path.realpath(os.path.join(BASE_DIR, path))
    base_real = os.path.realpath(BASE_DIR)
    if not safe_path.startswith(base_real):
        raise HTTPException(status_code=403, detail="SECURITY BREACH: Attempted to escape sandbox.")
    return safe_path

def verify_key(key: str):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key")

# ==========================================
#         1. CORE FILE OPERATIONS
# ==========================================
tags_file = ["1. Core File Operations"]

@app.get("/list", tags=tags_file)
def list_files(api_key: str, directory: str = "."):
    verify_key(api_key)
    return {"files": os.listdir(get_safe_path(directory))}

@app.get("/read", tags=tags_file)
def read_file(api_key: str, filepath: str):
    verify_key(api_key)
    with open(get_safe_path(filepath), "r", encoding="utf-8", errors="ignore") as f:
        return {"content": f.read()}

@app.get("/write", tags=tags_file)
def write_file(api_key: str, filepath: str, content: str):
    verify_key(api_key)
    with open(get_safe_path(filepath), "w", encoding="utf-8") as f:
        f.write(content)
    return {"message": f"Wrote to {filepath}"}

@app.get("/append", tags=tags_file)
def append_file(api_key: str, filepath: str, content: str):
    verify_key(api_key)
    with open(get_safe_path(filepath), "a", encoding="utf-8") as f:
        f.write("\n" + content)
    return {"message": "Appended"}

@app.get("/delete", tags=tags_file)
def delete_item(api_key: str, path: str):
    verify_key(api_key)
    target = get_safe_path(path)
    os.remove(target) if os.path.isfile(target) else shutil.rmtree(target)
    return {"message": "Deleted"}

@app.get("/mkdir", tags=tags_file)
def create_directory(api_key: str, directory: str):
    verify_key(api_key)
    os.makedirs(get_safe_path(directory), exist_ok=True)
    return {"message": "Directory Created"}

@app.get("/copy", tags=tags_file)
def copy_item(api_key: str, source: str, destination: str):
    verify_key(api_key)
    src, dest = get_safe_path(source), get_safe_path(destination)
    shutil.copytree(src, dest) if os.path.isdir(src) else shutil.copy2(src, dest)
    return {"message": f"Copied to {destination}"}

@app.get("/rename", tags=tags_file)
def rename_item(api_key: str, old_path: str, new_path: str):
    verify_key(api_key)
    os.rename(get_safe_path(old_path), get_safe_path(new_path))
    return {"message": "Renamed"}

# ==========================================
#         2. ADVANCED FILESYSTEM (V5 NEW)
# ==========================================
tags_adv = ["2. Advanced Filesystem"]

@app.get("/info", tags=tags_adv)
def get_info(api_key: str, path: str):
    verify_key(api_key)
    stat = os.stat(get_safe_path(path))
    return {"size_bytes": stat.st_size, "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()}

@app.get("/find_ext", tags=tags_adv)
def find_by_extension(api_key: str, ext: str, directory: str = "."):
    verify_key(api_key)
    matches = []
    for root, _, files in os.walk(get_safe_path(directory)):
        for f in files:
            if f.endswith(ext):
                matches.append(os.path.relpath(os.path.join(root, f), BASE_DIR))
    return {"matches": matches}

@app.get("/split", tags=tags_adv, summary="Split a large file into smaller chunks")
def split_file(api_key: str, filepath: str, lines_per_chunk: int = 1000):
    verify_key(api_key)
    target = get_safe_path(filepath)
    chunks = []
    with open(target, 'r', encoding='utf-8', errors='ignore') as f:
        chunk, count = [], 0
        for line in f:
            chunk.append(line)
            if len(chunk) >= lines_per_chunk:
                out_name = f"{filepath}.part{count}"
                with open(get_safe_path(out_name), 'w') as out:
                    out.writelines(chunk)
                chunks.append(out_name)
                chunk, count = [], count + 1
        if chunk:
            out_name = f"{filepath}.part{count}"
            with open(get_safe_path(out_name), 'w') as out:
                out.writelines(chunk)
            chunks.append(out_name)
    return {"chunks_created": chunks}

@app.get("/merge", tags=tags_adv, summary="Merge multiple files into one")
def merge_files(api_key: str, file_paths_comma_sep: str, output_file: str):
    verify_key(api_key)
    files = file_paths_comma_sep.split(",")
    with open(get_safe_path(output_file), 'w', encoding='utf-8') as outfile:
        for fname in files:
            with open(get_safe_path(fname.strip()), 'r', encoding='utf-8', errors='ignore') as infile:
                outfile.write(infile.read())
    return {"message": f"Merged into {output_file}"}

@app.get("/empty_dir", tags=tags_adv)
def empty_directory(api_key: str, directory: str):
    verify_key(api_key)
    target = get_safe_path(directory)
    for filename in os.listdir(target):
        fp = os.path.join(target, filename)
        os.remove(fp) if os.path.isfile(fp) else shutil.rmtree(fp)
    return {"message": "Directory emptied without deleting the directory itself."}

@app.get("/symlink", tags=tags_adv)
def create_symlink(api_key: str, target_path: str, link_name: str):
    verify_key(api_key)
    os.symlink(get_safe_path(target_path), get_safe_path(link_name))
    return {"message": f"Symlink {link_name} created -> {target_path}"}

# ==========================================
#         3. DATA PROCESSING & SEARCH (V5 NEW)
# ==========================================
tags_data = ["3. Data Processing & Search"]

@app.get("/grep", tags=tags_data)
def grep_search(api_key: str, directory: str, search_string: str):
    verify_key(api_key)
    results = {}
    for root, _, files in os.walk(get_safe_path(directory)):
        for file in files:
            fp = os.path.join(root, file)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    matches = [l.strip() for l in f if search_string in l]
                    if matches:
                        results[os.path.relpath(fp, BASE_DIR)] = matches[:5]
            except: pass
    return {"results": results}

@app.get("/regex_search", tags=tags_data)
def regex_search(api_key: str, filepath: str, pattern: str):
    verify_key(api_key)
    with open(get_safe_path(filepath), "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    matches = re.findall(pattern, content)
    return {"match_count": len(matches), "matches": list(set(matches))[:50]}

@app.get("/diff", tags=tags_data, summary="Compare two files")
def file_diff(api_key: str, file1: str, file2: str):
    verify_key(api_key)
    with open(get_safe_path(file1), 'r', errors='ignore') as f1, open(get_safe_path(file2), 'r', errors='ignore') as f2:
        diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=file1, tofile=file2)
    return {"diff": "".join(diff)}

@app.get("/csv_to_json", tags=tags_data)
def csv_to_json(api_key: str, filepath: str):
    verify_key(api_key)
    with open(get_safe_path(filepath), 'r', encoding='utf-8', errors='ignore') as f:
        return {"data": list(csv.DictReader(f))}

@app.get("/json_to_csv", tags=tags_data)
def json_to_csv(api_key: str, json_filepath: str, output_csv: str):
    verify_key(api_key)
    with open(get_safe_path(json_filepath), 'r') as f:
        data = json.load(f)
    if not isinstance(data, list) or len(data) == 0:
        raise HTTPException(status_code=400, detail="JSON must be a list of dictionaries")
    with open(get_safe_path(output_csv), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return {"message": "Converted JSON to CSV"}

# ==========================================
#         4. SYSTEM & TERMINAL POWER
# ==========================================
tags_sys = ["4. System & OS Power"]

@app.get("/run_command", tags=tags_sys)
def run_command(api_key: str, command: str):
    verify_key(api_key)
    res = subprocess.run(command, shell=True, cwd=BASE_DIR, capture_output=True, text=True, timeout=20)
    return {"stdout": res.stdout.strip(), "stderr": res.stderr.strip(), "exit_code": res.returncode}

@app.get("/kill", tags=tags_sys, summary="Kill a Linux process by PID")
def kill_process(api_key: str, pid: int):
    verify_key(api_key)
    try:
        os.kill(pid, 9) # SIGKILL
        return {"message": f"Process {pid} killed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/whoami", tags=tags_sys)
def whoami(api_key: str):
    verify_key(api_key)
    return {"user": os.getlogin()}

@app.get("/uptime", tags=tags_sys)
def sys_uptime(api_key: str):
    verify_key(api_key)
    res = subprocess.run("uptime -p", shell=True, capture_output=True, text=True)
    return {"uptime": res.stdout.strip()}

@app.get("/ps", tags=tags_sys)
def list_processes(api_key: str):
    verify_key(api_key)
    res = subprocess.run("ps -eo pid,cmd,%mem,%cpu --sort=-%cpu | head -n 15", shell=True, capture_output=True, text=True)
    return {"processes": res.stdout.strip()}

@app.get("/git_status", tags=tags_sys)
def git_status(api_key: str, directory: str = "."):
    verify_key(api_key)
    res = subprocess.run("git status", shell=True, cwd=get_safe_path(directory), capture_output=True, text=True)
    return {"git_output": res.stdout.strip() or res.stderr.strip()}

# ==========================================
#         5. NETWORK & DOWNLOADS
# ==========================================
tags_net = ["5. Network Tools"]

@app.get("/download_url", tags=tags_net)
def download_file(api_key: str, url: str, save_as: str):
    verify_key(api_key)
    urllib.request.urlretrieve(url, get_safe_path(save_as))
    return {"message": "Downloaded"}

@app.get("/curl", tags=tags_net, summary="Make a GET request from the host machine")
def curl_url(api_key: str, url: str):
    verify_key(api_key)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return {"status": response.status, "body": response.read().decode('utf-8')[:2000]} # Limit output
    except Exception as e:
        return {"error": str(e)}

@app.get("/ip", tags=tags_net)
def public_ip(api_key: str):
    verify_key(api_key)
    try:
        with urllib.request.urlopen("https://api.ipify.org") as response:
            return {"public_ip": response.read().decode('utf-8')}
    except:
        return {"error": "Could not fetch IP"}

@app.get("/ports", tags=tags_net)
def open_ports(api_key: str):
    verify_key(api_key)
    res = subprocess.run("ss -tuln", shell=True, capture_output=True, text=True)
    return {"ports": res.stdout.strip()}

# ==========================================
#         6. SECURITY & ENCODING
# ==========================================
tags_sec = ["6. Security & Encoding"]

@app.get("/hash", tags=tags_sec)
def hash_file(api_key: str, filepath: str):
    verify_key(api_key)
    sha256_hash = hashlib.sha256()
    with open(get_safe_path(filepath), "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return {"sha256": sha256_hash.hexdigest()}

@app.get("/md5", tags=tags_sec)
def md5_file(api_key: str, filepath: str):
    verify_key(api_key)
    md5_hash = hashlib.md5()
    with open(get_safe_path(filepath), "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return {"md5": md5_hash.hexdigest()}

@app.get("/base64_read", tags=tags_sec)
def base64_read(api_key: str, filepath: str):
    verify_key(api_key)
    with open(get_safe_path(filepath), "rb") as f:
        return {"base64": base64.b64encode(f.read()).decode('utf-8')}

@app.get("/base64_write", tags=tags_sec)
def base64_write(api_key: str, filepath: str, b64_string: str):
    verify_key(api_key)
    with open(get_safe_path(filepath), "wb") as f:
        f.write(base64.b64decode(b64_string))
    return {"message": "Binary written"}

# ==========================================
#         7. ARCHIVE & COMPRESSION
# ==========================================
tags_zip = ["7. Archive & Compression"]

@app.get("/tar", tags=tags_zip)
def tar_folder(api_key: str, folder_path: str, archive_name: str):
    verify_key(api_key)
    shutil.make_archive(get_safe_path(archive_name), 'gztar', get_safe_path(folder_path))
    return {"message": "Tar created"}

@app.get("/untar", tags=tags_zip)
def untar_file(api_key: str, archive_path: str, extract_to: str = "."):
    verify_key(api_key)
    shutil.unpack_archive(get_safe_path(archive_path), get_safe_path(extract_to), format='gztar')
    return {"message": "Untarred"}

@app.get("/gzip", tags=tags_zip, summary="Compress a single file to .gz")
def gzip_file(api_key: str, filepath: str):
    verify_key(api_key)
    target = get_safe_path(filepath)
    with open(target, 'rb') as f_in, gzip.open(target + '.gz', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    return {"message": f"Compressed to {filepath}.gz"}

@app.get("/gunzip", tags=tags_zip, summary="Decompress a .gz file")
def gunzip_file(api_key: str, filepath: str):
    verify_key(api_key)
    target = get_safe_path(filepath)
    out_path = target[:-3] if target.endswith('.gz') else target + ".unzipped"
    with gzip.open(target, 'rb') as f_in, open(out_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    return {"message": f"Extracted to {out_path}"}


# --- AUTO-DOCUMENTATION FOR AI ---
def print_ai_instructions(public_url: str):
    print("\n" + "🔥"*35)
    print("🚀 API V5 (ULTIMATE RAT) IS LIVE")
    print(f"🔗 PUBLIC LINK: {public_url}")
    print(f"🔗 SWAGGER UI:  {public_url}/docs")
    print(f"🔑 API KEY REQ: ?api_key={API_KEY}")
    print("🔥"*35)
    print("\n--- NEW V5 CAPABILITIES FOR AI ---")
    print("🧠 DATA: /csv_to_json, /json_to_csv, /diff, /regex_search")
    print("⚡ SYSTEM: /kill, /whoami, /uptime, /git_status")
    print("🌐 NETWORK: /ip, /ports, /curl (Act as proxy)")
    print("📂 ADVANCED FS: /split, /merge, /symlink, /find_ext")
    print("📦 COMPRESSION: /gzip, /gunzip, /tar, /untar")
    print("----------------------------------\n")

# --- EXECUTION ---
if __name__ == "__main__":
    import uvicorn
    import threading
    from pycloudflared import try_cloudflare

    PORT = 8000

    def start_tunnel():
        time.sleep(2)
        try:
            tunnel = try_cloudflare(port=PORT)
            public_url = tunnel.tunnel 
            print_ai_instructions(public_url)
        except Exception as e:
            print(f"Tunnel Error: {e}")

    tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
    tunnel_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
