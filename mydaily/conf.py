# -*- coding: utf-8 -*-

import os
from mydaily import qconfig

__userhome = os.getenv("HOME")
DFT_CONFFILE = os.path.join(__userhome,".mydaily.conf")
def loadDefault():
    cfg = qconfig.confFactory(str='''
dft {
    domain = main
    user = %s
    company = For private
}
path {
    db = %s
    tmp = %s
}
    ''' % (
        os.getlogin() or "Your Name",
        os.path.join(__userhome,".mydaily.db"),
        os.path.join(__userhome,".local/tmp/mydaily"
            )))
    open(DFT_CONFFILE,"wb+").write(str(cfg).encode("utf-8"))
    return cfg

def loadConf():
    return qconfig.confFactory(file=DFT_CONFFILE) if os.path.exists(DFT_CONFFILE) else\
        loadDefault()

def saveConf(obj):
    open(DFT_CONFFILE,"wb+").write(str(obj).encode("utf-8"))

Conf = loadConf()
