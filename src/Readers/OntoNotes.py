# -*- coding: utf8 -*-

# http://conll.cemantix.org/2012/data.html

import os


class OntoNotesReader(object):
    """
    Класс для работы с форматом OntoNotes
    """
    def __init__(self):
        self.columns = ["docName", "partId", "tokenId", "form", "upos", "parseBit",
                        "lemma", "frameset", "sense", "speaker", "NER", "coreference"]  # "predicateArgs"
        self.defaultValues = [None, 0, 0, "", "-", "*", "-", "-", "-", "-", "*", "-"]
        pass
    
    def tokenLineToDict(self, tokenLine):
        d = {}
        d["id"] = tokenLine[0]
        d["form"] = tokenLine[1]
        d["lemma"] = tokenLine[2]
        d["upos"] = tokenLine[3]
        d["xpos"] = tokenLine[4]
        d["morph"] = tokenLine[5]
        d["head"] = tokenLine[6]
        d["deprel"] = tokenLine[7]
        d["deps"] = tokenLine[8]
        d["space"] = tokenLine[9]
        return d

    def tokenDictToLine(self, tokenDict, docInfo):
        line = []
        for c_i, colName in enumerate(self.columns):
            if colName in ["docName", "partId"]:
                line.append(docInfo[colName])
            elif colName in tokenDict:
                if colName=="form":
                    tokenDict[colName] = tokenDict[colName].replace(" ", "_")
                line.append(tokenDict[colName])
            else:
                line.append(self.defaultValues[c_i])
        line = "\t".join([str(x) for x in line])
        return line
    
    def checkFixParse(self, tokens):
        """
        сейчас просто вставляется,
        а надо проверять и возможно это востанавливается из парсинга
        """
        for s_i, sent in enumerate(tokens):
            for t_i, token in enumerate(sent):
                if t_i==0:
                    token["parseBit"] = "(TOP*"
                elif t_i==len(sent)-1:
                    token["parseBit"] = "*)"
                else:
                    token["parseBit"] = "*"
    
    def tokensToPositions():
        pass
    
    def write(self, data, outFile=None):
        if "genre" in data["docMeta"] and data["docMeta"]["genre"] is not None:
            data["docMeta"]["docName"] = data["docMeta"]["genre"] + "/" + data["docMeta"]["docName"]
        strData = "#begin document ({}); part {}\n".format(data["docMeta"]["docName"], data["docMeta"]["partId"])
        
        if "tokensWithFeatures" in data:
            self.checkFixParse(data["tokensWithFeatures"])
            for s_i, sent in enumerate(data["tokensWithFeatures"]):
                for t_i, token in enumerate(sent):
                    line = self.tokenDictToLine(token, data["docMeta"])
                    strData += line +"\n"

                if s_i != len(data["tokensWithFeatures"]) - 1:
                    strData += "\n"
            
        
        strData += "#end document\n"
        
        return strData
        