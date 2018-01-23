#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, glob
from common import open_json, print_json


def amendementIsFromGouvernement(amdt):
    return amdt["groupe"] == "Gouvernement"



#######################################################
#######################################################
class BasicComputation(object):
    def computeAmendements(self,amdt):
        print(">>%s"% amdt["amendement"]["id"])
        return
    def computeInterventions(self,interv):
        print("Compute interv")
        return
    def computeText(self,text):
        print("Compute Text")
        return
    def finalize(self):
        print("Finalize")


#######################################################
#######################################################

class CountAmendementComputation(object):
    
    def __init__(self):
        
        #Amendement
        self.countAmdt = 0
        self.countAmdtAdoptes = 0
        self.countAmdtParl = 0
        self.countAmdtParlAdoptes = 0

        ###interv
        self.countNbMots = 0
        self.dicoIntervenants = {}

        ##steps
        self.countAccidentProcedure = 0

        #article_etapes
        self.firstStep = ""
        self.lastStep = ""
        self.dicoArticles = {}
        self.totalArticles = 0
        self.totalArticlesModified = 0
        self.firstStepTextLength = 0
        self.lastStepTextLength = 0

    def computeAmendements(self,amdt):
        self.countAmdt += 1

        #"le Gouvernement" pour l'AN and "Le Gouvernement" for Senat
        if not amendementIsFromGouvernement(amdt):
            self.countAmdtParl += 1
        
        if amdt["sort"] == "adopté":
            self.countAmdtAdoptes += 1
            if not amendementIsFromGouvernement(amdt):
                self.countAmdtParlAdoptes += 1
        

    def computeInterventions(self,interv):
        #total_mots of a dossier is excluding some low valuable sections
        #see the prepare_interventions.py:l173
        #therefore we will have a different count
        self.countNbMots += int(interv["intervention"]["nbmots"])

        ##
        slug = interv["intervention"]["intervenant_slug"]
        if slug in self.dicoIntervenants:
            self.dicoIntervenants[slug]+=1
        else:
            self.dicoIntervenants[slug]=1

        # print "Compute interv"
        return

    def computeText(self,text):
        #print "Compute Text"
        return

    def computeStep(self, step):
        #print "Compute Step"
        if step.get("echec") != None or step.get("echec") == "renvoi en commission":
            self.countAccidentProcedure += 1
        if self.firstStep == "":
            self.firstStep = step["directory"]
        if "directory" in step :
            self.lastStep = step["directory"]

    def computeArticleEtapes(self, artEtape):
        
        for article in artEtape["articles"]:
            art = artEtape["articles"][article]
            artId = art["id"]
            self.dicoArticles[artId]={}
            myArt = self.dicoArticles[artId]
            myArt["firstStep"] = "" 

            for step in art["steps"]:
                if myArt["firstStep"] == "":
                    myArt["firstStep"] = step["directory"]
                    if myArt["firstStep"] != self.firstStep:
                        myArt["modified"] = True;
                    else:
                        myArt["modified"] = False;
                        self.firstStepTextLength += step['length']

                myArt["lastStep"] = step["directory"]

                if step["n_diff"] != 0 :
                    myArt["modified"]= True;

                if step["directory"] == self.lastStep:
                    self.lastStepTextLength += step['length']

        for artId in self.dicoArticles:
            art = self.dicoArticles[artId]
            if art["lastStep"] == self.lastStep:
                self.totalArticles+=1
                if art["modified"]:
                    self.totalArticlesModified+=1
        return


    def finalize(self):
        #print "Number Amendements : %d" % self.countAmdtParl
        #print "Number Amendements Adoptées : %d" % self.countAmdtParlAdoptes
        return





#######################################################
#######################################################

class DossierWalker(object):
    def __init__(self, id, computationClass, sourcedir='data'):
        self.id = id;
        self.computationClass = computationClass
        self.procedurePath = os.path.join(sourcedir, self.id, "procedure")
        self.vizPath = os.path.join(sourcedir, self.id, "viz")

    def step_walker(self,step):
        #Intervention treatment
        if "intervention_directory" in step:
            intervDir = os.path.join(self.procedurePath, 
                step["intervention_directory"])
            if not os.path.exists(intervDir):
                print(">No Intervention Directory ")
                return;

            #interventions = open_json(amdtDir, "amendements.json")
            seance_files = step["intervention_files"]
            for seance_file in seance_files:
                seance = open_json(intervDir, "%s.json"%seance_file)

                for interv in seance["seance"]:
                    self.computationClass.computeInterventions(interv)
        
        #Text Treatment
        if "working_text_directory" in step:
            textDir = os.path.join(self.procedurePath,
                    step["working_text_directory"])
            if not os.path.exists(textDir):
                print("ERROR > no Text directory")
                return;

            text = open_json(textDir, "texte.json")
            
            self.computationClass.computeText(text)

        #Article Etape 
        articleEtape = open_json(self.vizPath, "articles_etapes.json")
        self.computationClass.computeArticleEtapes(articleEtape)
        

####################################################

    def walk(self):
        procedure = open_json(self.vizPath, "procedure.json")

        for step in procedure['steps'] :
           self.step_walker(step)
           self.computationClass.computeStep(step)

        for amdts_file in glob.glob(os.path.join(self.vizPath, 'amendements_*')):
            amendements = open_json(amdts_file)
            for subject in amendements.get('sujets', {}).values():
                for amdt in subject.get('amendements', []):
                    import pudb;pu.db
                    self.computationClass.computeAmendements(amdt)

        self.computationClass.finalize()




    

#######################################################
####################################################
 
#dossiersId = sys.argv[1]
#if not dossiersId:
#    sys.stderr.write('Error, no input directory given')
#    exit(1)



#computation = BasicComputation()
#computation = CountAmendementComputation()

#myWalker = DossierWalker(dossiersId, computation)
#myWalker.walk()
