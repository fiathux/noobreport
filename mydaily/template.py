# -*- coding: utf-8 -*-

import time
from mydaily.conf import Conf

def tNoteReport(objs,cts,mts):
    tmstr=\
"""
# 工作项目报告

    从 %(cts)s 到 %(mts)s

%(name)s, %(company)s

项目数: %(count)d

%(list)s

---------

## 详情记录

%(detail)s
"""
    datarec = {
            "name":Conf.dft.user,
            "company":Conf.dft.company,
            "cts":time.strftime("%Y-%m-%d",time.localtime(cts)),
            "mts":time.strftime("%Y-%m-%d",time.localtime(mts)),
            "count":len(objs),
            }
    datarec["list"] = "\n".join(["- %s (经历%d天，更新 %s)" % (
        i["title"],
        int((i["ctime"] - i["mtime"])/86400) + 1,
        time.strftime("%Y-%m-%d",time.localtime(i["mtime"]))
        ) for i in objs])
    datarec["detail"] = "\n\n---------\n\n".join([
"""### %s

    记录时间：%s
    最后更新：%s
    记录域：%s

%s""" % (
    i["title"],
    time.strftime("%Y-%m-%d",time.localtime(i["ctime"])),
    time.strftime("%Y-%m-%d",time.localtime(i["mtime"])),
    i["domain"],
    "\n".join(map(lambda s: "###" + s if s and s[0] == "#" else s,
        (i["content"].strip().split("\n"))[1:])),
    ) for i in objs])
    return tmstr % datarec
