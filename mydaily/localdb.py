# -*- coding: utf-8 -*-

# converted page list ORM
# ------------------------
# Droi Shanghai 2016
# Fiathux Su

import sqlite3
import time
import random
import threading
import multiprocessing
import uuid
from collections import namedtuple
from functools import reduce

#Table join ID{{{
def TabIDGen():
    i = 0
    while True:
        yield "T%06x" % i
        i = (i < 16777215 and (i + 1)) or 0
TABIDGEN = TabIDGen()
def TabJoinID():
    return TABIDGEN.__next__()
#}}}

def HOSTAddrCrc8Iter():
    netaddr = uuid.getnode()
    for i in range(0,32):
        yield (netaddr & 1) and 0xE0
        netaddr = netaddr >> 1

HOSTADDR = (lambda hcrc: int((hcrc / 100)) + (hcrc % 100) * 10)(
        reduce(lambda a,b: (a >> 1) ^ b,HOSTAddrCrc8Iter(),0))

class excDBError(Exception): pass

# A query dict with keys list
class queryDict(dict):
    def __init__(me,dictobj=None,dbkeys=None):
        super(dict,me).__init__()
        if dictobj:
            for k,v in dictobj.items():
                me[k]=v
        if dbkeys:
            me.dbkeys = tuple(dbkeys)

# 
def rule2AdditCtrlIter(ruledict,keycheck):
    if not ruledict:
        return
    if "__orderkey" in ruledict:
        orderk = filter(lambda k:k,map(keycheck,ruledict["__orderkey"]))
        if "__ordertype" in ruledict and ruledict["__ordertype"] == "desc":
            ordert = "desc"
        else:
            ordert = "asc"
        yield "order by %s %s" % (",".join(orderk), ordert)
    if "__top" in ruledict:
        toplimit = ruledict["__top"]
        if "__offset" in ruledict:
            topoffset = ruledict["__offset"]
        else:
            topoffset = 0
        yield "limit %d offset %d" %(toplimit,topoffset)

SQLExpression = namedtuple("SQLiKey",["is_null","eq","not_eq","more","less","more_eq",
    "less_eq","is_in","not_in","is_exists","not_exists"])

# generate hash compare expression with specify middle-fix
SQLITE_HASHEXP = lambda s: (lambda k,v:("%s %s (%s)" % \
        (k,s,",".join(map(lambda i: "?",range(0,len(v)))) ),v))
# compare expression for SQLite
SQLITE_EXPRESSION = SQLExpression(
        lambda k,v: ("%s is null" % (k,),[]),  # is null
        lambda k,v: ("%s=?" % (k,),[v]),       # eq
        lambda k,v: ("%s<>?" % (k,),[v]),      # not eq
        lambda k,v: ("%s>?" % (k,),[v]),       # more than
        lambda k,v: ("%s<?" % (k,),[v]),       # less than
        lambda k,v: ("%s>=?" % (k,),[v]),      # more than or eq
        lambda k,v: ("%s<=?" % (k,),[v]),      # less than or eq
        lambda k,v: SQLITE_HASHEXP("in")(k,v),
        lambda k,v: SQLITE_HASHEXP("not in")(k,v),
        lambda k,v: SQLITE_HASHEXP("exists")(k,v),
        lambda k,v: SQLITE_HASHEXP("not exists")(k,v)
        )

# convert condition rule to where statement
def rule2where_with_express(ruledict,keycheck,exp):
    if not ruledict:
        return "",[]
    # join rule items
    def packResult(result,merge = " and "):
        result = list(filter(lambda r: r and r[0],result))
        return (
                merge.join(map(lambda r: r[0],result)),
                reduce(lambda r,last: r + last, map(lambda r: r[1], result),[])
                )
    #process simple rule
    def simprule(keysql,vobj):
        if vobj is None:
            return exp.is_null(keysql,None) #"%s is null" % keysql, []
        else:
            return exp.eq(keysql,vobj) #"%s=?" % keysql, [vobj]
    #process slice rule
    def sliceRule(keysql,sliobj):
        if not sliobj.start and not sliobj.stop:
            raise excDBError("at less one vaild condition must specified in slice")
        sqlsegment = []
        sqlparam = []
        if sliobj.start:
            onesql,oneparam = ((sliobj.step or 0) & 1 and exp.more_eq(keysql,sliobj.start)) or \
                    exp.more(keysql,sliobj.start)
            sqlsegment.append(onesql)
            sqlparam.extend(oneparam)
            #sqlsegment.append("%s%s?" % (keysql,(sliobj.step and ">=") or ">"))
            #sqlparam.append(sliobj.start)
        if sliobj.stop:
            onesql,oneparam = ((sliobj.step or 0) & 2 and exp.more_eq(keysql,sliobj.stop)) or \
                    exp.more(keysql,sliobj.stop)
            sqlsegment.append(onesql)
            sqlparam.extend(oneparam)
            #sqlsegment.append("%s%s?" % (keysql,(sliobj.step and "<=") or "<"))
            #sqlparam.append(sliobj.stop)
        return " and ".join(sqlsegment),sqlparam
    #advance SQL sub-list statement(contain slice and unit)
    def advListRule(listfunc):
        def hiListRule(keysql,key,listobj):
            sli_str,sli_param = packResult(orIter(
                    list(map(lambda v: (key,v), filter(lambda v:type(v) is slice, listobj))) ),
                    " or ")
            li_rst = listfunc(keysql,filter(lambda v:type(v) is not slice, listobj))
            if sli_str:
                if li_rst:
                    return "(%s or %s)" % (sli_str,li_rst[0]), sli_param + li_rst[1]
                else:
                    return sli_str,sli_param
            elif li_rst:
                return li_rst
            else:
                raise excDBError("invalid sub-list")
        return hiListRule
    #original SQL "in" statement
    @advListRule
    def listRule(kesql,listobj):
        if listobj is not list: #convert iterator
            listobj = list(listobj)
        if not listobj:
            return None
        return exp.is_in(kesql,listobj)
        #return "%s in (%s)" % ( kesql, ",".join(map(lambda i: "?",range(0,len(listobj)))) ),listobj
    #make general rule item
    def generalRult(key,val):
        keysql = keycheck(key)
        if not keysql:
            raise KeyError("[%s] is not defined in table" % str(key))
        if type(val) is slice:
            return sliceRule(keysql,val)
        elif type(val) is list:
            if not val:
                return "",[]
            return listRule(keysql,key,val)
        else:
            return simprule(keysql,val)
    # logic "or" iterator
    def orIter(rules):
        for key,val in rules:
            if type(key) is str and key[0:2] == "__":
                continue
            if key is None:
                if val and type(val) is dict:
                    andsql,param = packResult(andIter(val.items()))
                    yield "(%s)" % andsql,param
            else:
                yield generalRult(key,val)
    # logic "and" iterator
    def andIter(rules):
        for key,val in rules:
            if type(key) is str and key[0:2] == "__":
                continue
            if type(key) is tuple and type(val) is tuple: # or rule
                if len(key) != len(val):
                    raise excDBError("not all key-value pairs is matched")
                or_rst = list(orIter([(key[i],val[i]) for i in range(0,len(key))]))
                if or_rst:
                    yield packResult(or_rst," or ")
            else:
                yield generalRult(key,val)
    return packResult(andIter(ruledict.items()))

# where statement with sqlite
def rule2where(ruledict,keycheck):
    return rule2where_with_express(ruledict,keycheck,SQLITE_EXPRESSION)
 
SQLiKey = namedtuple("SQLiKey",["name","type","indexName","availNone","isPrimary"])

class ORMExecList(list):pass

# SQL Executable object
class ORMSQLExec(object):
    # generate where statement condition
    def SQLCondition(me,ruledict,keycheck):
        return rule2where(ruledict,keycheck)

    # generate insert SQL list expression
    def mk_insertcond(me,values):
        return ",".join(map(lambda v:"?",values))

    # generate update SQL list expression
    def mk_updatestatement(me,items):
        values = list(map(lambda itm: itm[1],items))
        keysql = ",".join(map(lambda itm: "\"%s\"=?" % itm[0], items))
        return keysql,values

    def execList(me,execlist):
        return ORMExecList(execlist)

    def __init__(me, dbconnect):
        me._conn = dbconnect
    # execute SQL
    def executSQL(me,sqlist):
        sql = None
        param = None
        result = []
        try:
            with me._conn:
                for sql,params in sqlist:
                    cur = me._conn.cursor()
                    if type(params) is ORMExecList and params:
                        # some parameter groups with one SQL statement
                        for param in params:
                            result.append(cur.execute(sql,param))
                    else:
                        # one parameter list only
                        param = params
                        result.append(cur.execute(sql,param or tuple()))
            return result
        except Exception as e:
            raise excDBError(str(e),sql,param)

# Simple ORM prototype of table object
class simpORMTable(ORMSQLExec):
    KEYS = [
            SQLiKey("sample", "int", None, False, True),
            SQLiKey("smpkey", "text", "idxsamp", False, False),
            SQLiKey("smpunique", "int", "idxsamp_unique", False, False)
            ]
    mKeyLock = threading.Lock()
    mKeyTM = None
    mKeyRnd = None
    mKeyRndCyc = lambda: int(random.random() * 80000000) + HOSTADDR * 10000000

    # Create primary key
    @classmethod
    def mKey(c):
        with c.mKeyLock:
            tm = int(time.time()) % 788400000
            if c.mKeyTM == tm:
                while True:
                    rnd = c.mKeyRndCyc()
                    if rnd not in c.mKeyRnd:
                        c.mKeyRnd.add(rnd)
                        break
            else:
                rnd = c.mKeyRndCyc()
                c.mKeyTM = tm
                c.mKeyRnd = {rnd,}
            return tm * 10000000000 + rnd

    # generate "create table" statement
    @classmethod
    def makeTableSQL(c):
        tabname = c.__name__
        primary = ["\"%s\"" % (k.name,) for k in filter(lambda k:k.isPrimary, c.KEYS)]
        keystr = ",".join(map(lambda k: "\"%s\" %s%s" % \
                (k.name,k.type,(not k.availNone and " not null") or ""),c.KEYS))
        if primary:
            keystr = "%s, primary key (%s)" % (keystr,",".join(primary))
        return "create table if not exists \"%s\" (%s);" % (tabname, keystr)

    # generate all "create index" statements
    @classmethod
    def makeIndexSQLIter(c):
        tabname = c.__name__
        indexedItem = [k for k in filter(lambda k: k.indexName, c.KEYS)]
        indexes = set(map(lambda k: k.indexName, indexedItem))
        for idx in indexes:
            param = ["unique" if idx[-7:] == "_unique" else ""]
            param.append(idx)
            param.append(c.__name__)
            param.append(
                    ",".join(
                        map(lambda k: "\"%s\"" % (k.name,),
                            filter(lambda k:k.indexName == idx,indexedItem) ) ))
            yield "create %s index if not exists \"%s\" on \"%s\" (%s)" % tuple(param)

    def __init__(me, dbconnect, newtable = True):
        me._conn = dbconnect
        me.keys = set(map(lambda k: k.name, me.KEYS))
        if newtable:
            sqlist = [(me.makeTableSQL(),None)] + [(idxsql,None) for idxsql in me.makeIndexSQLIter()]
            me.executSQL(sqlist)

    # convert rule dict to where statement
    def _rule2where(me,ruledict):
        chkkey = lambda k: (k in me.keys and ('"%s"' % k)) or None
        rulestr,param = me.SQLCondition(ruledict,chkkey)
        if rulestr:
            return "where " + rulestr + " " + " ".join(rule2AdditCtrlIter(ruledict,chkkey)),param
        else:
            return " ".join(rule2AdditCtrlIter(ruledict,chkkey)),[]

    # table select
    def __getitem__(me,ruledict):
        def itemiter(query):
            while True:
                qobj = query.fetchone()
                if qobj:
                    yield qobj
                else:
                    break
        if hasattr(ruledict,"dbkeys") and ruledict.dbkeys:
            keys = ",".join(map(lambda k:"\"%s\"" % k, ruledict.dbkeys))
        else:
            keys = "*"
        sqlwhere,param = me._rule2where(ruledict)
        sql = "select %s from \"%s\" %s;" % (keys,type(me).__name__, sqlwhere)
        return itemiter(me.executSQL([(sql,param),])[0])

    # table item insert
    def __setitem__(me,keys,values):
        if not values: return
        if keys:
            for k in keys:
                if k not in me.keys:
                    raise KeyError("[%s] is not defined in table" % k)
            keysql = "(%s)" % ",".join(map(lambda k: "\"%s\"" % k, keys))
        else:
            keysql = ""
        if type(values[0]) is not tuple:
            values = [values]
        insrtexp = me.mk_insertcond(values[0])#",".join(map(lambda v:"?",values[0]))
        sql = "insert into \"%s\" %s values (%s)" % (type(me).__name__, keysql, insrtexp)
        me.executSQL([(sql,me.execList(values)),])

    # table item delete
    def __delitem__(me,ruledict):
        sqlwhere,param = me._rule2where(ruledict)
        sql = "delete from \"%s\" %s;" % (type(me).__name__, sqlwhere)
        me.executSQL([(sql,param),])

    # table query method
    def query(me,*keys,**ruledict):
        return me[queryDict(ruledict,keys)]

    #table insert method
    def insert(me,*values,**addit):
        keys = addit["keys"] if "keys" in addit else None
        me[keys] = values

    # table item count
    def count(me,**ruledict):
        sqlwhere,param = me._rule2where(ruledict)
        sql = "select count(*) from \"%s\" %s;" % (type(me).__name__, sqlwhere)
        return me.executSQL([(sql,param),])[0].fetchone()[0]

    # table item update
    def update(me,*uplist):
        def buildSQLTab(ruledict,changedict):
            ksql,vallist = me.mk_updatestatement(changedict.items())
            sqlwhere,param = me._rule2where(ruledict)
            sql = "update \"%s\" set %s %s;" % (type(me).__name__, ksql, sqlwhere)
            return (sql,vallist + param)
        if len(uplist) == 2 and type(uplist[0]) is dict:
            sqlist = [buildSQLTab(uplist[0],uplist[1])]
        else:
            sqlist = [buildSQLTab(rule,change) for rule,change in uplist]
        me.executSQL(sqlist)

    # make new table instance
    def instance(me):
        return type(me)(me._conn,False)

    # make left/right join
    def __add__(me,joinObj):
        if joinObj is me:
            raise excDBError("self join self must use deffrent table instance. use 'instance()' method to make it")
        return ORMJoinFactory(me,joinObj,"left")

    # make inner join
    def __mul__(me,joinObj):
        if joinObj is me:
            raise excDBError("self join self must use deffrent table instance. use 'instance()' method to make it")
        return ORMJoinFactory(me,joinObj,"inner")

# table join unit
class ORMJoinObject(ORMSQLExec):
    def __init__(me,left,right,mode,keyleft,keyright):
        me.tables = set()
        me.tabname = {}
        me._conn = left._conn
        #check parameter {{{
        if isinstance(left,ORMJoinObject):
            me.tables = me.tables | left.tables
            me.tabname.update(left.tabname)
            me.condition = left.condition
        elif isinstance(left,simpORMTable):
            me.tables.add(left)
            me.tabname[left] = TabJoinID()
            me.condition = left.SQLCondition
        else:
            raise excDBError("Invalid left target to join")
        if isinstance(right,ORMJoinObject):
            if me.tables & right.tables:
                raise excDBError("Repeat join one table object")
            me.tables = me.tables | right.tables
            me.tabname.update(right.tabname)
        elif isinstance(right,simpORMTable):
            if right in me.tables:
                raise excDBError("Repeat join one table object")
            me.tables.add(right)
            me.tabname[right] = TabJoinID()
        else:
            raise excDBError("Invalid right target to join")
        if mode != "inner" and mode != "left":
            raise excDBError("Invalid mode name to join")
        if isinstance(left,simpORMTable) and type(keyleft) is str: keyleft= (left,keyleft)
        if isinstance(right,simpORMTable) and type(keyright) is str: keyright= (right,keyright)
        if keyleft[0] not in me.tables or keyleft[1] not in keyleft[0].keys:
            raise excDBError("Invalid key name to join")
        if keyright[0] not in me.tables or keyright[1] not in keyright[0].keys:
            raise excDBError("Invalid key name to join")
        #}}}
        me.mode = mode
        me.left = left
        me.right = right
        me.keyleft = keyleft
        me.keyright = keyright

    def makeTabID(me,tab):
        return "%s%06x" % (type(tab).__name__, int(random.random() * 16777215))

    # make left/right join
    def __add__(me,joinObj):
        return ORMJoinFactory(me,joinObj,"left")

    # make inner join
    def __mul__(me,joinObj):
        return ORMJoinFactory(me,joinObj,"inner")

    def _rule2where(me,ruledict):
        def mkMtKey(key):
            tab,kname = key
            if tab not in me.tables or kname not in tab.keys:
                return None
            else:
                return "\"%s\".\"%s\"" % (me.tabname[tab],kname)
        rulestr,param = me.condition(ruledict,mkMtKey)
        if rulestr:
            return "where " + rulestr,param
        else:
            return "",[]

    def _mkJoin(me):
        pack = {"mode":me.mode}
        if isinstance(me.left,ORMJoinObject):
            pack["leftid"] = me.left._mkJoin()
        else:
            pack["leftid"] = "\"%s\" as \"%s\"" % (type(me.left).__name__, me.tabname[me.left])
        if isinstance(me.right,ORMJoinObject):
            pack["rightid"] = me.right._mkJoin()
        else:
            pack["rightid"] = "\"%s\" as \"%s\"" % (type(me.right).__name__, me.tabname[me.right])
        pack["ltab"] = me.tabname[me.keyleft[0]]
        pack["lkey"] = me.keyleft[1]
        pack["rtab"] = me.tabname[me.keyright[0]]
        pack["rkey"] = me.keyright[1]
        return "%(leftid)s %(mode)s join %(rightid)s on \"%(ltab)s\".\"%(lkey)s\" = \"%(rtab)s\".\"%(rkey)s\"" % pack

    # do query
    def __getitem__(me,ruledict):
        def itemiter(query):
            while True:
                qobj = query.fetchone()
                if qobj:
                    yield qobj
                else:
                    break
        if hasattr(ruledict,"dbkeys") and ruledict.dbkeys:
            keys = ",".join(map(lambda k:"\"%s\".\"%s\"" % k, ruledict.dbkeys))
        else:
            keys = "*"
        sqlwhere,param = me._rule2where(ruledict)
        sql = "select %s from %s %s;" % (keys,me._mkJoin(), sqlwhere)
        return itemiter(me.executSQL([(sql,param),])[0])
        #return sql

    #
    def query(me,*keys,**ruledict):
        return me[queryDict(ruledict,keys)]

    # count items
    def count(me,**ruledict):
        sqlwhere,param = me._rule2where(ruledict)
        sql = "select count(*) from %s %s;" % (me._mkJoin(), sqlwhere)
        return me.executSQL([(sql,param),])[0].fetchone()[0]
        #return sql

def ORMJoinFactory(left,right,mode):
    def ObjectProto(leftkey,rightkey):
        return ORMJoinObject(left,right,mode,leftkey,rightkey)
    return ObjectProto

# simple Database ORM
class simpORMDB(object):
    TABLES = {}

    @classmethod
    def DBTable(c,table):
        c.TABLES[table.__name__] = table
        return table

    def __init__(me,filename):
        me.inTransection = 0
        me._lock = multiprocessing.Lock()
        me._conn_start = lambda: sqlite3.connect(filename)
        me._conn = None
        with me:
            me._tabdict = {tbname:tbobj(me) for tbname,tbobj in me.TABLES.items()}

    def __getitem__(me,name):
        return me._tabdict[name]

    def cursor(me):
        if me._conn:
            return me._conn.cursor()
        else:
            return me._conn_start().cursor()

    def __enter__(me):
        if not me.inTransection:
            me._lock.acquire()
            me._conn = me._conn_start()
            me._conn.__enter__()
        me.inTransection = me.inTransection + 1
        return me

    def __exit__(me,exc_type, exc_value, traceback):
        if me.inTransection:
            if not exc_value:
                me.inTransection = me.inTransection - 1
            else:
                me.inTransection = 0
            if not me.inTransection:
                me._conn.__exit__(exc_type, exc_value, traceback)
                me._conn = None
                me._lock.release()

def newDBType(dbtype):
    setattr(dbtype,"TABLES",{})
    return dbtype
