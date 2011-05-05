#!/usr/bin/env python

import os
import stat
import sys

import ConfigParser

ipfHome = os.environ.get("IPF_HOME")
if ipfHome == None:
    print "IPF_HOME environment variable not set"
    sys.exit(1)

##############################################################################################################

steps = {}

def readSteps():
    config = ConfigParser.ConfigParser()
    config.read(ipfHome+"/etc/ipf.config")

    stepDirsStr = config.get("default","stepDirs")
    if stepDirsStr == "":
        stepDirs = ipfHome+"/step"
    else:
        stepDirs = stepDirsStr.split(",")
        # handle relative directories
        for i in range(0,len(stepDirs)):
            if stepDirs[i][0] != "/":
                stepDirs[i] = ipfHome+"/"+stepDirs[i]

    steps = {}
    for stepDir in stepDirs:
        readStepsFromDirectory(stepDir)

def readStepsFromDirectory(dirPath):
    subDirectories = []
    for fileName in os.listdir(dirPath):
        path = dirPath + "/" + fileName
        mode = os.stat(path)[ST_MODE]
        if stat.S_ISDIR(mode):
            subDirectories.append(path)
            continue
        if stat.S_ISREG(mode):
            if stat.S_IXUSR(mode):
                stepName = getStepName(path)
                if stepName != None:
                    if steps.has(stepName):
                        logger.warn("already found a step named "+stepName+", ignoring executable "+path)
                        continue
                    steps[stepName] = path
            continue
        logger.info("ignoring file "+fileName)
    for directory in subDirectories:
        readStepsFromDirectory(directory)

def getStepName(path):
    # this should be done in a separate process
    (status, output) = commands.getstatusoutput(path+" name")
    if status != 0:
        return None
    return output

##############################################################################################################

class Node(object):
    def __init__(self):
        self.id = None
        self.name = None
        self.args = None
        self.dependsOn = []
        self.complete = False

    def __str__(self):
        nstr = "node "+self.id+"\n"
        nstr = nstr + "  step: "+self.name+"\n"
        nstr = nstr + "  inputs from: "
        for index in range(0,len(self.dependsOn)):
            if index > 0:
                nstr = nstr + ", "
            nstr = nstr + self.dependsOn[index]
        nstr = nstr + "\n"
        return nstr

    def run(self):
        pass

class Workflow(object):
    def __init__(self):
        self.nodes = {}

    def __str__(self):
        wstr = ""
        for id in self.nodes.keys().sort():
            wstr = wstr + str(self.nodes[id])
        return wstr

    def read(self, path):
        """Workflow file has very simple syntax. Each line is one of:
            id: name argname1=argvalue1 argname2=argvalue2
            id1, id2, id3 -> id4
            # comment
          The first line associates an id with a step name.
          The second line says that step id4 takes the outputs of steps id1, id2, and id3 as input.
          Comments start with a #."""
        self.nodes.clear()
        f = open(path,"r")
        lineNumber = 1
        for line in f:
            if line[0] == '#':
                continue
            if line.find(":") != -1:
                node = Node()
                (node.id,node.name,args) = line.split(" :")
                # don't need to parse the arguments
                self.args = ""
                for arg in args:
                    self.args = self.args + " " + arg
                if node.id in self.nodes:
                    logger.warn("")
                self.nodes[node.id] = node
                continue
            if line.find("->") != -1:
                index = line.find("->")
                sources = line[:index].split(", ")
                destinations = line[index+2:].split(", ")
                for destination in destinations:
                    if not destination in self.nodes:
                        raise IpfError("undefined node "+destination+" at line "+str(lineNumber))
                    for source in sources:
                        if not source in self.nodes:
                            raise IpfError("undefined node "+source+" at line "+str(lineNumber))
                        self.nodes[destination].dependsOn.append(source)
                continue
            lineNumber = lineNumber + 1
        f.close()

    def run(self):
        pass


##############################################################################################################

if __name__ == "__main__":
    readSteps()
    for (name,path) in steps:
        print(name+": "+path)
