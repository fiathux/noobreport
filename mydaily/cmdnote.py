# -*- coding: utf-8 -*-

import os
import time
import re
from mydaily.localdb import queryDict
from mydaily.rootcmd import cmdErr
from mydaily.rootcmd import cmdHelp
from mydaily.rootcmd import rootCMD as rcmd
from mydaily import cmdengine as cmdeg
from mydaily.editor import edit
from mydaily.editor import edit

TIME_FMT = lambda ts: time.strftime("%Y-%m-%d %H:%M",time.localtime(ts))

def fileID():
    return "%08x%s" % (int(time.time()),os.urandom(4).hex())

@rcmd.path("note","n")
@cmdeg.pathNew
class noteCMD(cmdeg.ArgPath):
    _NOTE = "manager work note"
    def init(me):pass

noteCMD.path("help","h")(cmdHelp)

@noteCMD.path("add")
@cmdeg.pathNew
class noteCMD_Add(cmdeg.ArgPath):
    _NOTE = "Manager work note"
    _MAXTARGET = 0
    def init(me):
        me.app["ctime"] = int(time.time())
    def finalCmd(me,param):
        now = int(time.time())
        eventid = fileID()
        content = edit(me.app)(eventid,"# note something\n")
        title = content.split("\n")[0]
        me.app["DB"]["daily"][(
            "id","ctime","mtime","domain","title","content")] = (
                    eventid, me.app["ctime"], now,
                    me.app["domain"], title, content
                    )
        return "OK!\n"

@noteCMD_Add.paramete("--t","specify event create time")
def p_noteCMD_Add_time(param, app):
    m_df = lambda s: re.match("^([0-9]{4})-([0-9]{2})-([0-9]{2})$",s) and "%Y-%m-%d"
    m_ds = lambda s: re.match("^(20[0-9]{6})$",s) and "%Y%m%d"
    m_tf = lambda s: re.match("^([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})$",s) and "%Y-%m-%d %H:%M:%S"
    pfmt = m_df(param) or m_ds(param) or m_tf(param) or m_ts(param) or m_tt(param)
    print(pfmt)
    try:
        app["ctime"] = time.mktime(time.strptime(param,pfmt))
    except:
        raise cmdErr("time convert error")

@noteCMD_Add.paramete("--dm","specify a domain. [mian] is default")
def p_noteCMD_domain(param, app):
    app["domain"] = param or "mian"

@noteCMD.path("remove","rm")
@cmdeg.pathNew
class noteCMD_Remove(cmdeg.ArgPath):
    _NOTE = "Remove note"
    
    def init(me):pass
    def finalCmd(me,param):
        if not param: return "nothing to do\n"
        del me.app["DB"]["daily"][{"id":param}]
        return "\n"

@noteCMD.path("change")
@cmdeg.pathNew
class noteCMD_Change(cmdeg.ArgPath):
    _NOTE = "Change note"
    _MAXTARGET = 1
    def init(me):pass
    def finalCmd(me,param):
        if not param: return "nothing to do\n"
        li = list(me.app["DB"]["daily"].query("id","content",**{"id":param[0]}))
        if not li: return "nothing to do\n"
        now = int(time.time())
        obj = li[0]
        content = edit(me.app)(obj[0], obj[1])
        if content == obj[1]: return "no change\n"
        title = content.split("\n")[0]
        me.app["DB"]["daily"].update(({"id":obj[0]},{"title":title,"content":content,"mtime":now}))
        return "OK!\n"

@noteCMD.path("cat")
@cmdeg.pathNew
class noteCMD_Change(cmdeg.ArgPath):
    _NOTE = "Show note content"
    _MAXTARGET = 1
    def init(me):pass
    def finalCmd(me,param):
        if not param: return "nothing to do\n"
        li = list(me.app["DB"]["daily"].query("id", "ctime", "mtime", "content",**{"id":param[0]}))
        if not li: return "no data\n"
        obj = li[0]
        readobj = (obj[0],TIME_FMT(obj[1]),TIME_FMT(obj[2]),obj[3])
        return "FileID: %s\nCreate at: %s and Last modify at: %s\n========\n\n%s" % readobj

@noteCMD.path("list","ls")
@cmdeg.pathNew
class noteCMD_List(cmdeg.ArgPath):
    _NOTE = "List note"
    _MAXTARGET = 0
    def init(me):
        me.app["days"] = 6
        me.app["lstemp"] = lambda eid, ct, mt, dm, tit:\
            "%s %s [%s] - %s" % (eid,TIME_FMT(mt), dm, tit)
    def finalCmd(me,param):
        nowlt = time.localtime(time.time())
        qtime = int(time.mktime((
            nowlt.tm_year, nowlt.tm_mon, nowlt.tm_mday, 
            0,0,0,0,0,0)) - me.app["days"] * 86400)
        li = me.app["DB"]["daily"].query("id","ctime","mtime","domain","title",
                ctime=slice(qtime,None), __orderkey=["ctime"], __ordertype="desc")
        return "\n".join([me.app["lstemp"](*pm) for pm in li])

@noteCMD_List.paramete("--day", "Event closed days")
def p_noteCMD_List_days(param, app):
    app["days"] = (param and int(param)) or 0

@noteCMD_List.paramete("-f")
@noteCMD_List.paramete("--fullid", "Show full event info")
def p_noteCMD_List_days(param, app):
    app["lstemp"] = lambda eid, ct, mt, dm, tit:\
        "%s C: %s M: %s [%s] - %s" % (eid, TIME_FMT(ct), TIME_FMT(mt), dm, tit)
