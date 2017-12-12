# -*- coding: utf-8 -*-

import os.path
import subprocess
from mydaily.rootcmd import cmdErr

RDPIPE = {"stdout":subprocess.DEVNULL,"stderr":subprocess.DEVNULL}
TEST_GVIM = lambda :not subprocess.Popen(["which","gvim"],**RDPIPE).wait() and ["gvim","-f"]
TEST_MACVIM = lambda :not subprocess.Popen(["which","mvim"],**RDPIPE).wait() and ["mvim"]
TEST_VIM = lambda :not subprocess.Popen(["which","vim"],**RDPIPE).wait() and ["vim"]
TEST_VI = lambda :not subprocess.Popen(["which","vi"],**RDPIPE).wait() and ["vi"]
TEST_NANO = lambda :not subprocess.Popen(["which","nano"],**RDPIPE).wait() and ["nano"]
EDITOR = TEST_GVIM() or TEST_VIM() or TEST_VI() or TEST_NANO()

def edit(app):
    def pop(objid, original):
        try:
            fname = os.path.join(app["TMP"], objid)
            fp = open(fname, "wb+")
            fp.write(original.encode("utf-8"))
            fp.close()
            subprocess.Popen(EDITOR + [fname]).wait()
            rsp = fp = open(fname, "rb").read().decode("utf-8")
            os.unlink(fname)
            return rsp
        except Exception as e:
            raise cmdErr("edit content error - " + repr(e))
    return pop

