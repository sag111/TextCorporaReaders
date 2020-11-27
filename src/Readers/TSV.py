# -*- coding: utf8 -*-
import os
import re

COLUMNS_CONLL = ["id", "form", "lemma", "upos", "xpos", "morph", "head", "deprel", "deps", "spaceAfter"]
DTYPES_CONLL = {"id": int, "head": int}

class TSVReader(object):
    """
    Класс для работы с форматом tab separated values
    В одном файле может быть несколько текстов
    Тексты начинаются с комментария #
    Предложения разделены пустой строкой
    Каждая строка - токен, признаки токена разделены табуляцией
    """
    def __init__(self, columns, dtypes):
        self.columns = columns
        self.dtypes = dtypes
        pass
    
    def tokenLineToDict(self, tokenLine):
        """
        Преобразование строки токена в словарь
        """
        d = {}
        for c_i, c in enumerate(self.columns):
            if c=="spaceAfter":
                # в колонке отвечающей за то, какой непечатный символ следует за словом
                # оставляю только сам символ и заменяю их экранированные варианты на сам символ
                tokenLine[c_i] = re.sub("Spaces?After=", "", tokenLine[c_i], re.U)
                # с этим какая-то проблема была, не помню, приходилось убирать возвращение каретки
                tokenLine[c_i] = tokenLine[c_i].replace("\\r\\n", "\n")
                tokenLine[c_i] = tokenLine[c_i].replace("\\n", "\n")
                tokenLine[c_i] = tokenLine[c_i].replace("\\s", " ")
            if self.dtypes.get(c, None) == int:
                d[c] = int(tokenLine[c_i])
            else:
                d[c] = tokenLine[c_i]            
        return d
    
    def tokenDictToLine(self, tokenDict):
        """
        Преобразование словаря с описанием токена в строку с табуляцией
        """
        if "spaceAfter" in tokenDict and tokenDict["spaceAfter"] !="_":
            # заменяем обратно непечатные символы на экранированные варианты
            tokenDict["spaceAfter"] = tokenDict["spaceAfter"].replace("\n", "\\n")
            tokenDict["spaceAfter"] = tokenDict["spaceAfter"].replace(" ", "\\s")
            if tokenDict["spaceAfter"]=="No":
                tokenDict["spaceAfter"] = "SpaceAfter="+tokenDict["spaceAfter"]
            else:
                tokenDict["spaceAfter"] = "SpacesAfter="+tokenDict["spaceAfter"]
        line = [str(tokenDict[c]) for c in self.columns]
        line = "\t".join(line)
        return line
    
    def read(self, conllu, docName):
        """
        Чтение файла
        Parameters:
            filePath - путь к файлу
        Returns:
            dict - считанный корпус или текст в формате sagnlpJSON
        """        

        # удалить все новые строки в конце файла
        #conllu = conllu[:-2]  # потому что в конце conllu \n\n
        conllu = re.sub("\n+$", "", conllu)
        conllu = conllu.split("\n\n")
        conllu = [x.split("\n") for x in conllu]
        conllu = [[token.strip().split("\t") for token in sent] for sent in conllu ]
        
        #dicts = [[self.tokenLineToDict(token) for token in sent if len(token)==10] for sent in conllu ]
        text = {"raw":"", "meta":{}, "sentences": [], "paragraphs": []}
        text["meta"]["fileName"] = docName
        rawText = ""
        for s_i, sent in enumerate(conllu):
            sentence_d = {"raw":"", "meta":{}, "tokens":[]}
            for t_i, token in enumerate(sent):
                token_d = {}
                if len(token) != len(self.columns):
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
                        raise ValueError("Wierd token {} in sent {} with len less then {}:\n{}".format(t_i, s_i, len(self.columns), token))
                token_d = self.tokenLineToDict(token)
                
                sentence_d["tokens"].append(token_d)
                
                rawText += token_d["form"]
                if token_d.get("spaceAfter", "_") == "_":
                    rawText += " "
                elif token_d["spaceAfter"] == "No":
                    continue
                else:
                    rawText += token_d["spaceAfter"]
            text["sentences"].append(sentence_d)

        text["raw"] = rawText
        return text
        
    def read_file(self, filePath):
        with open(filePath, "r", encoding="utf-8") as f:
            conllu = f.read()
        docData = self.read(conllu, os.path.basename(filePath))
        return docData

    def write(self, data, filePath=None):
        conllLines = []
        if "id" in data["meta"]:
            conllLines.append("# newdoc id = {}".format(data["meta"]["id"]))
        for s_i, sentence_d in enumerate(data["sentences"]):
            if s_i in data["paragraphs"]:
                conllLines.append("# newpar")
            if "id" in sentence_d["meta"]:
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
