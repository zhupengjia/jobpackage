#!/usr/bin/env python
modules=["jobcreate"]
for m in modules:
    try:
	exec("from %s import *"%m)
    except Exception as err:
	print "Error!!",err
