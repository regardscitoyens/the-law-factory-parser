#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from common import open_json, print_json


class Stats(object):
    
    def __init__(self):
        self.countDossiers = 0
        self.totalAmendement = 0
        self.totalAmendementParl = 0
        self.totalAmendementAdoptes = 0
        self.totalAmendementParlAdoptes = 0

        self.totalIntervenant = 0

        self.totalArticles = 0
        self.totalArticlesModified = 0

        self.totalAccidentProcedure = 0
        self.nbDossiersAccidentProcedure = 0

        self.totalDays = 0


    def computeStatOverFile(self,file):
        dossiers = open_json("data", file)
        for dossier in dossiers["dossiers"]:
            self.countDossiers += 1

            self.totalDays += dossier["total_days"]

            self.totalAmendement += dossier["total_amendements"]
            self.totalAmendementParl += dossier["total_amendements_parlementaire"]
            self.totalAmendementAdoptes += dossier["total_amendements_adoptes"]
            self.totalAmendementParlAdoptes += dossier["total_amendements_parlementaire_adoptes"]

            self.totalIntervenant += dossier["total_intervenant"]

            self.totalArticles += dossier["total_articles"]
            self.totalArticlesModified += dossier["total_articles_modified"]

            self.totalAccidentProcedure += dossier["total_accident_procedure"]
            if dossier["total_accident_procedure"] > 0: 
                self.nbDossiersAccidentProcedure +=1 

    
    
    def printStats(self):
        print "Total Amendement traites : %d" % (self.totalAmendement)
        print "Nb Amendement Moyen par dossier : %f" %(float(self.totalAmendement)/self.countDossiers)
        print "Nb Amendement Adoptes Moyen par dossier : %f" %(float(self.totalAmendementAdoptes)/self.countDossiers)
        print "Nb Amendement Parlementaires Moyen par dossier : %f" %(float(self.totalAmendementParl)/self.countDossiers)
        print "Nb Amendement Parlementaires Adoptes Moyen par dossier : %f" %(float(self.totalAmendementParlAdoptes)/self.countDossiers)
        print "Reussite des amendements Parl : %f" % (float(self.totalAmendementParlAdoptes)/float(self.totalAmendementParl))
        print "Nb Amendement du gouv Moyen par dossier : %f" %(float(self.totalAmendement - self.totalAmendementParl)/self.countDossiers)
        print "Nb Amendement du gouv Adoptes Moyen par dossier : %f" %(float(self.totalAmendementAdoptes - self.totalAmendementParlAdoptes)/self.countDossiers)
        print "Reussite des amendements du gouv : %f" % (float(self.totalAmendementAdoptes - self.totalAmendementParlAdoptes)/(self.totalAmendement - self.totalAmendementParl))
    
        print "======================================================"
        print "Nombre moyen intervenant : %f " %(float(self.totalIntervenant)/self.countDossiers)
        print "Nombre d'articles : %d " % self.totalArticles
        print "Nombre d'articles modifies : %d " % self.totalArticlesModified
        print "Pourcentage d'articles de loi modifiés dans la procédure : %f " %(float(self.totalArticlesModified)/self.totalArticles)


        print "======================================================"
        print "total accident procedure : %d" % self.totalAccidentProcedure
        print "Nb moyen accident procedure : %f" % (float(self.totalAccidentProcedure)/self.countDossiers)
        print "nombre dossier avec accident procedure : %d" % self.nbDossiersAccidentProcedure
        print "Proba dossier avec accident procedure : %f" % (float(self.nbDossiersAccidentProcedure)/self.countDossiers)

        print "Nb moyen jour de procedure avant promul : %f" %(float(self.totalDays)/self.countDossiers)



stats = Stats()
stats.computeStatOverFile("dossiers_0_49.json")
stats.computeStatOverFile("dossiers_50_99.json")
stats.computeStatOverFile("dossiers_100_149.json")
stats.computeStatOverFile("dossiers_150_199.json")
stats.computeStatOverFile("dossiers_200_209.json")
stats.printStats()
