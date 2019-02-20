# -*- coding: utf8 -*-
import os
import re

class CoNLLUReader(object):
    """
    Класс для работы с форматом Conll-u
    """
    def __init__(self):
        self.columns = ["id", "form", "lemma", "upos", "xpos", "morph", "head", "deprel", "deps", "spaceAfter"]
        self.dtypes = {"id": int, "head": int}
        pass
    
    def tokenLineToDict(self, tokenLine):
        d = {}
        for c_i, c in enumerate(self.columns):
            if c=="spaceAfter":
                tokenLine[c_i] = re.sub("Spaces?After=", "", tokenLine[c_i], re.U)
                tokenLine[c_i] = tokenLine[c_i].replace("\\r\\n", "\n")
                tokenLine[c_i] = tokenLine[c_i].replace("\\n", "\n")
                tokenLine[c_i] = tokenLine[c_i].replace("\\s", " ")
            if self.dtypes.get(c, None) == int:
                d[c] = int(tokenLine[c_i])
            else:
                d[c] = tokenLine[c_i]            
        return d
    
    def tokenDictToLine(self, tokenDict):        
        if tokenDict["spaceAfter"] !="_":
            tokenDict["spaceAfter"] = tokenDict["spaceAfter"].replace("\n", "\\n")
            tokenDict["spaceAfter"] = tokenDict["spaceAfter"].replace(" ", "\\s")
            if tokenDict["spaceAfter"]=="No":
                tokenDict["spaceAfter"] = "SpaceAfter="+tokenDict["spaceAfter"]
            else:
                tokenDict["spaceAfter"] = "SpacesAfter="+tokenDict["spaceAfter"]
        line = [str(tokenDict[c]) for c in self.columns]
        line = "\t".join(line)
        return line
    
    def tokensToPositions():
        pass
    
    def read(self, filePath):
        with open(filePath, "r", encoding="utf-8") as f:
            conllu = f.read()
        conllu = conllu[:-2]  # потому что в конце conllu \n\n
        conllu = conllu.split("\n\n")
        conllu = [x.split("\n") for x in conllu]
        conllu = [[token.strip().split("\t") for token in sent] for sent in conllu ]
        
        #dicts = [[self.tokenLineToDict(token) for token in sent if len(token)==10] for sent in conllu ]
        text = {"raw":"", "meta":{}, "sentences": [], "paragraphs": []}
        text["meta"]["fileName"] = os.path.basename(filePath)
        rawText = ""
        for s_i, sent in enumerate(conllu):
            sentence_d = {"raw":"", "meta":{}, "tokens":[]}
            for t_i, token in enumerate(sent):
                token_d = {}
                if len(token) != 10:
                    # либо это коммент либо какая-то хрень
                    token = "\t".join(token)
                    if token[0] == "#":
                        if "newdoc id" in token:
                            text["meta"]["id"] = token.replace("# newdoc id = ", "")
                        elif "newpar" in token:
                            # paragraphs = sent idx where new paragraph starts
                            # блин, вот это не правильно, id то не тот, который указан ниже
                            text["paragraphs"].append(s_i)
                        elif "sent_id" in token:
                            sentence_d["meta"]["id"] = int(token.replace("# sent_id = ", ""))
                        elif "text" in token:
                            sentence_d["raw"] = token.replace("# text = ", "")  
                        continue
                    else:
                        raise ValueError("Wierd token with len less then 10:\n{}".format(token))
                token_d = self.tokenLineToDict(token)
                
                sentence_d["tokens"].append(token_d)
                
                rawText += token_d["form"]
                if token_d["spaceAfter"] == "_":
                    rawText += " "
                elif token_d["spaceAfter"] == "No":
                    continue
                else:
                    rawText += token_d["spaceAfter"]
            text["sentences"].append(sentence_d)

        text["raw"] = rawText
        return text
        
    def write(self, data, filePath=None):
        conllLines = []
        conllLines.append("# newdoc id = {}".format(data["meta"]["id"]))
        for s_i, sentence_d in enumerate(data["sentences"]):
            if s_i in data["paragraphs"]:
                conllLines.append("# newpar")
            conllLines.append("# sent_id = {}".format(sentence_d["meta"]["id"]))
            conllLines.append("# text = {}".format(sentence_d["raw"]))
            
            for token in sentence_d["tokens"]:
                line = self.tokenDictToLine(token)
                conllLines.append(line)
            conllLines.append("")
        if filePath is not None:
            with open(filePath, "w") as f:
                for line in conllLines:
                    f.write(line + "\n")
        else:
            return "\n".join(conllLines) + "\n"
        #raise Exception("Not implemented")
