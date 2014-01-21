the-law-factory-parser
======================

Data generator for the-law-factory project

## Generate data for one bill ##

- search for the [bill procedure page on senat.fr](http://www.senat.fr/dossiers-legislatifs/index-general-projets-propositions-de-lois.html)

- execute *generate data* script using the procedure page :

`bash generate_data_from_senat_url.sh <url>`

The data are generated in the "*data*" directory.

For example, to generate data about the "*Enseignement supérieur et recherche*" bill:

```
bash generate_data_from_senat_url.sh http://www.senat.fr/dossier-legislatif/pjl12-614.html
ls data/pjl12-614/
```

### Dependencies ###

A few perl and python dependencies are required. You can install them with the following:

 ```bash
 sudo apt-get install recode libwww-mechanize-perl
 sudo pip install -r requirements.txt
 ```

