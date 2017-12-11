# -*- coding: utf-8 -*-

import os
import os.path
from mydaily import cmdengine as cmdeg
from mydaily import dailydb
from mydaily.conf import Conf
from mydaily.conf import saveConf

class cmdErr(cmdeg.ExcCMDError):
    def __init__(me,msg):
        me.message = msg

class cmdApp(cmdeg.AppInstance):
    def init(me):
        me["DB"] = dailydb.dailyDB(Conf.path.db)
        me["TMP"] = Conf.path.tmp
        me["domain"] = Conf.dft.domain
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

@rootCMD.path("chdomain","cd")
@cmdeg.pathNew
class cmdDomain(cmdeg.ArgPath):
    _NOTE = "Change default domain"
    _MAXTARGET = 1
    def init(me):pass
    def finalCmd(me,param):
        if not param:
            return "No target!\ncurrent domain is [%s]\n" % Conf.dft.domain
        Conf.dft["domain"] = param[0]
        saveConf(Conf)
        return "\n"

@rootCMD.path("chname","cn")
@cmdeg.pathNew
class cmdDomain(cmdeg.ArgPath):
    _NOTE = "Change your name"
    _MAXTARGET = 1
    def init(me):pass
    def finalCmd(me,param):
        if not param:
            return "No target!\ncurrent name is [%s]\n" % Conf.dft.user
        Conf.dft["user"] = param[0]
        saveConf(Conf)
        return "\n"

@rootCMD.path("chcompany","cco")
@cmdeg.pathNew
class cmdDomain(cmdeg.ArgPath):
    _NOTE = "Change your company"
    _MAXTARGET = 1
    def init(me):pass
    def finalCmd(me,param):
        if not param:
            return "No target!\ncurrent company is [%s]\n" % Conf.dft.company
        Conf.dft["company"] = param[0]
        saveConf(Conf)
        return "\n"

