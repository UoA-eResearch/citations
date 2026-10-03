#!/bin/bash
# Bare clones of the 12 SWE-bench repositories (full history; git grep works on bare repos at a given commit)
cd "$(dirname "$0")/../data/repos"
for r in astropy/astropy django/django matplotlib/matplotlib mwaskom/seaborn pallets/flask psf/requests pydata/xarray pylint-dev/pylint pytest-dev/pytest scikit-learn/scikit-learn sphinx-doc/sphinx sympy/sympy; do
  n=$(echo $r | tr / __); [ -d "$n.git" ] || git clone -q --bare https://github.com/$r.git $n.git && echo "$(date '+%T') cloned $r $(du -sh $n.git | cut -f1)"
done
echo DONE
