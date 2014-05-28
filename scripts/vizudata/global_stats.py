#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from common import open_json, print_json


class Stats(object):

    def __init__(self):
        self.countDossiers = 0
        self.countDossiersAmende = 0


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

        self.textSizeOrig = 0
        self.textSizeFinal = 0
        self.countTextWithDoubledVolume = 0
        self.countTextWithDoubledVolume2 = 0
        self.countTextReduced = 0
        self.countTextReduced2 = 0

        self.countModifSup50 = 0
        self.countInflaSup50 = 0
        self.countInflaSup100 = 0

        self.textValues = {}



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

            ##
            self.textSizeOrig += dossier["input_text_length2"]
            self.textSizeFinal += dossier["output_text_length2"]
            #if (float(dossier["output_text_length"])/dossier["input_text_length"]) > 2.0:
            #    self.countTextWithDoubledVolume +=1
            if dossier["output_text_length"] < dossier["input_text_length"]:
                self.countTextReduced +=1

            if (float(dossier["output_text_length2"])/dossier["input_text_length2"]) > 2.0:
                self.countTextWithDoubledVolume2 +=1
            if dossier["output_text_length2"] < dossier["input_text_length2"]:
                self.countTextReduced2 +=1

            if dossier["total_amendements"] >0:
                self.countDossiersAmende += 1

                if dossier["ratio_texte_modif"] >= 0.5:
                    self.countModifSup50 += 1
                if (dossier["output_text_length2"]-dossier["input_text_length2"])/float(dossier["input_text_length2"]) > 0.5 :
                    self.countInflaSup50 += 1
                if (dossier["output_text_length2"]-dossier["input_text_length2"])/float(dossier["input_text_length2"]) > 1 :
                    self.countInflaSup100 += 1



            ##############################################
            self.textValues[dossier["id"]] = {}
            self.textValues[dossier["id"]]["inflation"] = (dossier["output_text_length2"]-dossier["input_text_length2"])/float(dossier["input_text_length2"])
            self.textValues[dossier["id"]]["modification"] = dossier["ratio_texte_modif"]
            self.textValues[dossier["id"]]["amendement"] = dossier["total_amendements"]
            self.textValues[dossier["id"]]["short_title"] = dossier["short_title"]


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
        #print "Nombre d'articles : %d " % self.totalArticles
        #print "Nombre d'articles modifies : %d " % self.totalArticlesModified
        #print "Pourcentage d'articles de loi modifiés dans la procédure : %f " %(float(self.totalArticlesModified)/self.totalArticles)


        print "Nb moyen jour de procedure avant promul : %f" %(float(self.totalDays)/self.countDossiers)

        print "======================================================"
        print "total accident procedure : %d" % self.totalAccidentProcedure
        print "Nb moyen accident procedure : %f" % (float(self.totalAccidentProcedure)/self.countDossiers)
        print "nombre dossier avec accident procedure : %d" % self.nbDossiersAccidentProcedure
        print "Proba dossier avec accident procedure : %f" % (float(self.nbDossiersAccidentProcedure)/self.countDossiers)


        print "======================================================"
        #print "Nb texte ayant double de volume : %d" % self.countTextWithDoubledVolume
        #print "Nb texte ayant reduit de volume : %d" % self.countTextReduced
        print "Nb texte ayant double de volume 2 : %d" % self.countTextWithDoubledVolume2
        print "Nb texte ayant reduit de volume 2 : %d" % self.countTextReduced2
        print "Inflation législative moyenne : %f" % (float(self.textSizeFinal - self.textSizeOrig)/self.textSizeOrig)

        print "======================================================"
        print "Texte ayant plus de 50%% de modification : %f" %(float(self.countModifSup50)/self.countDossiersAmende)
        print "Texte ayant plus de 50%% d'inflation : %f" %(float(self.countInflaSup50)/self.countDossiersAmende)
        print "Texte ayant plus de 100%% d'inflation : %f" %(float(self.countInflaSup100)/self.countDossiersAmende)


        #print self.textValues

    def writeCSV(self):
        f = open("stats.csv", "w")
        for text in self.textValues :
            title = self.textValues[text]["short_title"]
            infla = self.textValues[text]["inflation"]
            modif = self.textValues[text]["modification"]
            amendement = self.textValues[text]["amendement"]

            s = u"%s;%s;%f;%f;%d\n" %(text,title, infla, modif, amendement)
            f.write(s.encode("utf-8"))
        f.close()




stats = Stats()
stats.computeStatOverFile("dossiers_0_49.json")
stats.computeStatOverFile("dossiers_50_99.json")
stats.computeStatOverFile("dossiers_100_149.json")
stats.computeStatOverFile("dossiers_150_199.json")
stats.computeStatOverFile("dossiers_200_249.json")
stats.computeStatOverFile("dossiers_250_294.json")

stats.printStats()
stats.writeCSV()
