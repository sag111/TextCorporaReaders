# -*- coding: utf8 -*-

class CoNLLUReader(object):
    """
    Класс для работы с форматом Conll-u
    """
    def __init__(self):
        self.columns = ["tokenId", "form", "lemma", "upos", "xpos", "morph", "head", "deprel", "deps", "space"]
        pass
    
    def tokenLineToDict(self, tokenLine):
        d = {}
        for c_i, c in enumerate(self.columns):
            d[c] = tokenLine[c_i]
        return d
    
    def tokensToPositions():
        pass
    
    def read(self, filePath):
        with open(filePath, "r", encoding="utf-8") as f:
            conllu = f.read()
        conllu = conllu.split("\n\n")
        conllu = [x.split("\n") for x in conllu]
        conllu = [[token.split("\t") for token in sent] for sent in conllu ]
        
        dicts = [[self.tokenLineToDict(token) for token in sent if len(token)==10] for sent in conllu ]
        text = ""
        #for sent in conllu:
        #    for line in sent:
        #        line = line[0]
        #        mark = "# text = "
        #        if line[:len(mark)] == mark:
        #            text += line[len(mark):]
        for sent in dicts:
            for token in sent:
                text += token["form"]
                if token["space"] == "SpacesAfter=\\n":
                    text += "\n"
                elif token["space"] == "SpacesAfter=No":
                    continue
                else:
                    text += " "
                
        return {"rawText": text, "tokensWithFeatures":dicts}
        
    def write(self, data, filePath=None):
        conllLines = []
        for sent in data["tokensWithFeatures"]:
            
            for token in sent:
                line = [token[c] for c in self.columns]
                line = "\t".join(line)
                conllLines.append(line)
            conllLines.append("")
        if filePath is not None:
            with open(filePath, "w") as f:
                for line in conllLines:
                    f.write(line + "\n")
        else:
            return "\n".join(conllLines)
