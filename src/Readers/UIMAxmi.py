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
        
        self.entities = {}
        for k in self.markupLayers:
            self.entities[k] = []
        pass
    
    def getEntities(self):
        self.text = None
        for child in self.fileRoot:
            if "custom" in child.tag:
                # custom помечаются созданные мной слои для медицинской разметки
                markupLayerMO = re.search("|".join(self.markupLayers), child.tag)
                markupLayer = markupLayerMO.group()
                entity = child.attrib
                entity["begin"] = int(entity["begin"])
                entity["end"] = int(entity["end"])
                self.entities[markupLayer].append(child.attrib)
            elif "Sofa" in child.tag:
                # отсюда достаётся текст
                self.text = child.attrib["sofaString"]
        self.text = self.text.replace("&amp;", "&")
        self.text = self.text.replace("&#10;", "\n")
        self.text = self.text.replace("&quot;", "\"")
    
    def read(self, filePath):
        tree = ET.parse(filePath)
        self.fileRoot = tree.getroot()
        self.getEntities()
        
        return {"rawText": self.text}

