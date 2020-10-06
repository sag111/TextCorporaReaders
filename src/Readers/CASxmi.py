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


class CASxmiReader(object):
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
        self.ContextLinkType =  self.typesystem.get_type('webanno.custom.ContextChainLink')
        self.ContextChainType =  self.typesystem.get_type('webanno.custom.ContextChainChain')
        self.ConcatLinkType = self.typesystem.get_type('webanno.custom.MedRelations')
        self.MedEntityType = self.typesystem.get_type('webanno.custom.MedEntity')
        self.CorefLinkType = self.typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.coref.type.CoreferenceLink')
        self.CorefChainType = self.typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.coref.type.CoreferenceChain')
        self.MedRelationsType = self.typesystem.get_type('webanno.custom.MedRelations')


    def GetChainsAsClusters(self, casData, linkDtype, chainDtype, objectsList):
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

    def getConcatedChains(self, casData):
        concatEdges = []
        for rel in casData.select(self.MedRelationsType.name):
            concatEdges.append(sorted([rel.Dependent.xmiID, rel.Governor.xmiID]))
        flatted = [x for sublist in concatEdges for x in sublist]
        uniq = sorted(list(set(flatted)))

        def dfs(v):
            hist[v] = True
            for w in uniq:
                if w==v:
                    continue
                if not hist[w]:
                    for edge in concatEdges:
                         if len(set([v,w]) & set(edge))==2:
                            dfs(w)
        pathes = set()
        for v in uniq:
            hist = defaultdict(bool)
            dfs(v)
            path = tuple(sorted([k for k,v in hist.items() if v]))
            pathes.add(path)
        return pathes

    def getEntities(self, casData, concatedAsSpans=True):
        text = casData.get_sofa().sofaString
        entitiesObjects, coreferenceObjects, contextObjects = defaultdict(list), defaultdict(list), defaultdict(list)
        # собираем список сущностей в исходном в файле в список словарей
        for medEntity in casData.select(self.MedEntityType.name):
            # заполняем поля словаря обязательными признаками
            newEntity = {
                "spans": [
                    {
                        "begin": int(medEntity.begin),
                        "end": int(medEntity.end)
                    }
                ],
                "xmiID": medEntity.xmiID,
                "text": casData.get_covered_text(medEntity),
                "MedEntityType": medEntity.MedEntityType,

            }
            # заполняем поля признаками, которые могут быть не заданы
            for feature in ["DisType", "MedType", "MedFrom", "MedMaker", "Note", "Context"]:
                if medEntity.__getattribute__(feature) is not None:
                    newEntity[feature] = medEntity.__getattribute__(feature)
            entitiesObjects["MedEntity"].append(newEntity)
        # для чейнов составляем структуры вида {mentions: [{startPos, endPos}], clusters:[[mention_idx_1, mention_idx_2], [...], ...]}
        self.GetChainsAsClusters(casData, self.CorefLinkType, self.CorefChainType, coreferenceObjects)
        self.GetChainsAsClusters(casData, self.ContextLinkType, self.ContextChainType, contextObjects)

        if concatedAsSpans:
            # у нас отношения только одни - конкаты
            # я их не добавляю как объекты, вместо этого меняю поля начала и конца сущностей на список спанов
            for k in entitiesObjects:
                pathes = self.getConcatedChains(casData)
                for path in pathes:
                    path = [medEntity for medEntity in entitiesObjects[k] if medEntity["xmiID"] in path]
                    mergedEntity = path[0]
                    for e_i, entity in enumerate(path[1:]):
                        equalEntities = True
                        for feature in ["DisType", "MedType", "MedFrom", "MedMaker", "Note"]:
                            if entity.get(feature, None) is not None and mergedEntity.get(feature, None) is None:
                                
                                logging.warning("Concated different entities:{} vs {}".format(mergedEntity, entity))
                                equalEntities = False
                                #mergedEntity[feature] = entity[feature]
                        if not equalEntities:
                            continue
                        mergedEntity["spans"].append({
                                "begin": int(entity["spans"][0]["begin"]),
                                "end": int(entity["spans"][0]["end"])
                            })
                        mergedEntity["text"] += " " + entity["text"]
                        entitiesObjects[k].remove(entity)
                for entity in entitiesObjects[k]:
                    entity["spans"] = sorted(entity["spans"], key=lambda x:int(x["begin"]))
        else:
            #если будут какие-то ещё отношения кроме конкатов, их надо подругому обрабатывать

            raise ValueError("Not implemented")
        return entitiesObjects, coreferenceObjects, contextObjects
    
    def read(self, filePath):
        docData = {"meta": {}, "raw": ""}
        docData["meta"]["fileName"] = os.path.basename(filePath)
        with open(filePath, "r", encoding="utf-8") as f:
            casData = load_cas_from_xmi(f.read(), typesystem=self.typesystem)
        docData["raw"] = casData.get_sofa().sofaString
        entitiesObjects, coreferenceObjects, contextObjects = self.getEntities(casData)
        docData["objects"] = entitiesObjects
        if coreferenceObjects is not None:
            docData["coreference"] = coreferenceObjects
        if contextObjects is not None:
            docData["context"] = contextObjects
        return docData
       
    def write(self, jsonData, filePath):
        newCas = Cas(self.typesystem)
        newCas.sofa_string = jsonData["raw"]
        
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