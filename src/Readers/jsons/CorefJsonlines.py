# -*- coding: utf8 -*-

import json

class CorefJsonCollection(object):
    def __init__(self):
        
        self.annotationLayers = ["speakers", "constituents", "morphology", "clusters", "doc_key", "sentences", "ner"]
        self.defaultVals = {
            "speaker": "_",
            "morphology": "_",
            "form": "_",
        }
        pass

    def read(self, filePath, predicted=False):
        # надо еще нёр и парсинг восстанавливать
        with open(filePath, "r", encoding="utf-8") as f:
            jsonlines = f.readlines()
        collectionData = []
        for line in jsonlines:
            docData = {"meta" : {}, "sentences": [], "coreference": {"clusters":[], "mentions": []}}
            docJson = json.loads(line)
            docData["meta"]["docName"] = docJson["doc_key"]
            for s_i in range(len(docJson["sentences"])):
                sentenceData = {"tokens":[]}
                for t_i in range(len(docJson["sentences"][s_i])):
                    tokenData = {}                    
                    tokenData["form"] = docJson["sentences"][s_i][t_i]
                    tokenData["speaker"] = docJson["speakers"][s_i][t_i]
                    if "morphology" in docJson:
                        tokenData["morph"] = docJson["morphology"][s_i][t_i]
                    sentenceData["tokens"].append(tokenData)
                docData["sentences"].append(sentenceData)

            for cluster in docJson["clusters"] if not predicted else docJson["predicted_clusters"]:
                clusterMentions = []
                for mention in cluster:
                    mentionData = {"startToken":mention[0], "endToken": mention[1]}
                    if mentionData in docData["coreference"]["mentions"]:
                        clusterMentions.append(docData["coreference"]["mentions"].index(mentionData))
                    else:
                        docData["coreference"]["mentions"].append(mentionData)
                        clusterMentions.append(len(docData["coreference"]["mentions"]) -1)
                docData["coreference"]["clusters"].append(clusterMentions)
            collectionData.append(docData)
        return collectionData

    def write(self, collectionData, filePath=None):
        jsonlines = []
        for docData in collectionData:
            documentJson = {}
            for layer in self.annotationLayers:
                documentJson[layer] = []
            if "genre" in docData["meta"]:
                documentJson["doc_key"] = docData["meta"]["genre"][:2] + "/" + docData["meta"]["fileName"]
            else:
                documentJson["doc_key"] = docData["meta"]["fileName"]
            documentJson["constituents"] = []
            for sentence in docData["sentences"]:
                documentJson["constituents"].append([-1, -1, "TOP"])  # я хз, что это
                documentJson["speakers"].append([])
                documentJson["morphology"].append([])
                documentJson["sentences"].append([])
                for token in sentence['tokens']:
                    documentJson["speakers"][-1].append(token.get("speaker", self.defaultVals["speaker"]))
                    documentJson["morphology"][-1].append(token.get("morph", self.defaultVals["morphology"]))
                    documentJson["sentences"][-1].append(token.get("form", self.defaultVals["form"]))
            documentJson["clusters"] = []
            for cluster in docData["coreference"]["clusters"]:
                documentJson["clusters"].append([])
                for m_i in cluster:
                    mentionsTokens = [-1, -1]
                    mentionsTokens[0] = docData["coreference"]["mentions"][m_i]["startToken"]
                    mentionsTokens[1] = docData["coreference"]["mentions"][m_i]["endToken"]
                    documentJson["clusters"][-1].append(mentionsTokens)
            jsonlines.append(json.dumps(documentJson))
        if filePath is not None:
            with open(filePath, "w", encoding="utf-8") as f:
                for line in jsonlines:
                    f.write(line + "\n")
