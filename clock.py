# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 21:50:13 2019

@author: klian
"""

from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour=1)
def scheduled_job1():
	print('This job is run everyday at 1am UTC (9am SGT).')
	subprocess.run(['python', 'scrape_from_rss.py'])

# @sched.scheduled_job('cron', hour=7)
# def scheduled_job2():
# 	print('This job is run everyday at 7am UTC (3pm SGT).')
# 	subprocess.run(['python', 'scrape_from_rss.py'])
	
@sched.scheduled_job('cron', hour=13)
def scheduled_job3():
	print('This job is run everyday at 1pm UTC (9pm SGT).')
	subprocess.run(['python', 'scrape_from_rss.py'])
	
# @sched.scheduled_job('cron', hour=19)
# def scheduled_job4():
# 	print('This job is run everyday at 7pm UTC (3am SGT).')
# 	subprocess.run(['python', 'scrape_from_rss.py'])

sched.start()