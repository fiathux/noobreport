# -*- coding: utf-8 -*-

import sys
from mydaily import rootcmd
from mydaily.cmdengine import ExcCMDError
import mydaily.cmdnote

__all__ = ["conf","rootcmd","cmdnote","cmdengine"]

def main():
    try:
        print(rootcmd.rootCMD(rootcmd.cmdApp(), sys.argv[1:])())
    except ExcCMDError as e:
        print(str(e))
