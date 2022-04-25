# -*- coding: utf8 -*-

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from cassis import *
from cassis.xmi import CasXmiSerializer
from collections import defaultdict
import logging

def getEntityText(text, entity):
    entityText = []
    for span in entity["spans"]:
        entityText.append(text[span["begin"]:span["end"]])
    entityText = " ".join(entityText)
    return entityText


class RuDRecxmiReader(object):
    """
    Класс для работы с форматом UIMA XMI
    Сейчас реализовано извлечение текста и заданных слоёв разметки
    TODO
    Разработать стандарт внутреннего представления слоёв разметки
    Реализация ридера для коллекции
    самостоятельное определение всех слоёв разметки (для коллекции документов, для одного не получится)

    """
    def __init__(self, typesystem):
        if type(typesystem)==str:
            with open(typesystem, 'rb') as f:
                self.typesystem = load_typesystem(f)
        else:
            self.typesystem = typesystem
        self.GetTypes()

    def GetTypes(self):
        self.NERType = self.typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity')
        self.SentenceLinkType = self.typesystem.get_type('webanno.custom.SentenceLink')
        self.SentenceChainType = self.typesystem.get_type('webanno.custom.SentenceChain')
        self.MetaDataType = self.typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.metadata.type.DocumentMetaData')
        self.SentenceType = self.typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence')
        self.TokenType = self.typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token')


    def GetChainsAsClusters(self, casData, linkDtype, chainDtype, objectsList):
        objectsList["mentions"]
        objectsList["clusters"]
        for link in casData.select(linkDtype.name):
            objectsList["mentions"].append({
                    "startPos": int(link.begin),  # стоит ли сохранять next и id?
                    "endPos": int(link.end)
                })
        for chain in casData.select(chainDtype.name):
            objectsList["clusters"].append([])
            nextLink = chain.first
            while nextLink is not None:
                newLink_d = {
                    "startPos": int(nextLink.begin),
                    "endPos": int(nextLink.end)
                }
                objectsList["clusters"][-1].append(objectsList["mentions"].index(newLink_d))
                nextLink = nextLink.next
            objectsList["clusters"][-1] = sorted(objectsList["clusters"][-1])


    def getEntities(self, casData, concatedAsSpans=True):
        text = casData.get_sofa().sofaString
        entitiesObjects, sentencesLinksObjects = defaultdict(list), defaultdict(list)
        # собираем список сущностей в исходном в файле в список словарей
        for nerEntity in casData.select(self.NERType.name):
            # заполняем поля словаря обязательными признаками
            newEntity = {
                "spans": [
                    {
                        "begin": int(nerEntity.begin),
                        "end": int(nerEntity.end)
                    }
                ],
                "xmiID": nerEntity.xmiID,
                "text": casData.get_covered_text(nerEntity),
                "MedEntityType": nerEntity.value,

            }
            entitiesObjects["NER"].append(newEntity)
        # для чейнов составляем структуры вида {mentions: [{startPos, endPos}], clusters:[[mention_idx_1, mention_idx_2], [...], ...]}
        self.GetChainsAsClusters(casData, self.SentenceLinkType, self.SentenceChainType, sentencesLinksObjects)
        return entitiesObjects, sentencesLinksObjects
    
    def getSegmentation(self, casData, docData):
        docData["sentences"] = []
        sentencesBounds = []
        for sent in casData.select(self.SentenceType.name):
            docData["sentences"].append([])
            sentencesBounds.append((sent.begin, sent.end))
        sentencesBounds = sorted(sentencesBounds, key=lambda x:x[0])
        for token in casData.select(self.TokenType.name):
            for s_i, sentBound in enumerate(sentencesBounds):
                if token.begin >= sentBound[0] and token.begin < sentBound[1]:
                    break
            docData["sentences"][s_i].append({
                "forma": casData.get_covered_text(token),
                "start": token.begin,
                "end": token.end,
            })

    def read(self, filePath):
        docData = {"meta": {}, "raw": ""}
        docData["meta"]["fileName"] = os.path.basename(filePath)
        with open(filePath, "r", encoding="utf-8") as f:
            casData = load_cas_from_xmi(f.read(), typesystem=self.typesystem)
        for smth in casData.select(self.MetaDataType.name):
            docData["meta"]["annotator"] = smth.documentId
        docData["raw"] = casData.get_sofa().sofaString
        self.getSegmentation(casData, docData)
        entitiesObjects, sentencesLinksObjects = self.getEntities(casData)
        docData["objects"] = entitiesObjects
        docData["SentenceLinks"] = sentencesLinksObjects
        return docData
    
    def addSegmentationToCas(self, casData, docData):
        prevSentenceBounds = None
        for sentence in docData["sentences"]:
            if prevSentenceBounds is not None:
                prevSentenceBounds[1] = sentence[0]["start"]
                casData.add_annotation(self.SentenceType(begin=prevSentenceBounds[0], end=prevSentenceBounds[1]))
            prevSentenceBounds = [sentence[0]["start"], sentence[-1]["end"]]
            for token in sentence:
                casData.add_annotation(self.TokenType(begin=token["start"], end=token["end"]))
        if prevSentenceBounds is not None:
            prevSentenceBounds[1] = sentence[0]["start"]
            casData.add_annotation(self.SentenceType(begin=prevSentenceBounds[0], end=prevSentenceBounds[1]))

    def write(self, jsonData, filePath):
        newCas = Cas(self.typesystem)
        newCas.sofa_string = jsonData["raw"]
        
        if "annotator" in jsonData["meta"]:
            docMeta = self.MetaDataType()
            docMeta.documentId = jsonData["meta"]["annotator"]
            newCas.add_annotation(docMeta)
            
        self.addSegmentationToCas(newCas, jsonData)

        medEntity_requiredFeatures = [x.name for x in self.MedEntityType.all_features]
        for medEntity in jsonData["objects"]["MedEntity"]:
            spanEntities = []
            for span in medEntity["spans"]:
                newEntity = {k:v for k,v in medEntity.items() if k in medEntity_requiredFeatures}
                casEntity = self.MedEntityType(**newEntity)
                casEntity.sofa = newCas.get_sofa().xmiID
                casEntity.begin = span["begin"]
                casEntity.end = span["end"]
                newCas.add_annotation(casEntity)
                spanEntities.append(casEntity)
                #break
            if len(spanEntities)>1:
                for gov, dep in zip(spanEntities, spanEntities[1:]):
                    relAnn = self.MedRelationsType(Governor=gov, Dependent=dep, RelationType="concat")
                    newCas.add_annotation(relAnn)
          
        for cluster in jsonData["coreference"]["clusters"]:
            prevLink = None
            for m_i in sorted(cluster, reverse=True):
                mention = jsonData["coreference"]["mentions"][m_i]
                linkAnn = self.CorefLinkType(begin=mention['startPos'], end=mention['endPos'])
                if prevLink is not None:
                    linkAnn.next = prevLink
                newCas.add_annotation(linkAnn)
                prevLink = linkAnn
            chainAnn = self.CorefChainType(first=prevLink)
            newCas.add_annotation(chainAnn)

        if self.typesystem.contains_type('webanno.custom.ContextChainChain'):
            for cluster in jsonData["context"]["clusters"]:
                prevLink = None
                for m_i in sorted(cluster, reverse=True):
                    mention = jsonData["context"]["mentions"][m_i]
                    linkAnn = self.ContextLinkType(begin=mention['startPos'], end=mention['endPos'])
                    if prevLink is not None:
                        linkAnn.next = prevLink
                    newCas.add_annotation(linkAnn)
                    prevLink = linkAnn
                chainAnn = self.ContextChainType(first=prevLink)
                newCas.add_annotation(chainAnn)
        serializer = CasXmiSerializer()
        with open(filePath, "wb") as f:
            serializer.serialize(f, newCas)