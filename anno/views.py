#coding=utf8

from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse
import datetime
from Utils.SearchResultHub import SearchResultHub
from Utils import LogParser
from Utils import AnnoLogParser
from Utils import SessionAnnoLogParser
from Utils import OutcomeLogParser
from Utils import TimeEstLogParser

from Utils import QuerySatisfactionLogParser
from Utils.LogHub import LogHub
from django.template import loader
from django import template
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, models
import random

import sys
import urllib
from anno.models import Task
from anno.models import Setting
from copy import deepcopy
reload(sys)

def search(request,taskid,satisfaction,temporal,query,pageid):
    # print 'view search', query
    srh = SearchResultHub()
    query = urllib.unquote(query)
   # query = query.decode('cp936','ignore').decode('utf8')

    # print urllib.quote(query)
    results = srh.getResult(query, 10*(int(pageid)-1), 10)
    print type(results)
    man_results= list()
    if satisfaction=='SAT':
        for i in range(0,10,1):
            man_results.append(results[i])
    if satisfaction=='MIDSAT':
        for i in range(0,5,1):
            man_results.append(results[4-i])
        for i in range(5,10,1):
            man_results.append(results[i])
    if satisfaction =='UNSAT':
        for i in range(0,10,1):
            man_results.append(results[9-i])
    results_count = srh.getCount(query)
    print man_results
    max_pageid = results_count / 10
    if temporal=='HIGH':
        t = template.Template(open('templates/outexplicit.html').read())
    if temporal == 'LOW':
        t = template.Template(open('templates/outimplicit.html').read())
    next_pageid = ''
    if int(pageid) < max_pageid:
        next_pageid = str(int(pageid)+1)
    page_str = ''.join([str(x) for x in range(1, max_pageid+1)])
    c = template.Context({'resultlist': [r.content for r in man_results],
                          'taskid': taskid,
                          'query': query,
                          'pageid': pageid,
                          'page_str': page_str,
                          'next_pageid': next_pageid,
                          'satisfaction':satisfaction,
                          'temporal':temporal})
    # fout = open('temp/test.html','w')
    # fout.write(t.render(c).decode('utf8','ignore').encode('utf8'))
    # fout.close()
    return HttpResponse(t.render(c))

def login(request):
    class tempt:
        def __init__(self,_idx,_t):
            idx = _idx
            temporal = _t

    settings = set()
    for t in Setting.objects.all():
        settings.add((t.idx,t.temporal))
    allsettings = set()
    for s in settings:
        allsettings.add((s[0],s[1]))
        print s[0],s[1]
    html = template.Template(open('templates/login.html').read())
    c = template.Context({'allsettings':allsettings})
    respon = HttpResponse(html.render(c))
    return HttpResponse(respon)

def tasks(request, sID,settingId):
    settings = Setting.objects.filter(idx=int(settingId))
    tlist = list()
     # tlist = (taskid, query,audiofile,option,temporal)
    for s in settings:
        _listitem = [0,'','','','','']
        temporal = s.temporal
        option= s.option
        taskidx = s.taskidx
        query = Task.objects.get(task_id = taskidx).init_query
        audiofile = Task.objects.get(task_id = taskidx).audiofilename

        if option=='HIDDEN':
            continue
        else:
            _listitem[3]= option
            _listitem[0] = taskidx
            _listitem[1] = query
            _listitem[2] = audiofile
            _listitem[4] = temporal
            tlist.append(_listitem)
    if sID == '0123456789':
        tlist = [Task.objects.get(task_id=13)]
    random.seed(int(sID))
    random.shuffle(tlist)
    print 'len tlist', len(tlist)

    html = template.Template(open('templates/tasks.html').read())

    c = template.Context({'tasks':tlist,'tasknum':len(tlist)})

    respon = HttpResponse(html.render(c))

    respon.set_cookie('studentID', value=sID, max_age=None, expires=None, path='/', domain=None, secure=None)

    return respon

def annolist(request, taskid):
    try:
        studentID = request.COOKIES['studentID']
    except:
        return HttpResponse('ERROR: UNKNOWN STUDENT ID')
    lh = LogHub()
    queries = lh.getQueriesWithSIDandTaskID(studentID,int(taskid))
    html = template.Template(open('templates/annolist.html').read())
    c = template.Context({'querynum': len(queries), 'taskid': taskid, 'querylist': queries})
    return HttpResponse(html.render(c))


def annotation(request, taskid):
    try:
        studentID = request.COOKIES['studentID']
    except:
        return HttpResponse('ERROR: UNKNOWN STUDENT ID')
    lh = LogHub()

    results = lh.getClickedResults(studentID, int(taskid))
    print 'len result for annotation:', len(results)

    t = template.Template(open('templates/annotation.html').read())
    c = template.Context({'resultlist': [r.content for r in results],
                          'taskid': taskid})
    return HttpResponse(t.render(c))


def questionnaire(request, task_id):
    task = Task.objects.get(task_id=int(task_id))
    t = template.Template(open('templates/questionnaire.html').read())
    c = template.Context({'task': task})
    return HttpResponse(t.render(c))


def description(request, task_id, init_query):
    task = Task.objects.get(task_id=int(task_id))
    t = template.Template(open('templates/description.html').read())
    c = template.Context({'task': task, 'initQuery': init_query})
    return HttpResponse(t.render(c))


def taskreview(request,taskid):
    try:
        studentID = request.COOKIES['studentID']
    except:
        return HttpResponse('ERROR: UNKNOWN STUDENT ID')
    lh = LogHub()
    currTask = Task.objects.get(task_id =int(taskid))
    query = currTask.init_query
    question = currTask.question
    results = lh.getClickedResults(studentID, taskid)
    # print 'len result:', len(results)
    t = template.Template(open('templates/taskreview.html').read())
    c = template.Context({'resultlist': [r.content for r in results],
                          'taskid': taskid,
                          'query': query,
                          'question':question})
    return HttpResponse(t.render(c))
@csrf_exempt
def log(request):
    message = urllib.unquote(request.POST[u'message']).encode('utf8')
    # print message
    # print type(message)
    LogParser.insertMessageToDB(message)
    return HttpResponse('OK')


@csrf_exempt
def log_annotation(request):
    message = urllib.unquote(request.POST[u'message'])
    # print message
    AnnoLogParser.insertMessageToDB(message)
    return HttpResponse('OK')


@csrf_exempt
def log_session_annotation(request):
    message = urllib.unquote(request.POST[u'message'])
    # print message
    SessionAnnoLogParser.insertMessageToDB(message)
    return HttpResponse('OK')


@csrf_exempt
def log_outcome(request):
    message = urllib.unquote(request.POST[u'message'])
    # print message
    OutcomeLogParser.insertMessageToDB(message)
    return HttpResponse('OK')

@csrf_exempt
def log_query_satisfaction(request):
    message = urllib.unquote(request.POST[u'message'])
    # print message
    QuerySatisfactionLogParser.insertMessageToDB(message)
    return HttpResponse('OK')

@csrf_exempt
def log_timeest(request):

    message = urllib.unquote(request.POST[u'message'])
    TimeEstLogParser.insertMessageToDB(message)
    return HttpResponse('OK')