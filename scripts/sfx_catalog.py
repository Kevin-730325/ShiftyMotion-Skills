#!/usr/bin/env python3
"""Query bundled sounds without decoding/loading all audio into context."""
from pathlib import Path
import argparse,hashlib,json,wave
p=argparse.ArgumentParser();p.add_argument('--category');p.add_argument('--max-duration',type=float);p.add_argument('--reverse',action='store_true');p.add_argument('--limit',type=int,default=10);p.add_argument('--json',action='store_true');p.add_argument('--verify',action='store_true');args=p.parse_args()
root=Path(__file__).resolve().parents[1]/'assets/sfx';data=json.loads((root/'manifest.json').read_text());rows=data['sounds']
if args.verify:
 for r in rows:
  f=root/r['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'],f
  with wave.open(str(f),'rb') as w:
   assert w.getnchannels()==r['channels'] and w.getframerate()==r['sample_rate'],f
   assert abs(w.getnframes()/w.getframerate()-r['duration_seconds'])<1e-6,f
   raw=w.readframes(w.getnframes());assert len(raw)==w.getnframes()*w.getnchannels()*w.getsampwidth(),f
 print(f"Verified {len(rows)} WAVs: SHA-256, format, duration and full PCM read. Not a listening review.");raise SystemExit(0)
if args.category:
 ids=[c['id'] for c in data['categories']]
 if args.category not in ids:p.error('category must be one of '+', '.join(ids))
 rows=[r for r in rows if r['category']==args.category]
if args.max_duration is not None:rows=[r for r in rows if r['duration_seconds']<=args.max_duration]
if args.reverse:rows=[r for r in rows if r['reverse']]
rows=sorted(rows,key=lambda r:(r['duration_seconds'],r['id']))[:max(0,args.limit)]
if args.json:print(json.dumps(rows,ensure_ascii=False,indent=2))
else:
 for r in rows:print(f"{r['id']} | {r['duration_seconds']:.3f}s | {r['sample_peak_dbfs']:.1f} dBFS | {root/r['file']}")
