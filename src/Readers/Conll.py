# -*- coding: utf8 -*-

class CoNLLUReader(object):
    """
    Класс для работы с форматом Conll-u
    """
    def __init__(self):
        pass
    
    def tokenLineToDict(self, tokenLine):
        d = {}
        d["tokenId"] = tokenLine[0]
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
        
    def write(self, filePath):
        raise Exception("Not implemented")