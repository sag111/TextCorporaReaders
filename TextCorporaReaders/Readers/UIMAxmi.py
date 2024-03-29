# -*- coding: utf8 -*-

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

# ятут исправил - брейк в проверке идеального совпадения конката и сущности убрал,
# потому что терялась нужная сущность, если пересекали несколько, надо проверить, в скрипте перевода, нет ли такой ж еошибки
# уддаление сущностей входящих в несколько линков добавил
# и заменил множество на список при подсчёте упоминаний
# после entity["MedEntityType"]==mergedEntity["MedEntityType"] добавил ADR, там не было
from collections import defaultdict
def processConcat(docData):
    for concatCluster in docData["concatenation"]["clusters"]:
        concatedEntities = defaultdict(list)
        # поиск сущностей, которые пересекаются с линками
        linksWithoutEntity = []
        for m_i in concatCluster:
            link = docData["concatenation"]["mentions"][m_i]
            for medEntity in docData["objects"]["MedEntity"]:
                if medEntity["spans"][0]["begin"]==link["startPos"] and medEntity["spans"][0]["end"]==link["endPos"]:
                    concatedEntities[m_i].append(medEntity)
                    #break
                elif medEntity["spans"][0]["begin"]<=link["endPos"] and medEntity["spans"][0]["end"]>=link["endPos"]:
                    concatedEntities[m_i].append(medEntity)
                elif medEntity["spans"][0]["begin"]<=link["startPos"] and medEntity["spans"][0]["end"]>=link["startPos"]:
                    concatedEntities[m_i].append(medEntity)
                elif medEntity["spans"][0]["begin"]>=link["startPos"] and medEntity["spans"][0]["end"]<=link["endPos"]:
                    concatedEntities[m_i].append(medEntity)
                elif medEntity["spans"][0]["begin"]<=link["startPos"] and medEntity["spans"][0]["end"]>=link["endPos"]:
                    # Такого почему-то раньше не было добавлено, видимо из-за огромных Other
                    # Не понятно, надо ли это добавлять
                    pass
                    #print("LINK", link, "ENTITY", medEntity)
                    #concatedEntities[m_i].append(medEntity)
            if len(concatedEntities[m_i]) == 0:
                # обговаривалось, что конкат линк можно ставить без дублирования мед.сущности
                # тогда будет считаться, что там стоит такая же сущность
                linksWithoutEntity.append(link)
        #print("concatedEntities", concatedEntities)
        concatedEntities_list = [x for sublist in concatedEntities.values() for x in sublist]
        
        # составляем словарь, указывающий для каждого индекса сущности, с какими линками (индекс) она пересекается
        reverseIndex = {}
        for e_i, entity in enumerate(concatedEntities_list):
            reverseIndex[e_i] = []
            for k in concatedEntities:
                if entity in concatedEntities[k]:
                    reverseIndex[e_i].append(k)
        # Удаляем из списка конкатенирующихся сущностей те, которые попали во все линки
        # То есть одна здоровая сущность пересекла все линки, её нет смысла конкатить
        for k in sorted(reverseIndex.keys(), reverse=True):
            if len(reverseIndex[k])>=len(concatedEntities.keys()):
                del concatedEntities_list[k]
        
        #Объединение схожих сущностей и удаление одних из них
        # mergedEntities будет содержать уникальные сущности, не совпадающие по типу.
        # entitiesToRemove - сущности совпадающие по типу с сущностями из mergedEntities
        # Они будут удалены из словаря, а их спаны добавлены в сущности из mergedEntities
        mergedEntities = []
        entitiesToRemove = []
        for entity in concatedEntities_list:
            #print("entity", entity)
            entityToMerge = None
            for mergedEntity in mergedEntities:
                # был один раз такой косяк, надо это где-то в более подходящем месте отловить
                # тут оно просто сильно мешает
                if "MedEntityType" not in entity:
                    continue
                #Проверить атрибуты, которые есть и там и там на совпадение
                if entity["MedEntityType"]==mergedEntity["MedEntityType"]:
                    if entity["MedEntityType"]=="Medication" and entity.get("MedType", "None")==mergedEntity.get("MedType", "None")\
                     and entity.get("MedMaker", "None")==mergedEntity.get("MedMaker", "None")  and entity.get("MedFrom", "None")==mergedEntity.get("MedFrom", "None"):
                        entityToMerge = mergedEntity
                        break
                    if entity["MedEntityType"]=="Disease" and entity["DisType"]==mergedEntity["DisType"]:
                        entityToMerge = mergedEntity
                        break
                    if entity["MedEntityType"]=="ADR" and mergedEntity["MedEntityType"]=="ADR":
                        entityToMerge = mergedEntity
                        break
            #print("entityToMerge", entityToMerge)
            if entityToMerge == None:
                mergedEntity = entity
                mergedEntities.append(mergedEntity)
            else:
                entitiesToRemove.append(entity)
                # если сконкатенированная сущность имеет какой-то признак, которого нет
                # у той, которая будет сохранена, добавляем его.
                # Хотя кажется это не будет происходить, раз я по всем признакам сравнивать решил
                for k in entity.keys():
                    if k not in ["next", "id", "startPos", "endPos", '{http://www.omg.org/XMI}id', "sofa", "begin", "end"]:
                        if k not in mergedEntity:
                            mergedEntity[k] = entity[k]
                mergedEntity["spans"] += entity["spans"]
        for entityToRemove in entitiesToRemove:
            docData["objects"]["MedEntity"].remove(entityToRemove)
        
        # заполняем линки, которые не пересекали сущности
        if len(linksWithoutEntity) > 0:
            for entity in mergedEntities:
                for link in linksWithoutEntity:
                    entity["spans"].append({"begin": link["startPos"], "end": link["endPos"]})
    for entity in docData["objects"]["MedEntity"]:
            entity["spans"] = sorted(entity["spans"], key=lambda x:int(x["begin"]))

def getEntityText(text, entity):
    entityText = []
    for span in entity["spans"]:
        entityText.append(text[span["begin"]:span["end"]])
    entityText = " ".join(entityText)
    return entityText

class UIMAxmiReader(object):
    """
    Класс для работы с форматом UIMA XMI
    Сейчас реализовано извлечение текста и заданных слоёв разметки
    TODO
    Разработать стандарт внутреннего представления слоёв разметки
    Реализация ридера для коллекции
    самостоятельное определение всех слоёв разметки (для коллекции документов, для одного не получится)

    """
    def __init__(self, markupLayers):
        self.markupLayers = markupLayers
        if "ConcatenationLink" in self.markupLayers and "ConcatenationChain" in self.markupLayers:
            self.concatenation = {"clusters":[], "mentions":[]}
        else:
            self.concatenation = None
        if "CoreferenceLink" in self.markupLayers and "CoreferenceChain" in self.markupLayers:
            self.coreference = {"clusters":[], "mentions":[]}
        else:
            self.coreference = None
            
        self.entities = {}
        for k in self.markupLayers:
            if k not in ["CoreferenceLink", "CoreferenceChain", "ConcatenationLink", "ConcatenationChain"]:
                self.entities[k] = []
        pass
    
    def processCoreference(self):
        clusterArrays = []
        for cluster in self.coreference["clusters"]:
            clusterArrays.append([])
            nextId = cluster["firstId"]
            while nextId != -1:
                for m_i, mention in enumerate(self.coreference["mentions"]):
                    if mention["id"]==nextId:
                        clusterArrays[-1].append(m_i)
                        newNextId = mention["next"]
                        break
                if newNextId==nextId:
                    raise ValueError("next mention id not found")
                nextId = newNextId

        self.coreference["clusters"] = clusterArrays
    
    def processConcatenation(self):
        clusterArrays = []
        for cluster in self.concatenation["clusters"]:
            clusterArrays.append([])
            nextId = cluster["firstId"]
            while nextId != -1:
                for m_i, mention in enumerate(self.concatenation["mentions"]):
                    if mention["id"]==nextId:
                        clusterArrays[-1].append(m_i)
                        newNextId = mention["next"]
                        break
                if newNextId==nextId:
                    raise ValueError("next mention id not found")
                nextId = newNextId

        self.concatenation["clusters"] = clusterArrays

    def getEntities(self):
        self.text = None
        for child in self.fileRoot:
            entity = child.attrib
            if "custom" in child.tag and "Concatenation" not in child.tag:
                # custom помечаются созданные мной слои для медицинской разметки
                markupLayerMO = re.search("|".join(self.markupLayers), child.tag)
                markupLayer = markupLayerMO.group()                
                entity["begin"] = int(entity["begin"])
                entity["end"] = int(entity["end"])
                self.entities[markupLayer].append(child.attrib)
            elif "Sofa" in child.tag:
                # отсюда достаётся текст
                self.text = child.attrib["sofaString"]
            elif self.coreference is not None:
                if "CoreferenceLink" in child.tag:
                    self.coreference["mentions"].append({"startPos": int(entity["begin"]),
                                                         "endPos": int(entity["end"]),
                                                         "next": int(entity.get("next", -1)),
                                                         "id": int(entity["{http://www.omg.org/XMI}id"])})
                elif "CoreferenceChain" in child.tag:
                    self.coreference["clusters"].append({"firstId": int(entity['first'])})
            elif self.concatenation is not None and ("ConcatenationLink" in child.tag or "ConcatenationChain" in child.tag):
                if "ConcatenationLink" in child.tag:
                    self.concatenation["mentions"].append({"startPos": int(entity["begin"]),
                                                         "endPos": int(entity["end"]),
                                                         "next": int(entity.get("next", -1)),
                                                         "id": int(entity["{http://www.omg.org/XMI}id"])})
                elif "ConcatenationChain" in child.tag:
                    self.concatenation["clusters"].append({"firstId": int(entity['first'])})
        
        if self.coreference is not None:
            self.processCoreference()
        if self.concatenation is not None:
            self.processConcatenation()
        
        self.text = self.text.replace("&amp;", "&")
        self.text = self.text.replace("&#10;", "\n")
        self.text = self.text.replace("&quot;", "\"")
    
    def read(self, filePath):
        docData = {"meta": {}, "raw": ""}
        tree = ET.parse(filePath)
        self.fileRoot = tree.getroot()
        entities = self.getEntities()
        docData["raw"] = self.text
        docData["meta"]["fileName"] = os.path.basename(filePath)
        docData["objects"] = self.entities
        if self.coreference is not None:
            docData["coreference"] = self.coreference
        if self.concatenation is not None:
            docData["concatenation"] = self.concatenation
        return docData
        
        