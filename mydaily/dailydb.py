# -*- coding: utf-8 -*-

from mydaily import localdb

@localdb.newDBType
class dailyDB(localdb.simpORMDB):pass

@dailyDB.DBTable
class daily(localdb.simpORMTable):
    KEYS = [
            localdb.SQLiKey("id", "text", None, False, True),           # daily ID
            localdb.SQLiKey("ctime", "int", "idxdlyts", False, False),  # create timestamp
            localdb.SQLiKey("mtime", "int", None, False, False),        # last modify timestamp
            localdb.SQLiKey("domain", "text", "idxdlysub", False, False),   # daily domain 
            localdb.SQLiKey("title", "text", None, False, False),       # daily title
            localdb.SQLiKey("content", "text", None, False, False)      # daily content
            ]

@dailyDB.DBTable
class plan(localdb.simpORMTable):
    KEYS = [
            localdb.SQLiKey("id", "text", None, False, True),           # plain ID
            localdb.SQLiKey("ctime", "int", "idxplts", False, False),   # create timestamp
            localdb.SQLiKey("mtime", "int", None, False, False),        # last modify timestamp
            localdb.SQLiKey("ptime", "int", "idxplpt", True, False),    # begin execution timestamp
            localdb.SQLiKey("etime", "int", "idxplpt", True, False),    # closed timestamp
            localdb.SQLiKey("dtime", "int", "idxpldl", True, False),    # deathline  timestamp
            localdb.SQLiKey("domain", "text", "idplsub", False, False), # plain domain 
            localdb.SQLiKey("state", "text", "idxpldl", False, False),  # plain state
            localdb.SQLiKey("title", "text", None, False, False),       # plain title
            localdb.SQLiKey("content", "text", None, False, False)      # plain content
            ]

