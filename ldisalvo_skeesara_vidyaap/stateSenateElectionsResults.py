"""
CS504 : stateSenateElectionsResults
Team : Vidya Akavoor, Lauren DiSalvo, Sreeja Keesara
Description :

Notes :

February 26, 2019
"""

import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
import csv
import io
from ldisalvo_skeesara_vidyaap.helper.constants import TEAM_NAME, STATE_SENATE_ELECTIONS, STATE_SENATE_ELECTIONS_RESULTS

class stateSenateElectionsResults(dml.Algorithm):
    contributor = TEAM_NAME
    reads = [STATE_SENATE_ELECTIONS]
    writes = [STATE_SENATE_ELECTIONS_RESULTS]

    @staticmethod
    def execute(trial=False):
        """
            Retrieve election results data from electionstats and insert into collection
            ex) {
                    "City/Town" : "Egremont",
                    "Ward" : "-",
                    "Pct" : "1",
                    "Election ID" : "131526",
                    "Adam G Hinds" : 682,
                    "All Others" : 0,
                    "Blanks" : 111,
                    "Total Votes Cast" : 793
                }
        """
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate(TEAM_NAME, TEAM_NAME)

        # Get list of election ids from collection
        electionIds = list(repo[STATE_SENATE_ELECTIONS].find({}, {"_id":1}))
        electionResultsRows = []

        # Use election ids to retrieve data from electionstats for each state senate election
        for question in electionIds:
            id = question['_id']
            url = 'http://electionstats.state.ma.us/elections/download/{id}/precincts_include:1/'.format(id=id)
            csvString = urllib.request.urlopen(url).read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(csvString))
            data = json.loads(json.dumps(list(reader)))
            data = [stateSenateElectionsResults.cleanData(row, id) for row in data[1:]]
            electionResultsRows.extend(data)

        # Insert rows into collection
        repo.dropCollection("stateSenateElectionsResults")
        repo.createCollection("stateSenateElectionsResults")
        repo[STATE_SENATE_ELECTIONS_RESULTS].insert_many(electionResultsRows)
        repo[STATE_SENATE_ELECTIONS_RESULTS].metadata({'complete': True})
        print(repo[STATE_SENATE_ELECTIONS_RESULTS].metadata())

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start": startTime, "end": endTime}

    @staticmethod
    def cleanData(precinctDictionary, id):
        """ Add Election ID field, change num votes values to int, remove '.' from middle initial"""

        # Add ID field
        precinctDictionary['Election ID'] = id

        keysToChange = list(precinctDictionary.keys())[3:-1]
        for key in keysToChange:
            precinctDictionary[key] = int(precinctDictionary[key].replace(',',''))
            precinctDictionary[key.replace('.','')] = precinctDictionary.pop(key)

        return precinctDictionary


    @staticmethod
    def provenance(doc=prov.model.ProvDocument(), startTime=None, endTime=None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('alice_bob', 'alice_bob')
        doc.add_namespace('alg',
                          'http://datamechanics.io/algorithm/')  # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat',
                          'http://datamechanics.io/data/')  # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont',
                          'http://datamechanics.io/ontology#')  # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/')  # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('alg:alice_bob#example',
                                {prov.model.PROV_TYPE: prov.model.PROV['SoftwareAgent'],
                                 'ont:Extension': 'py'})
        resource = doc.entity('bdp:wc8w-nujj', {'prov:label': '311, Service Requests',
                                                prov.model.PROV_TYPE: 'ont:DataResource',
                                                'ont:Extension': 'json'})
        get_found = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime)
        get_lost = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_found, this_script)
        doc.wasAssociatedWith(get_lost, this_script)
        doc.usage(get_found, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval',
                   'ont:Query': '?type=Animal+Found&$select=type,latitude,longitude,OPEN_DT'
                   }
                  )
        doc.usage(get_lost, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval',
                   'ont:Query': '?type=Animal+Lost&$select=type,latitude,longitude,OPEN_DT'
                   }
                  )

        lost = doc.entity('dat:alice_bob#lost', {prov.model.PROV_LABEL: 'Animals Lost',
                                                 prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(lost, this_script)
        doc.wasGeneratedBy(lost, get_lost, endTime)
        doc.wasDerivedFrom(lost, resource, get_lost, get_lost, get_lost)

        found = doc.entity('dat:alice_bob#found', {prov.model.PROV_LABEL: 'Animals Found',
                                                   prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(found, this_script)
        doc.wasGeneratedBy(found, get_found, endTime)
        doc.wasDerivedFrom(found, resource, get_found, get_found, get_found)

        repo.logout()

        return doc


'''
# This is example code you might use for debugging this module.
# Please remove all top-level function calls before submitting.
example.execute()
doc = example.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))
'''
## eof