#!/usr/bin/env python3
"""Extract supplied compiler packages in scratch; install nothing on the host."""
import argparse
from pathlib import Path
import subprocess

p=argparse.ArgumentParser()
p.add_argument('--clang-packages',type=Path,required=True)
a=p.parse_args()
packet=Path(__file__).resolve().parents[1]
scratch=packet/'scratch'; scratch.mkdir(exist_ok=True)
dest=scratch/'clang18'; dest.mkdir(exist_ok=True)
packages=sorted(a.clang_packages.glob('*.deb'))
assert packages,'no compiler packages supplied'
for package in packages:
    members=subprocess.check_output(['ar','t',str(package)],text=True).splitlines()
    data=next(x for x in members if x.startswith('data.tar.'))
    archive=scratch/(package.name+'.'+data)
    with archive.open('wb') as output:
        subprocess.run(['ar','p',str(package),data],stdout=output,check=True)
    subprocess.run(['tar','-xf',str(archive),'-C',str(dest)],check=True)
    archive.unlink()
print('Compiler packages extracted in scratch/clang18')
