#!/usr/bin/env python3
"""Prepare only disposable comparison inputs from the exact source and public authority."""
import pathlib,shutil,subprocess,sys
repo,packet=map(lambda x:pathlib.Path(x).resolve(),sys.argv[1:3]);head=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip();assert head=="f3dc2ae5bad02aa05a504b43c207e8b304d2bed5"
ref="09c7231eca343607c97c0d66abebb2553688712c"
(packet/"receipts").mkdir(parents=True,exist_ok=True)
for name in ("head","reference"):(packet/"scratch"/name).mkdir(parents=True,exist_ok=True)
for f in ("acmp.c","acmp.h"):
 source=repo/("src" if f.endswith(".c") else "include")/f
 shutil.copyfile(source,packet/"scratch/head"/f)
 data=subprocess.check_output(["gh","api",f"repos/kebag-logic/milan-fpga/contents/sw/firmware/ctrl/acmp/{f}?ref={ref}","-H","Accept: application/vnd.github.raw+json"])
 (packet/"receipts"/("upstream-"+f)).write_bytes(data);(packet/"scratch/reference"/f).write_bytes(data)
print("Exact-head and pinned-reference comparison inputs prepared")
