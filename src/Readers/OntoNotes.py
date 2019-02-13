# -*- coding: utf8 -*-

# http://conll.cemantix.org/2012/data.html

class OntoNotesReader(object):
    """
    Класс для работы с форматом OntoNotes
    """
    def __init__(self):
        self.columns = ["fileName", "partId", "id", "form", "upos", "parseBit",
                        "lemma", "frameset", "sense", "speaker", "NER", "coreference"] # "predicateArgs"
        self.defaultValues = [None, 0, 0, "", "-", "*", "-", "-", "-", "-", "*", "-"]
        pass
    
    def tokenLineToDict(self, tokenLine):
        d = {}
        d["id"] = tokenLine[2]
        d["form"] = tokenLine[3]
        d["upos"] = tokenLine[4]
        d["xpos"] = "_"
        d["parseBit"] = tokenLine[5]
        d["lemma"] = tokenLine[6]
        d["frameset"] = None
        d["sense"] = None
        d["speaker"] = None
        d["NER"] = None
        d["coreference"] = None
        return d

    def tokenDictToLine(self, tokenDict, docMeta):
        line = []
        for c_i, colName in enumerate(self.columns):
            if colName == "fileName":
                line.append(docMeta[colName])
            elif colName == "partId":
                line.append(0)
            elif colName in tokenDict:
                line.append(tokenDict[colName])
            else:
                line.append(self.defaultValues[c_i])
        line = "\t".join([str(x) for x in line])
        return line
    
    def checkFixParse(self, sentences):
        """
        сейчас просто вставляется,
        а надо проверять и возможно это востанавливается из парсинга
        """
        for s_i, sent in enumerate(sentences):
            for t_i, token in enumerate(sent["tokens"]):
                if "parseBit" not in token:
                    if t_i==0:
                        token["parseBit"] = "(TOP*"
                    elif t_i==len(sent)-1:
                        token["parseBit"] = "*)"
                    else:
                        token["parseBit"] = "*"
    
    def tokensToPositions():
        pass
    
    def write(self, docData, outFile=None):
        if "genre" in docData["meta"] and docData["meta"]["genre"] is not None:
            docData["meta"]["fileName"] = docData["meta"]["genre"] + "/" + docData["meta"]["fileName"]
        strData = "#begin document ({}); part {}\n".format(docData["meta"]["fileName"], docData["meta"]["partId"])
        
        
        self.checkFixParse(docData["sentences"])
        for s_i, sent in enumerate(docData["sentences"]):
            for t_i, token in enumerate(sent["tokens"]):
                line = self.tokenDictToLine(token, docData["meta"])
                strData += line +"\n"

            if s_i != len(docData["sentences"]) - 1:
                strData += "\n"
            
        
        strData += "#end document\n"
        
        return strData
    
    def read(self, filePath):
        raise ValueError("Not implemented")