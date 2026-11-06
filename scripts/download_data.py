"""Download ECB source files with bounded retries and strict byte verification."""
from pathlib import Path
import sys
import io
import zipfile
import hashlib
import urllib.request
import time
import json
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from space_cx.analysis import SOURCE_URL,CSV_NAME,CSV_SHA256

def download(destination=None):
    dest=Path(destination or ROOT/'data'/'raw')
    target=dest/CSV_NAME
    if target.exists():
        actual=hashlib.sha256(target.read_bytes()).hexdigest()
        if actual!=CSV_SHA256:
            raise ValueError('Local raw CSV differs from the verified source. Preserve it and investigate.')
        return target
    for attempt in range(3):
        try:
            request=urllib.request.Request(SOURCE_URL,headers={'User-Agent':'SPACE2024-reproducible-research/1.0'})
            with urllib.request.urlopen(request,timeout=60) as response:
                content=response.read()
            break
        except (OSError,TimeoutError):
            if attempt==2:
                raise RuntimeError('Could not fetch ECB data. Download the ZIP from the URL in README and extract its three files into data/raw/.')
            time.sleep(attempt+1)
    archive=zipfile.ZipFile(io.BytesIO(content))
    wanted=[CSV_NAME,'SPACE 2024 Codebook.xlsx','SPACE 2024 labels.xlsx']
    payload={}
    for name in wanted:
        matches=[n for n in archive.namelist() if Path(n).name==name]
        if len(matches)!=1:raise ValueError(f'Missing or ambiguous archive member: {name}')
        payload[name]=archive.read(matches[0])
    if hashlib.sha256(payload[CSV_NAME]).hexdigest()!=CSV_SHA256:
        raise ValueError('ECB source changed since this analysis. Review and update the checksum deliberately.')
    dest.mkdir(parents=True,exist_ok=True)
    for name,b in payload.items(): (dest/name).write_bytes(b)
    (dest/'download_manifest.json').write_text(json.dumps({'source_url':SOURCE_URL,
        'downloaded_utc':datetime.now(timezone.utc).isoformat(),'csv_sha256':CSV_SHA256},indent=2))
    return target

if __name__=='__main__':print(download())
