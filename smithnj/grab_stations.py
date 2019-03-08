import urllib.request
import json
import dml
import prov.model
import datetime
import uuid

############################################
# grab_stations.py
# Script for collecting CTA L station location
############################################

class grab_stations(dml.Algorithm):
    contributor = 'smithnj'
    reads = []
    writes = ['smithnj.stations']

    @staticmethod
    def execute(trial=False):

        startTime = datetime.datetime.now()

        # ---[ Connect to Database ]---------------------------------
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('smithnj', 'smithnj')
        repo_name = stations.writes[0]

        # ---[ Grab Data ]-------------------------------------------
        url = 'http://datamechanics.io/data/smithnj/CTA_RailStations.json'
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        content = response.read()
        json_response = json.loads(content)
        json_string = json.dumps(json_response, sort_keys=True, indent=2)


        # ---[ MongoDB Insertion ]-------------------------------------------
        repo.dropCollection('stations')
        repo.createCollection('stations')
        repo[repo_name].insert_many(json_response)
        repo[repo_name].metadata({'complete': True})

        # ---[ Finishing Up ]-------------------------------------------
        print(repo[repo_name].metadata())
        repo.logout()
        endTime = datetime.datetime.now()
        return {"start": startTime, "end": endTime}









        #@staticmethod
        #def provenance(doc=prov.model.ProvDocument(), startTime=None, endTime=None):