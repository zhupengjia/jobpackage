#!/usr/bin/env python
import os,sys,random,math,time
import xml.etree.ElementTree as ET
from xml.dom import minidom

class jobcreate:
    def __init__(self):
	self.identifyhost()
	self.checkjobdir()
    
    def identifyhost(self):
	pc=os.popen("uname -n").read().strip()
	if any([x in pc for x in ["ifarm","vvoo55","dmep"]]):
	    self.host=1
	    self.jobdir="/w/halla-sfs62/g2p/pzhu/jobs"
	elif "ui0" in pc:
	    self.host=2
	    self.jobdir="/moose/JLabUser/pzhu/jobs"
	else:
	    self.host=0
	    print "err!! not usable host"
	    sys.exit()
	    
    def checkjobdir(self):
	self.scriptdir=os.path.join(self.jobdir,"scripts")
	self.exedir=os.path.join(self.jobdir,"jobs")
	self.outdir=os.path.join(self.jobdir,"outs")
	self.errdir=os.path.join(self.jobdir,"errs")
	self.logdir=os.path.join(self.jobdir,"log")
	
	for d in (self.jobdir,self.exedir,self.outdir,self.errdir,self.scriptdir):
	    if not os.path.exists(d):
		os.makedirs(d)
		
    def createjob(self,cmd,args=[],inputfiles=[],outputfiles=[],addcmdpre=[],addcmdafter=[],test=False,flucspace=False):
	args=[str(x) for x in args]
	if cmd[0]=="." or cmd[0]=="/":
	    cmdfile=os.path.abspath(cmd)
	    cmddir,cmdfilen=os.path.split(cmdfile)
	    globalcmd=False
	else:
	    #for command 
	    cmd=cmd.split(" ")
	    cmdfilen=cmd[0]
	    globalcmd=True
	    if len(cmd)>1:
		args=[" ".join(cmd[1:])]+args
	    cmd=cmd[0]
	randomid=int(random.random()*1000000)
	savefilen=cmdfilen+"_"+str(randomid)
	jobfilen1=os.path.join(self.exedir,"%s.job"%savefilen)
	jobfilen2=os.path.join(self.scriptdir,"%s.job.sh"%savefilen)
	outfilen=os.path.join(self.outdir,"%s.out"%savefilen)
	errfilen=os.path.join(self.errdir,"%s.err"%savefilen)
	logfilen=os.path.join(self.logdir,"%s.log"%savefilen)
	if self.host==1:
	    diskspace=os.getenv("DISK_SPACE")
	    memory=os.getenv("MEMORY")
	    if diskspace=="None":diskspace=1000
	    else:diskspace=int(diskspace)
	    if memory=="None":memory=2000
	    else:memory=int(memory)
	    lenargs=len(args)
	    if lenargs<1:
		args=[""]
		lenargs=1
	    Request=ET.Element('Request')
	    Project=ET.SubElement(Request,'Project')
	    Project.set("name","g2p")
	    Name=ET.SubElement(Request,'Name')
	    Name.set("name","%s"%savefilen)
	    Memory=ET.SubElement(Request,'Memory')
	    Memory.set("space","%i"%memory)
	    Memory.set("unit","MB")
	    OS=ET.SubElement(Request,'OS')
	    OS.set("name","centos62")
	    Track=ET.SubElement(Request,'Track')
	    if test:Track.set("name","debug")
	    else:Track.set("name","analysis")
	    if not flucspace:
		DiskSpace=ET.SubElement(Request,'DiskSpace')
		DiskSpace.set("space","%i"%diskspace)
		DiskSpace.set("unit","MB")
	    else:DiskSpace=[]
	    Job,Command,Input=[],[],[]
	    for iargs in range(lenargs):
		jobfilen22=jobfilen2+"_"+args[iargs]
		jobfile2=open(jobfilen22,"w")
		savefilen1=savefilen+args[iargs]
		print>>jobfile2,"#!/bin/bash"
		print>>jobfile2,"source /home/pzhu/.bashrc"
		print>>jobfile2,":>%s.out"%savefilen1
		print>>jobfile2,"exec &>%s.out"%savefilen1
		print>>jobfile2,"uname -a"
		if len(addcmdpre)<1:
		    if not globalcmd:
			print>>jobfile2,"cp %s ."%cmdfile
		else:
		    for c in addcmdpre:
			print>>jobfile2,c.replace("$ARG$",args[iargs])
		print>>jobfile2,"ls -la *"
		print>>jobfile2,"echo",cmd,args[iargs]
		print>>jobfile2,cmd,args[iargs]
		if len(addcmdafter)<1:
		    print>>jobfile2,"cp -r * %s"%cmddir
		else:
		    for c in addcmdafter:
			print>>jobfile2,c.replace("$ARG$",args[iargs])
		print>>jobfile2,"cp *.out %s"%self.outdir
		jobfile2.close()
		os.system("chmod +x %s"%jobfilen22)
	    
		Job.append(ET.SubElement(Request,'Job'))
		Command.append(ET.SubElement(Job[-1],'Command'))
		Command[iargs].text=jobfilen22
		if flucspace:
		    totsize=0
		    for f in inputfiles[iargs]:
			totsize+=os.path.getsize(f)
		    totsize=float(totsize)/1e6*1.2+diskspace
		    DiskSpace.append(ET.SubElement(Job[-1],'DiskSpace'))
		    DiskSpace[-1].set("space","%i"%totsize)
		    DiskSpace[-1].set("unit","MB")
		Input.append([])
		for f in inputfiles[iargs]:
		    Input[-1].append(ET.SubElement(Job[-1],'Input'))
		    if "/mss/" in f:f="mss:"+f
		    else:f="file:"+f
		    Input[-1][-1].set("src",f)
		    Input[-1][-1].set("dest",os.path.split(f)[-1])
		#if test:break
	    with open(jobfilen1,"wb") as jobfile:
		jobfile.write(minidom.parseString(ET.tostring(Request)).toprettyxml())
	    os.system("jsub -xml %s"%jobfilen1)
	    
	elif self.host==2:
            Nsubonce=os.getenv("NSUBONCE")
            subinterval=os.getenv("JOBINTERVAL")
            if Nsubonce==None:Nsubonce=100
            else: Nsubonce=int(Nsubonce)
            if subinterval==None:subinterval=600
            else:subinterval=int(subinterval)
	    with open(jobfilen2,"w") as jobfile2:
		print>>jobfile2,"#!/bin/bash"
		print>>jobfile2,"source /home/pzhu/.bashrc"
		print>>jobfile2,"uname -a"
		print>>jobfile2,"%s $@"%cmd
		print>>jobfile2,"ls -la *"
	    os.system("chmod +x %s"%jobfilen2)
            Njobs=0
            while True:
                jobfilen11=jobfilen1+"_%i"%Njobs
                with open(jobfilen11,"w") as jobfile: 
                    print>>jobfile,"Executable=%s"%jobfilen2
                    if len(args)<1:
                        print>>jobfile,"queue"
                        Njobs+=1
                    else:
                        print>>jobfile,""
                        for i in range(Njobs,Njobs+Nsubonce):
                            if i>=len(args):break
                            print>>jobfile,"Arguments=%s"%args[i]
                            print>>jobfile,"output=%s_%s"%(outfilen,args[i])
                            print>>jobfile,"Error=%s_%s"%(errfilen,args[i])
                            #print>>jobfile,"Log=%s_%s"%(logfilen,args[i])
                            print>>jobfile,"queue"
                os.system("condor_submit %s"%jobfilen11)
                Njobs+=Nsubonce
                if Njobs>=len(args):break
                time.sleep(subinterval)
	
if __name__=="__main__":
    j=jobcreate()
