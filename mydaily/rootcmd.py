# -*- coding: utf-8 -*-

import os
import os.path
from mydaily import cmdengine as cmdeg
from mydaily import dailydb

class cmdErr(cmdeg.ExcCMDError):
    def __init__(me,msg):
        me.message = msg

class cmdApp(cmdeg.AppInstance):
    def init(me):
        userhome = os.getenv("HOME")
        me["DB"] = dailydb.dailyDB(os.path.join(userhome,".mydaily.db"))
        me["TMP"] = os.path.join(userhome,".local/tmp/mydaily")
        me["domain"] = "main"
        if not os.path.exists(me["TMP"]):
            os.makedirs(me["TMP"])

@cmdeg.pathNew
class rootCMD(cmdeg.ArgPath):
    _NOTE = "My daily log commit"
    def init(me):pass
    def checkOption(me):pass

@rootCMD.path("help","h")
@cmdeg.pathNew
class cmdHelp(cmdeg.ArgPath):
    _NOTE = "Show help content"
    def init(me):pass
    def finalCmd(me,param):
        me.app.poppath()
        if param and param[0] in me._parent._SUBCMD:
            me.app.path(param[0])
            return me._parent._SUBCMD[param[0]](me.app,[],me._parent).showHelp()
        return me._parent.showHelp()

