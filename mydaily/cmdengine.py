# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import sys

# basic exception 
class ExcCMDError(Exception):pass
# Argument error
class ExcCMDArgs(ExcCMDError):
    def __init__(me,argname):
        me.message = "Invalid argument [%s]" % (argname,)
# Argument error
class ExcCMDArgsUnkonw(ExcCMDError):
    def __init__(me,argname):
        me.message = "Unkonw argument [%s]" % (argname,)
# Argument error
class ExcCMDArgsUnSuff(ExcCMDError):
    def __init__(me,argname):
        me.message = "Unsufficient argument [%s]" % (argname,)
# Excessive arguments error
class ExcCMDArgsExcessive(ExcCMDError):
    def __init__(me,args):
        me.message = "Excessive arguments [%s]" % (", ".join(args),)

# search class inhert tree
def inhertof(cls,pcls):
    if hasattr(cls,"__bases__") and cls.__bases__:
        for i in cls.__bases__:
            if i is pcls:
                return True
            else:
                if inhertof(i,pcls): return True
    return False

# Create unique sub-command
def uniqueCmd(comment):
    def export(call):
        class uniqueCmdSimp(object):
            @staticmethod
            def mkhelp():
                return comment,None,None
            def __call__(me):
                return call()
        return uniqueCmdSimp()
    return export

# Parameter parser
def parseParamRegular(parse,keypos,valpos):
    def export(arg_one):
        p_res = parse(arg_one)
        if p_res:
            return p_res.group(keypos), p_res.group(valpos) if valpos is not None else None
        else:
            return None, None
    return export
# Parameter regular
_PARSE_SIMP_PARAM = parseParamRegular(re.compile("^-[a-zA-Z0-9]+$").match,0,None)
_PARSE_FULL_PARAM = parseParamRegular(
        re.compile("^(--[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*)(=(.*))?$").match,1,4)
_PARSE_SUBCMD = re.compile("^[a-zA-Z0-9][a-zA-Z0-9\\-_]*$").match

# Application instance
class AppInstance(dict):
    def __init__(me):
        super(AppInstance,me).__init__()
        me._pathstack = [sys.argv[0]]
        me.error = False
        me.init()
    # custom initialize
    def init(me):pass
    # Enter sub-command path
    def path(me,path):
        me._pathstack.append(path)
    def poppath(me):
        return me._pathstack.pop()
    # List current sub-command path
    def listpath(me):
        return me._pathstack[:]
    def warn(me,warnmsg):
        sys.stderr.write("WARNING: %s\n" % (warnmsg,))

# New path decorator
def pathNew(c):
    c._SUBCMD = {}
    c._SUBCMDREF = {}
    c._PARAM = {}
    c._PARAMNOTE = {}
    return c

# Command processor prototype
class ArgPath(object):
    _NOTE = "command note"
    _SUBCMD = {}
    _SUBCMDREF = {}
    _PARAM = {}
    _PARAMNOTE = {}
    # Max number of target for operat. effect only at terminal level commmand
    # 0 for None target. 1 for only one target. 2 or more for multi-target
    _MAXTARGET = 2

    def __init__(me,app,argv,parent=None):
        me.app = app    # Application instance refrence
        me._param = {}  # Parsed parameters
        me._subcmd = None   # Parsed sub command
        me._exc = None  # Parse exception (if it was occurs)
        me._parent = parent
        if hasattr(me,"init"):
            me.init()
        try:
            me.scanArgument(argv)
            me.doOption()
            me.checkOption()
        except ExcCMDError as scanExcept:
            me._exc = scanExcept
            me._subcmd = me.showHelp

    # Argument parser {{{
    def scanArgument(me,argv):
        i = 0
        length = len(argv)
        while i < length:
            # Simple parameter
            k,v = _PARSE_SIMP_PARAM(argv[i])
            if k:
                if k in me._PARAM:
                    if me._PARAM[k][0]: #need value
                        i = i + 1
                        if i < length:
                            me._param[k] = argv[i]
                        else:
                            raise ExcCMDArgsUnSuff(k)
                    else:
                        me._param[k] = True
                elif hasattr(me,"finalCmd"):
                    break
                else:
                    raise ExcCMDArgsUnkonw(k)
            else: # Full parameter
                k,v = _PARSE_FULL_PARAM(argv[i])
                if k:
                    if k in me._PARAM:
                        me._param[k] = v
                    elif hasattr(me,"finalCmd"):
                        break
                    else:
                        raise ExcCMDArgsUnkonw(k)
                elif _PARSE_SUBCMD(argv[i]) and argv[i] in me._SUBCMD: # Sub command
                        if inhertof(me._SUBCMD[argv[i]], ArgPath):
                            me.app.path(argv[i]) # append sub-command level
                            me._subcmd = me._SUBCMD[argv[i]](me.app, argv[i+1:], me)
                        else:
                            me._subcmd = me._SUBCMD[argv[i]]
                        return
                else:
                    if not hasattr(me,"finalCmd"):
                        raise ExcCMDArgsUnkonw(argv[i])
                    break
            i = i + 1
        if not me._subcmd:
            if hasattr(me,"finalCmd"):
                if me._MAXTARGET < 2 and len(argv[i:]) > me._MAXTARGET:
                    raise ExcCMDArgsExcessive(argv[i + me._MAXTARGET:])
                me._subcmd = lambda: me.finalCmd(argv[i:])
    #}}}
    
    # Custom initialize method
    def init(me):
        @me.path("help","h")
        @uniqueCmd("Get help text")
        def rootHelp():
            return me.showHelp()

    def checkOption(me):pass

    # Terminal command implament following method for process argument list
    #def finalCmd(me,list):pass

    # inhert for command option
    def doOption(me):
        for pk,pv in me._param.items():
            me._PARAM[pk][1](pv,me.app)

    # inhert for your command action
    def __call__(me):
        if me._exc:
            me.app.error = True
        if me._subcmd:
            try:
                return me._subcmd()
            except ExcCMDError as e:
                return e.message
        return "Specify sub-command or target please. use \"help\" or \"h\" for help.\n"

    # Append option
    @classmethod
    def paramete(c,param,note = None):
        def appendOption(optproc):
            if param[-1] == "=":
                c._PARAM[param[:-1]] = (True, optproc)
                notepname = param[:-1]
            else:
                c._PARAM[param] = (False, optproc)
                notepname = param
            if note: # parameter note for help
                c._PARAMNOTE[optproc] = ([notepname],note)
            elif optproc in c._PARAMNOTE:
                c._PARAMNOTE[optproc][0].append(notepname)
            return optproc
        return appendOption

    # Append sub-command
    @classmethod
    def path(c,*cmd):
        def appendPath(subcmd):
            for i in cmd:
                c._SUBCMD[i] = subcmd
            if subcmd not in c._SUBCMDREF:
                c._SUBCMDREF[subcmd] = [i for i in cmd]
            else:
                c._SUBCMDREF[subcmd].extend(cmd)
            return subcmd
        return appendPath

    # Get help infomation groups
    @classmethod
    def mkhelp(c):
        # help content format: (command note, parameter format, option list)
        parafmt = []
        if c._PARAM:
            parafmt.append("[options]")
        tartgetset = (c._MAXTARGET > 0 and ((c._MAXTARGET > 1 and "list...") or "target")) or ""
        if c._SUBCMD:
            if hasattr(c,"finalCmd"):
                parafmt.append("[sub-command]" + " " + tartgetset)
            else:
                parafmt.append("<sub-command>")
        elif hasattr(c,"finalCmd"):
            parafmt.append(tartgetset)
        return c._NOTE, parafmt, [
                (",".join(paralist), note) for paralist,note in c._PARAMNOTE.values()]

    # Get help string
    def showHelp(me):
        output = []
        if me._exc:
            output.append("ERROR - " + me._exc.message)
            output.append("")
        hcmt, harg, opts = me.mkhelp()
        output.append(
                "\ncommand help %s :" % (" ".join(map(lambda p:"[" + p + "]", me.app.listpath())),) )
        if hcmt: output.append(hcmt)
        output.append("----------------------")
        output.append("")
        if harg:
            output.append(" ".join([" ".join(me.app.listpath()), " ".join(harg)]))
            output.append("")
        # Sub-command help
        if me._SUBCMDREF:
            cmds = [(",".join(cname),cobj) for cobj,cname in me._SUBCMDREF.items()]
            cmds.sort(key=lambda k: k[0])
            output.append("Sub-Command:")
            colwidth = len(max(cmds,key=lambda k: len(k[0]))[0]) + 6
            for k,v in cmds:
                output.append("".join(
                    ["    ",k,"".join([" " for i in range(len(k),colwidth)]),v.mkhelp()[0]]))
            output.append("")
        # Options help
        if opts:
            output.append("Options:")
            colwidth = len(max(opts,key=lambda k: len(k[0]))[0]) + 6
            for k,v in opts:
                output.append("".join(["    ",k,"".join([" " for i in range(len(k),colwidth)]),v]))
            output.append("")
        return "\n".join(output)
