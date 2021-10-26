# -*- coding: UTF-8 -*-

import os

"""
Chains folder: Mention Id    Mention Offset    Mention Length    Chain Id
Mentions folder: Mention Id    Mention Offset    Mention Length
Raw Texts;
udpiped
morph
"""
class AnCoR2019(object):
    """
    Ридер для датасета с соревнования dialogue ancor 2019
    """
    def __init__(self):
        pass

    def readCollection(self, folderPath):
        collection = []
        fileNames = []
        for fName in os.listdir("{}/Texts".format(folderPath)):
            fileNames.append(fName)
        for fName in fileNames:
            doc_d = {"raw": "", "meta": {}}
            doc_d["meta"]["fileName"] = fName
            with open("{}/Texts/{}".format(folderPath, fName), "r", encoding="utf-16") as f:
                text = f.read()
            doc_d["raw"] = text
            
            doc_d["coreference"] = {}
            doc_d["coreference"]["mentions"] = []
            if os.path.exists("{}/Mentions/{}".format(folderPath, fName)):
                with open("{}/Mentions/{}".format(folderPath, fName), "r", encoding="utf-8") as f:
                    mentions = f.readlines()
                    mentions = [m.strip().split() for m in mentions]
                for m_i, mention in enumerate(mentions):
                    mention_d = {}
                    mention_d["startPos"] = int(mention[1])
                    mention_d["endPos"] = int(mention[1]) + int(mention[2])
                    if m_i+1 != int(mention[0]):
                        raise ValueError("wrong id of mention {}".format(mention))
                    doc_d["coreference"]["mentions"].append(mention_d)

            doc_d["coreference"]["clusters"] = []
            if os.path.exists("{}/Chains/{}".format(folderPath, fName)):
                with open("{}/Chains/{}".format(folderPath, fName), "r", encoding="utf-8") as f:
                    chains = f.readlines()
                    chains = [ch.strip().split() for ch in chains]
                clusters = {}
                for chainedMention in chains:
                    if int(chainedMention[3]) not in clusters:
                        clusters[int(chainedMention[3])] = []
                    clusters[int(chainedMention[3])].append(int(chainedMention[0])-1)
                doc_d["coreference"]["clusters"] = [clusters[k] for k in sorted(clusters.keys())]
            else:
                doc_d["coreference"]["clusters"] = []
                

            collection.append(doc_d)
        return collection

    def writeCollection(self, collectionData, folderPath):
        if not os.path.exists("{}/Texts".format(folderPath)):
            os.mkdir("{}/Texts".format(folderPath))
        if not os.path.exists("{}/Mentions".format(folderPath)):
            os.mkdir("{}/Mentions".format(folderPath))
        if not os.path.exists("{}/Chains".format(folderPath)):
            os.mkdir("{}/Chains".format(folderPath))
        
        for doc in collectionData:
            with open("{}/Texts/{}".format(folderPath, doc["meta"]["fileName"]), "w", encoding="utf8") as f:
                f.write(doc["raw"])
            with open("{}/Mentions/{}".format(folderPath, doc["meta"]["fileName"]), "w", encoding="utf8") as f:
                for m_i, mention in enumerate(doc["coreference"]["mentions"]):
                    mentionLine = []
                    mentionLine.append(m_i+1)
                    mentionLine.append(mention["startPos"])
                    mentionLine.append(mention["endPos"] - mention["startPos"])
                    mentionLine = " ".join([str(x) for x in mentionLine]) + "\n"
                    f.write(mentionLine)
            with open("{}/Chains/{}".format(folderPath, doc["meta"]["fileName"]), "w", encoding="utf8") as f:
                for c_i, cluster in enumerate(doc["coreference"]["clusters"]):
                    for m_i in cluster:
                        mention = doc["coreference"]["mentions"][m_i]
                        mentionLine = []
                        mentionLine.append(m_i+1)
                        mentionLine.append(mention["startPos"])
                        mentionLine.append(mention["endPos"] - mention["startPos"])
                        mentionLine.append(c_i+1)
                        mentionLine = " ".join([str(x) for x in mentionLine]) + "\n"
                        f.write(mentionLine)