#!env/python3
# coding: utf-8
try:
    import ipdb
except ImportError:
    pass

import sys


action = sys.argv[1]


if action == "hpo":
    from extratools import hpo
elif action == "panels":
    from extratools import panels
else:
    print("Wrong action, please use \"hpo\" or \"panels\"")





