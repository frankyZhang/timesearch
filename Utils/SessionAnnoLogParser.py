#coding=utf8
__author__ = 'defaultstr'
from anno.models import *
from django.db import transaction, models
import re


patterns = {key: re.compile('%s=(.*?)\\t' % key) for key in ['TIMESTAMP', 'USER', 'TASK', 'ACTION']}
info_patterns = re.compile('INFO:\\t(.*?)$')
anno_info_patterns = {}
anno_info_patterns['score'] = re.compile('score=(.*?)$')


def fromString(line):
    studentID = patterns['USER'].search(line).group(1)
    task_id = patterns['TASK'].search(line).group(1)
    info = info_patterns.search(line).group(1)
    score = int(anno_info_patterns['score'].search(info).group(1))
    anno_log_obj = SessionAnnotation.objects.create(studentID=studentID,
                                task_id=task_id,
                                score=score,
                                content=line)
    print anno_log_obj
    return anno_log_obj


@transaction.commit_manually
def insertMessageToDB(message):
    try:
        for line in message.split('\n'):
            print line
            if line == '':
                continue
            log = fromString(line)
            log.save()
    except:
        transaction.rollback()
    else:
        print "commit success!"
        transaction.commit()
