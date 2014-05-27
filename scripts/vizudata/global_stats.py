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



    def computeStatOverFile(self,file):
        dossiers = open_json("data", file)
        for dossier in dossiers["dossiers"]:
            self.countDossiers += 1
            self.totalAmendement += dossier["total_amendements"]
            self.totalAmendementParl += dossier["total_amendements_parlementaire"]
            self.totalAmendementAdoptes += dossier["total_amendements_adoptes"]
            self.totalAmendementParlAdoptes += dossier["total_amendements_parlementaire_adoptes"]
    
    
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
    




stats = Stats()
stats.computeStatOverFile("dossiers_0_49.json")
stats.computeStatOverFile("dossiers_50_99.json")
stats.computeStatOverFile("dossiers_100_149.json")
stats.computeStatOverFile("dossiers_150_199.json")
stats.computeStatOverFile("dossiers_200_209.json")
stats.printStats()
