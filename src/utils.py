# -*- coding: UTF-8 -*-
from copy import deepcopy
        
def mergeData(docData_1, docData_2):
    # сейчас для кореференции достаточно, но это не то, что я хотел
    mergedDoc = deepcopy(docData_1)
    for k in docData_2.keys():
        if k not in mergedDoc:
            mergedDoc[k] = docData_2[k]
    return mergedDoc

def addTokensPositions(docData):
    lastPos = 0
    for sentData in docData["sentences"]:
        for t_i, token in enumerate(sentData["tokens"]):
            token["startPos"] = lastPos
            token["endPos"] = lastPos + len(token["forma"])            
            lastPos += len(token["forma"])
            if "spaceAfter" in token:
                if token["spaceAfter"] == "_":
                    lastPos += 1
                elif token["spaceAfter"] == "No":
                    continue                
                else:
                    lastPos += len(token["spaceAfter"])
            else:
                lastPos += 1

def addTokensPositions(docData):
    lastPos = 0
    for s_i, sentData in enumerate(docData["sentences"]):
        for t_i, token in enumerate(sentData["tokens"]):
            pos = docData["raw"].find(token["forma"], lastPos)
            if pos != -1:
                lastPos = pos
            else:
                # фикс специально для ontonotes, 
                # там разделение идёт по пробелам, поэтому в токенах их не должно быть
                # поэтому я иногда их заменял на _, но для поиска позиций надо их вернуть на место
                token["forma"] = token["forma"].replace("_", " ")
                pos = docData["raw"].find(token["forma"], lastPos)
                if pos == -1:
                    # если токен все равно не был найден, например это тэг [CLS] из берта
                    token["startPos"] = -1
                    token["endPos"] = -1
                    continue
                else:
                    lastPos = pos
            token["startPos"] = lastPos
            token["endPos"] = lastPos + len(token["forma"])
            lastPos += len(token["forma"])
            #print(s_i, t_i,lastPos,  token["forma"], token["startPos"], token["endPos"])


wrongBounds = 0
goodBounds = 0
totalMentions = 0
def projectCorefPosToTokens(docData):
    global wrongBounds, goodBounds, totalMentions
    for mention in docData["coreference"]["mentions"]:
        totalMentions += 1
        tokenIdx = 0
        mention["startToken"], mention["endToken"] = -999, -999
        for sentence in docData["sentences"]:
            for t_i, token in enumerate(sentence["tokens"]):
                
                if token["startPos"]==mention["startPos"]:
                    mention["startToken"] = tokenIdx
                    goodBounds += 1
                if token["endPos"]==mention["endPos"]:
                    mention["endToken"] = tokenIdx
                    goodBounds += 1
                #if mention["startToken"] == -999:
                if token["startPos"] < mention["startPos"] and token["endPos"] > mention["startPos"]:
                    mention["startToken"] = tokenIdx
                    #wrongBounds += 1
                elif token["startPos"] > mention["startPos"] and mention["startToken"] == -999:
                    mention["startToken"] = tokenIdx
                    #wrongBounds += 1
                #if mention["endToken"] not in mention:
                #if mention["endToken"] == -999:
                if token["endPos"] > mention["endPos"] and token["startPos"] < mention["endPos"]:
                    mention["endToken"] = tokenIdx
                    #wrongBounds += 1
                elif token["endPos"] < mention["endPos"] and sentence["tokens"][min(len(sentence["tokens"])-1, t_i+1)]["startPos"]>mention["endPos"]:
                    mention["endToken"] = tokenIdx
                elif token["endPos"] < mention["endPos"] and tokenIdx > mention["endToken"]:
                    mention["endToken"] = tokenIdx
                    #wrongBounds += 1
                tokenIdx += 1
        if (mention["startToken"] == -999) or (mention["endToken"] == -999):
            raise ValueError("Can't find border token for mention:\n{}".format(mention))

def projectCorefTokensToPos(docData):
    for mention in docData["coreference"]["mentions"]:
        #totalMentions += 1
        tokenIdx = 0
        for sentence in docData["sentences"]:
            for token in sentence["tokens"]:
                if tokenIdx == mention["startToken"]:
                    mention["startPos"] = token["startPos"]
                if tokenIdx == mention["endToken"]:
                    mention["endPos"] = token["endPos"]
                if "startPos" in mention and "endPos" in mention:
                    break
                tokenIdx += 1
            if "startPos" in mention and "endPos" in mention:
                break
        if "startPos" not in mention or "endPos" not in mention:
            raise ValueError("Can't find border positions for mention:\n{}".format(mention))