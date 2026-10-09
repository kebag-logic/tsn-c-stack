#!/usr/bin/env python3
"""Provide scratch launchers without touching shared compiler files."""
import argparse, os, pathlib, shutil, subprocess
ap=argparse.ArgumentParser();ap.add_argument('packet',type=pathlib.Path);ap.add_argument('compiler_prefix',type=pathlib.Path);ap.add_argument('test_prefix',type=pathlib.Path);ap.add_argument('command',nargs=argparse.REMAINDER);a=ap.parse_args();p=a.packet.resolve();cc=a.compiler_prefix.resolve();gt=a.test_prefix.resolve();sdk=p/'scratch/sdk/root';bin=p/'scratch/bin';bin.mkdir(exist_ok=True)
resource=sdk/'usr/lib/llvm-18/lib/clang/18'
shutil.copytree(cc/'root/usr/lib/llvm-18/lib/clang/18/include',resource/'include',dirs_exist_ok=True)
launcher=bin/'compiler-launcher.py'
launcher.write_text("#!/usr/bin/env python3\nimport os,sys,pathlib\nprefix="+repr(str(cc))+"\nsdk="+repr(str(sdk))+"\nresource="+repr(str(resource))+"\nenv=dict(os.environ)\nenv['LD_LIBRARY_PATH']=prefix+'/root/usr/lib/x86_64-linux-gnu:'+env.get('LD_LIBRARY_PATH','')\nargs=sys.argv[1:]\ncxx='++' in pathlib.Path(sys.argv[0]).name\nif args and args[0]=='-cc1': flags=[]\nelse:\n flags=['-resource-dir='+resource]\n if cxx: flags+=['-nostdinc++','-isystem',sdk+'/usr/include/c++/13','-isystem',sdk+'/usr/include/x86_64-linux-gnu/c++/13','-isystem',sdk+'/usr/include/c++/13/backward']\nexe=prefix+'/root/usr/bin/'+('clang++-18' if cxx else 'clang-18')\nos.execve(exe,[exe,*flags,*args],env)\n")
launcher.chmod(0o755)
for name in ['clang','clang++','clang-18']:
 dest=bin/name
 if not dest.exists():dest.symlink_to(launcher.name)
env=dict(os.environ);env.update(PATH=str(cc/'bin')+':'+str(bin)+':'+env['PATH'],TSN_CLANG=str(bin/'clang-18'),PKG_CONFIG_PATH=str(gt/'lib/pkgconfig'),CMAKE_PREFIX_PATH=str(gt),LD_LIBRARY_PATH=str(gt/'lib')+':'+env.get('LD_LIBRARY_PATH',''))
raise SystemExit(subprocess.run(a.command,env=env).returncode)
