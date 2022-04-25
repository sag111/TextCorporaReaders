# -*- coding: utf8 -*-

# http://conll.cemantix.org/2012/data.html

# http://conll.cemantix.org/2012/data.html
import os
import re
from collections import deque

# надо бы id токена переименовать на idInSent и idInText
class OntoNotesReader(object):
    """
    Класс для работы с форматом OntoNotes
    """
    def __init__(self):
        self.columns = ["docName", "partId", "id", "form", "upos", "parseBit",
                        "lemma", "frameset", "sense", "speaker", "NER", "PredicateArguments" "coreference"] # "predicateArgs"
        self.defaultColumnValues = [None, 0, 0, "", "-", "*", "-", "-", "-", "-", "*", "-"]
        self.defaultValues = {"partId": 0, "frameset": "-", "NER": "*", "speaker": "-", "sense": "-"}
        pass
    
    def tokenLineToDict(self, tokenLine):
        d = {}
        d["id"] = tokenLine[2]
        d["form"] = tokenLine[3]
        d["upos"] = tokenLine[4]
        d["xpos"] = "_"
        d["parseBit"] = tokenLine[5]
        d["lemma"] = tokenLine[6]
        d["frameset"] = tokenLine[7]
        d["sense"] = tokenLine[8]
        d["speaker"] = tokenLine[9]
        d["NER"] = tokenLine[10]
        d["PredicateArguments"] = tokenLine[11:-1]
        d["coreference"] = tokenLine[-1]
        return d

    def fixForm(self, form):
        form = form.replace(" ", "_")
        form = form.replace("(", "-LBR-")  # костыли
        form = form.replace(")", "-RBR-")  # костыли
        return form

    def tokenDictToLine(self, tokenIdxInDoc, tokenDict, docData):
        line = []
        line.append(docData["meta"]["docName"])
        line.append(docData["meta"]["partId"])

        line.append(tokenDict["id"])
        line.append(self.fixForm(tokenDict["form"]))
        line.append(tokenDict["upos"].replace(" ", ":"))
        line.append(tokenDict["parseBit"])
        line.append(self.fixForm(tokenDict["lemma"]))
        line.append(tokenDict.get("frameset", self.defaultValues["frameset"]))
        line.append(tokenDict.get("sense", self.defaultValues["sense"]))
        line.append(tokenDict.get("speaker", self.defaultValues["speaker"]))
        line.append(tokenDict.get("NER", self.defaultValues["NER"]))
        
        if "PredicateArguments" in tokenDict:
            for predicArg in tokenDict["PredicateArguments"]:
                line.append(predicArg)
        coreferenceMarks = []
        startOfmentions = []
        endOfMentions = []
        wholeMention = None
        for m_i, mention in enumerate(docData['coreference']["mentions"]):
            if tokenIdxInDoc == mention["startToken"] and tokenIdxInDoc == mention["endToken"]:
                wholeMention = m_i
                #print("wholeMention", wholeMention)
            elif tokenIdxInDoc == mention["startToken"]:
                startOfmentions.append(m_i)
            elif tokenIdxInDoc == mention["endToken"]:
                endOfMentions.append(m_i)
        for cl_i, cluster in enumerate(docData['coreference']["clusters"]):
            if (wholeMention is not None) and (wholeMention in cluster):
                #print("wholeMention2", wholeMention)
                #print(cluster)              
                coreferenceMarks.append("({})".format(cl_i))
            for mention in startOfmentions:
                if mention in cluster:
                    coreferenceMarks.append("({}".format(cl_i))
            for mention in endOfMentions:
                if mention in cluster:
                    coreferenceMarks.append("{})".format(cl_i))
        
        if len(coreferenceMarks) > 0 :
            coreferenceMarks = "|".join(coreferenceMarks)
        else:
            coreferenceMarks = "-"
        line.append(coreferenceMarks)

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
                    #if len(sent)==1:
                    if t_i==0 and t_i==len(sent["tokens"])-1: 
                        token["parseBit"] = "(TOP*)"
                    elif t_i==0:
                        token["parseBit"] = "(TOP*"
                    elif t_i==len(sent["tokens"])-1:
                        token["parseBit"] = "*)"
                    else:
                        token["parseBit"] = "*"
    
    def tokensToPositions():
        pass
    
    def writeCollection(self, collectionData, outFile=None):
        collectionString = ""
        for docData in collectionData:
            collectionString += "#begin document ({}); part {:03d}\n".format(docData["meta"]["docName"], docData["meta"]["partId"])
            #tokenIdxInDoc = 1  # костыль
            tokenIdxInDoc = 0  # так, тут надо разобраться, в одних документах надо начинать с 1, в других с 0
            self.checkFixParse(docData["sentences"])
            for sentenceData in docData["sentences"]:
                for token in sentenceData["tokens"]:
                    collectionString += self.tokenDictToLine(tokenIdxInDoc, token, docData) + "\n"
                    tokenIdxInDoc += 1
                collectionString += "\n"
            collectionString += "#end document\n"
        
        if outFile is not None:
            with open(outFile, "w", encoding="utf-8") as f:
                f.write(collectionString)
        else:
            return strData
    
    def parseTokenCoreferenceMark(self, tokenInTextId, token_d, coreference_data, openedMentions, mentionsInFile):
        if token_d["coreference"] != "-":
            tokenClusters = token_d["coreference"].split("|")
            for mentionMark in tokenClusters:
                clusterId = int(re.search("\d+", mentionMark).group())
                # в корпусе conll были такие ситуации: (71 ... (71 ... 71) ... 71)
                # сущность внутри сущности того же кластера
                # я предположил, что первое что открывается закрывается последним
                if mentionMark[0]=="(":
                    if clusterId not in openedMentions:
                        openedMentions[clusterId] = deque()
                    newOpenedMention = {"startToken": tokenInTextId}
                    openedMentions[clusterId].append(newOpenedMention)
                if mentionMark[-1]==")":
                    if clusterId not in openedMentions:
                        raise ValueError("Closing mentions wasn't open")
                    mentionToClose = openedMentions[clusterId].pop()
                    mentionToClose["endToken"] = tokenInTextId
                    if clusterId not in mentionsInFile:
                        mentionsInFile[clusterId] = []
                    mentionsInFile[clusterId].append(mentionToClose)
                
    
    def readCollection(self, filePath):
        with open(filePath, "r", encoding="utf8") as f:
            collectionTable = f.read()
        collectionData = []
        for docTable in re.findall("(#begin document(.+\n\n?)+?#end document)", collectionTable, re.U|re.M):
            docData = {"raw":"", "meta":{}, "sentences":[]}
            docTable = docTable[0]
            docTable = [[tokenLine for tokenLine in sentenceTable.split("\n")] for sentenceTable in docTable.split("\n\n")]
            coreference_data = {"clusters":[], "mentions":[]}
            mentionsInFile = {}
            openedMentions = {}
            tokenIdx = 0
            endOfDoc = False
            for sentence in docTable:
                sentenceData = {"raw":"", "meta":{}, "tokens":[]}
                for tokenLine in sentence:
                    if "#begin document" in tokenLine:
                        docNameMO = re.search("#begin document \(([^)]+)\); part (\d+)", tokenLine)
                        docData["meta"]["docName"] = docNameMO.group(1)
                        docData["meta"]["partId"] = int(docNameMO.group(2))
                    elif "#end document" in tokenLine:
                        endOfDoc = True
                        break
                    else:
                        tokenLine = re.findall("\S+", tokenLine, re.U)
                        if len(tokenLine) < 12:
                            raise ValueError("Token line with small amount of columns:{}".format(tokenLine))
                        token_d = self.tokenLineToDict(tokenLine)
                        try:
                            self.parseTokenCoreferenceMark(tokenIdx, token_d, coreference_data, openedMentions, mentionsInFile)
                        except Exception as ve:
                            print("\n".join(sentence))
                            raise ve
                        sentenceData["tokens"].append(token_d)
                        tokenIdx += 1
                if not(endOfDoc and len(sentenceData["tokens"])==0):
                    docData["sentences"].append(sentenceData)
            
            # check if there is not closed mentions
            for clusterId in openedMentions:
                if len(openedMentions[clusterId]) > 0:
                    raise ValueError("mention wasn't closed: {}".format(openedMentions[clusterId]))
            for clusterId in sorted(mentionsInFile.keys()):
                # в файле может быть своя нумерация кластеров, не по порядку,и начинаться с произвольного номера
                # поэтому надо бы добавить пустые кластеры, чтоб её сохранить
                while len(coreference_data["clusters"]) <= (clusterId):
                    coreference_data["clusters"].append([])
                for mention in mentionsInFile[clusterId]:
                    if mention in coreference_data['mentions']:
                        coreference_data["clusters"][-1].append(coreference_data['mentions'].index(mention))
                    else:
                        coreference_data['mentions'].append(mention)
                        coreference_data["clusters"][-1].append(len(coreference_data['mentions']) - 1)
            docData["coreference"] = coreference_data
            collectionData.append(docData)
            #break
        
        return collectionData
