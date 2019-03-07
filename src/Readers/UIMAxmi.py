# -*- coding: utf8 -*-

import os
import re
import xml.etree.ElementTree as ET

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
            elif self.coreference is not None and ("ConcatenationLink" in child.tag or "ConcatenationChain" in child.tag):
                if "ConcatenationLink" in child.tag:
                    self.concatenation["mentions"].append({"startPos": int(entity["begin"]),
                                                         "endPos": int(entity["end"]),
                                                         "next": int(entity.get("next", -1)),
                                                         "id": int(entity["{http://www.omg.org/XMI}id"])})
                elif "CoreferenceChain" in child.tag:
                    self.concatenation["clusters"].append({"firstId": int(entity['first'])})

        if self.coreference is not None:
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
        