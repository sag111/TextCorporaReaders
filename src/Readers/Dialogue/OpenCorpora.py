# -*- coding: utf8 -*-
import os

class OpenCorpora(object):
    """
    Класс для работы с форматом Conll-u
    """
    def __init__(self, lineSeparator="\n"):
        self.columns = ["id", "startPos", "len", "form", "lemma", "pos+morph", "isItCoref", "isItMention"]
        self.dtypes = {"id": int, "startPos": int, "len": int}
        self.defaultValues = {"isItCoref": "-", "isItMention": "-"}
        self.lineSeparator = lineSeparator
    
    def tokenLineToDict(self, tokenLine):
        d = {}
        for c_i, c in enumerate(self.columns):
            if self.dtypes.get(c, None) == int:
                d[c] = int(tokenLine[c_i])
                if c=="len":
                    d["endPos"] = d["startPos"] + d["len"]
            else:
                if c=="pos+morph":
                    d["upos"] = tokenLine[c_i].split(",")[0]
                    d["morph"] = ",".join(tokenLine[c_i].split(",")[1:])
                else:
                    d[c] = tokenLine[c_i]
        return d
    
    def tokenDictToLine(self, tokenDict):
        tokenLine = []
        tokenLine.append(tokenDict["id"])
        tokenLine.append(tokenDict["startPos"])
        tokenLine.append(len(tokenDict["form"]))
        tokenLine.append(tokenDict["form"])
        tokenLine.append(tokenDict["lemma"])
        tokenLine.append(tokenDict["upos"])
        if "morph" in tokenDict and tokenDict["morph"] != "":
            tokenLine[-1] += ","+tokenDict["morph"]
        tokenLine.append(tokenDict.get("isItCoref", self.defaultValues["isItCoref"]))
        tokenLine.append(tokenDict.get("isItMention", self.defaultValues["isItMention"]))
        return "\t".join([str(x) for x in tokenLine])
    
    def tokensToPositions():
        raise Exception("Not implemented")
    
    def read(self, filePath):
        with open(filePath, "r", encoding="utf-8") as f:
            docTable = f.read()
        docTable = docTable[:-2]  # потому что в конце conllu \n\n
        docTable = docTable.split("\n"*2)
        docTable = [x.split("\n") for x in docTable]
        docTable = [[token.strip().split("\t") for token in sent] for sent in docTable ]
        
        #dicts = [[self.tokenLineToDict(token) for token in sent if len(token)==10] for sent in conllu ]
        text = {"raw":"", "meta":{}, "sentences": [], "paragraphs": []}
        text["meta"]["fileName"] = os.path.basename(filePath)        
        rawText = ""
        for s_i, sent in enumerate(docTable):
            sentence_d = {"raw":"", "meta":{}, "tokens":[]}
            for t_i, token in enumerate(sent):
                token_d = {}
                if len(token) != 8:
                    raise ValueError("Wierd token with len less then 8:\n{}".format(token))
                token_d = self.tokenLineToDict(token)
                
                sentence_d["tokens"].append(token_d)
                
                if t_i != 0:
                    spacesAfterPrevToken = token_d["startPos"] - sentence_d["tokens"][-2]["endPos"]
                else:
                    spacesAfterPrevToken = 0
                rawText += " " * spacesAfterPrevToken + token_d["form"]
            text["sentences"].append(sentence_d)

        text["raw"] = rawText
        return text
        
    def write(self, docData, filePath=None):
        conllLine = ""
        for sentence in docData["sentences"]:
            for token in sentence["tokens"]:
                tokenLine = self.tokenDictToLine(token)
                conllLine += tokenLine + self.lineSeparator
            conllLine += self.lineSeparator
        
        if filePath is not None:
            with open(filePath, "w", encoding="utf-8") as f:
                f.write(conllLine)
        else:
            return conllLine