the-law-factory-parser
======================

Data generator for [the-law-factory project](https://github.com/RegardsCitoyens/the-law-factory) (http://www.LaFabriqueDeLaLoi.fr)

Code used to generate the API avaialble at: http://www.LaFabriqueDeLaLoi.fr/api/


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
 sudo apt-get install python-pip
 sudo apt-get install python-bs4
 sudo pip install -r requirements.txt
 ```

##Generate git version for a bill

Once the bill is published on *http://www.LaFabriqueDeLaLoi.fr/api/*, you can generate a git repository of it. The git is published on a gitlab instance.

The scripts need to be executed on the machine that hosts the gitlab instance.

###Check the configuration

The configuration file used is *scripts/gitlaw/config.inc*.

It contains :

- **GITPASSWD** : the password for the admin user of our gitlab (same password for the 4 users assemblee, senat, CMP, gouvernement)
- **GITLAB** : the path to gitlab API controler (ie: ~gitlab/python-gitlab/gitlab)
- **MYSQL_USER** : the mysql user used by gitlab
- **MYSQL_PASS** : the mysql pass used by gitlab

###Generate the git repository

The following script generate git repository for a given law id :

    bash scripts/gitlaw/git.sh <LAW_ID>

It creates a gitlab repository, generate all the commits for the different steps and publish it on gitlab.

It uses *data/LAW_ID* as a working directory.

###Change dates on gitlab interface

*script/gitlaw/postgit.sh* changes the date on the gitlab interface to use the parliament ones instead of the pushed one.

To execute it :

    bash scripts/gitlaw/postgit.sh <LAW_ID>

It uses the data contained into *data/LAW_ID*.
