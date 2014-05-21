#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from common import open_json, print_json

dossiersId = sys.argv[1]
if not dossiersId:
    sys.stderr.write('Error, no input directory given')
    exit(1)



#######################################################
#######################################################
class BasicComputation(object):
    def computeAmendements(self,amdt):
        print ">>%s"% amdt["amendement"]["id"]
        return
    def computeInterventions(self,interv):
        print "Compute interv"
        return
    def computeText(self,text):
        print "Compute Text"
        return
    def finalize(self):
        print "Finalize"

class CountAmendementComputation(object):
    
    def __init__(self):
        self.countAmdt = 0;
        self.countAmdtAdoptes = 0;


    def computeAmendements(self,amdt):
        #print ">>>>>>>>>>>>>>>>>%s"% amdt["amendement"]["id"]
        self.countAmdt = self.countAmdt + 1

        print amdt["amendement"]["sort"] 
        if amdt["amendement"]["sort"] == u"Adopté":
        #if amdt["amendement"]["sort"] == u"Tombe":
            self.countAmdtAdoptes = self.countAmdtAdoptes +1
        

    def computeInterventions(self,interv):
        # print "Compute interv"
        return
    def computeText(self,text):
        #print "Compute Text"
        return

    def finalize(self):
        print "Number Amendements : %d" % self.countAmdt
        print "Number Amendements Adoptées : %d" % self.countAmdtAdoptes





#######################################################
#######################################################

class  DossierWalker(object):

    def __init__(self, id, computationClass):
        self.id = id;
        self.computationClass = computationClass
        self.procedurePath = os.path.join("data",self.id, "procedure")

    def step_walker(self,step):
        #if "directory" in step:
        #    print step["directory"]

        #Amendement treatment    
        if "amendement_directory" in step:
            amdtDir = os.path.join(self.procedurePath, 
                step["amendement_directory"])
            if not os.path.exists(amdtDir):
                print "ERROR > No Amendements Directory "
                return;

            amendements = open_json(amdtDir, "amendements.json")
            for amendement in amendements["amendements"]:
                self.computationClass.computeAmendements(amendement)
               # print ">>%s"% amendement["amendement"]["id"]

        #Intervention treatment
        if "intervention_directory" in step:
            intervDir = os.path.join(self.procedurePath, 
                step["intervention_directory"])
            if not os.path.exists(intervDir):
                print ">No Intervention Directory "
                return;

            #interventions = open_json(amdtDir, "amendements.json")
            seance_files = step["intervention_files"]
            for seance_file in seance_files:
                seance = open_json(intervDir, "%s.json"%seance_file)
                self.computationClass.computeInterventions(seance)
        
        #Text Treatment
        if "working_text_directory" in step:
            textDir = os.path.join(self.procedurePath,
                    step["working_text_directory"])
            if not os.path.exists(textDir):
                print "ERROR > no Text directory"
                return;

            text = open_json(textDir, "texte.json")
            
            self.computationClass.computeText(text)

####################################################

    def walk(self):
        print "WALKER %s"% self.procedurePath
        procedure = open_json(self.procedurePath, "procedure.json")

        for step in procedure['steps'] :
           self.step_walker(step)

        self.computationClass.finalize()




    

#######################################################
####################################################
 

#computation = BasicComputation()
computation = CountAmendementComputation()

myWalker = DossierWalker(dossiersId, computation)
myWalker.walk()
