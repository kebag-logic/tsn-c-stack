from pathlib import Path
import json, re, subprocess
p=Path('$VALIDATION_STORAGE/tsn21-a602/round3')
o=Path('$MANAGEMENT/2026-09-23/tsn21-a602/round3')
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
required={
 'reset-drops-bound-cache-only': ('AcmpCore.A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal', 'A31 the bound cache survives reset to publish the stopped binding withdrawal', 'AcmpCore.R622W2StoreResetOfABoundStoppedSinkPublishesItsWithdrawal'),
 'reset-drops-started-cache-only': ('AcmpCore.A31StoreRestoreOfAStoppedRecordPublishesTheStop', 'A31 the started cache survives reset to publish the restored stop', 'AcmpCore.R622W3StoreRestoreOfAStoppedRecordPublishesTheStop')}
rows=[]
for group,count,variants in [
 ('probes',79,['head','reset-drops-bound-cache-only','reset-drops-started-cache-only','moved-means-nonzero','publish-ignores-bound','publish-skips-last-sink','finish-publishes-after-admission']),
 ('probes-scoped',79,['head','reset-drops-bound-cache-only','reset-drops-started-cache-only','settled-ignores-rsv-ok','moved-means-nonzero','publish-ignores-bound','publish-skips-last-sink','finish-publishes-after-admission']),
 ('witness',81,['head','reset-drops-bound-cache-only','reset-drops-started-cache-only','settled-ignores-rsv-ok'])]:
 summary=(p/(group+'.log')).read_text()
 for variant in variants:
  log=(p/group/variant/'run.log').read_text()
  build=(p/group/variant/'build.log').read_text()
  assert 'Built target acmp_tests' in build
  assert re.search(r'\[==========\] '+str(count)+r' tests from .* ran\.',log)
  failed=sorted(set(re.findall(r'^\[  FAILED  \] ([A-Za-z0-9_.]+)',log,re.M)))
  rc=int(re.search(r'^'+re.escape(variant)+r': rc (\d+);',summary,re.M)[1])
  assert rc==(0 if variant=='head' else 1)
  assert bool(failed)==(variant!='head')
  if variant in required:
   test,needle,witness=required[variant]
   assert test in failed and needle in log
   if group=='witness': assert witness in failed
  rows.append(dict(group=group,variant=variant,instances=count,rc=rc,failed=failed))
original=(p/'probes.log').read_text()
assert 'settled-ignores-rsv-ok: replacement failed' in original
rv=[]
for variant,expected in [('head',0),('reset-drops-bound-cache-only',1),('reset-drops-started-cache-only',0)]:
 base=p/'rv32-controls'/('rv32-probe-'+variant)
 rc=int(base.with_suffix('.rc').read_text())
 assert rc==expected
 if expected:
  assert 'command failed: qemu-system-riscv32' in base.with_suffix('.log').read_text()
  configs=[]
  for kind in ('Debug','Release'):
   build=base/kind.lower()
   assert 'Built target rv32_smoke' in (build/'build.log').read_text()
   command=['qemu-system-riscv32','-machine','virt','-nographic','-bios','none','-kernel',str(build/'rv32_smoke.elf'),'-no-reboot']
   run=subprocess.run(command,capture_output=True,text=True,timeout=30)
   assert run.returncode==34
   (build/'audit-smoke.log').write_text(run.stdout+run.stderr)
   (build/'audit-smoke.rc').write_text(str(run.returncode)+'\n')
   configs.append(dict(configuration=kind,build_rc=0,smoke_rc=run.returncode,expected_failure=True))
 else:
  configs=json.loads((base/'results.json').read_text())
  assert len(configs)==2 and all(config['rc']==0 for config in configs)
 rv.append(dict(variant=variant,rc=rc,configurations=configs))
result=dict(head=head,original_probe_limit='The RSV_OK search string occurs twice; the original script refused its replacement. The scoped rerun uses the exact witness2.sh context and all seven faults execute.',runs=rows,rv32=rv)
(o/'review-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('review audit: head controls pass; seven scoped probes caught; W2/W3 and repository assertions catch both per-field faults; RV32 controls match')
