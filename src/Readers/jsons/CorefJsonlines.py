# -*- coding: utf8 -*-
import re
import json
from copy import deepcopy
from collections import defaultdict

class KentonCorefJsonline(object):
    def kenton_to_sag(self, corefjson):
        sagNLP = {
            "meta": {
                "docName": corefjson["doc_key"]
            },
            "sentences": [],
            "coreference": {
                "mentions": [],
                "clusters": []
            },
            "objects": {}
        }
        # tokens features
        tokenIdx = 0
        corefjson["constituents"] = sorted(corefjson["constituents"], key=lambda x: int(x[1]), reverse=False)
        for s_i, sent in enumerate(corefjson["sentences"]):
            sagsent = []
            for t_i, token in enumerate(sent):
                tokenConst = "*"
                for const in corefjson["constituents"]:
                    if const[0]==tokenIdx:
                        tokenConst = "("+const[2]+tokenConst
                    if const[1]==tokenIdx:
                        tokenConst = tokenConst + ")"
                sagsent.append({
                    "forma": token,
                    "speaker": corefjson["speakers"][s_i][t_i],
                    "morph": corefjson["morphology"][s_i][t_i],
                    "constituent": tokenConst
                })
                
                tokenIdx += 1
            sagNLP["sentences"].append(sagsent)

        # NER
        sagNLP["objects"]["NER"] = []
        for ner in corefjson["ner"]:
            sagNLP["objects"]["NER"].append({
                "startToken": ner[0],
                "endToken": ner[1],
                "Class": ner[2]
            })
        # coreference
        for c_i, cluster in enumerate(corefjson["clusters"]):
            sagNLP["coreference"]["clusters"].append([])
            for mention in cluster:
                sagNLP["coreference"]["mentions"].append({
                    "startToken": mention[0],
                    "endToken": mention[1]
                })
                sagNLP["coreference"]["clusters"][-1].append(len(sagNLP["coreference"]["mentions"]) - 1)
                
        return sagNLP

    def sag_to_kenton(self, sagNLP):
        corefJSON = {
            'clusters': [],
            'speakers': [],
            'sentences': [],
            'constituents': [],
            'ner': [],
            'doc_key': [],
            'morphology': []
        }
        corefJSON["doc_key"] = sagNLP["meta"]["docName"]
        
        corefJSON["sentences"] = [[t["forma"] for t in sent] for sent in sagNLP["sentences"] ]
        corefJSON["speakers"] = [[t["speaker"] for t in sent] for sent in sagNLP["sentences"] ]
        corefJSON["morphology"] = [[t["morph"] for t in sent] for sent in sagNLP["sentences"] ]
        
        tokenIdx = 0    
        openedConstituents = []
        for sent in sagNLP["sentences"]:
            for token in sent:
                if token["constituent"]!="*":
                    for openConst in re.findall(r"\((\w+)", token["constituent"]):
                        openedConstituents.append([tokenIdx, openConst])
                    closedConstCount = len(re.findall(r"\)", token["constituent"]))
                    if closedConstCount>0:
                        for const in openedConstituents[-closedConstCount:]:
                            corefJSON["constituents"].append([const[0], tokenIdx, const[1]])
                        openedConstituents = openedConstituents[:-closedConstCount]
                    
                tokenIdx += 1
                
        for ner in sagNLP["objects"]["NER"]:
            corefJSON["ner"].append([ner["startToken"], ner["endToken"], ner["Class"]])
        
        for c_i, cluster in enumerate(sagNLP["coreference"]["clusters"]):
            corefJSON["clusters"].append([])
            for m_i in cluster:
                mention = sagNLP["coreference"]["mentions"][m_i]
                corefJSON["clusters"][-1].append([mention["startToken"], mention["endToken"]])
        return corefJSON


class FBCorefJsonline(object):
    def fb_to_sag(self, corefjson):
        """
        """
        sagNLP = {
            "meta": {
                "docName": corefjson["doc_key"]
            },
            "sentences": [],
            "coreference": {
                "mentions": [],
                "clusters": []
            },
            "objects": {}
        }
        # tokens features
        tokenIdx = 0
        corefjson["constituents"] = sorted(corefjson["constituents"], key=lambda x: int(x[1]), reverse=False)
        for s_i, sent in enumerate(corefjson["sentences"]):
            sagsent = []
            for t_i, token in enumerate(sent):
                tokenConst = "*"
                for const in corefjson["constituents"]:
                    if const[0]==tokenIdx:
                        tokenConst = "("+const[2]+tokenConst
                    if const[1]==tokenIdx:
                        tokenConst = tokenConst + ")"
                sagsent.append({
                    "forma": token,
                    "speaker": corefjson["speakers"][s_i][t_i],
                    "UPOS": "PRP" if tokenIdx in corefjson["pronouns"] else "",  # в этом json есть только метка pronoun
                    "constituent": tokenConst
                })
                
                tokenIdx += 1
            sagNLP["sentences"].append(sagsent)

        # NER
        sagNLP["objects"]["NER"] = []
        for ner in corefjson["ner"]:
            sagNLP["objects"]["NER"].append({
                "startToken": ner[0],
                "endToken": ner[1],
                "Class": ner[2]
            })
        # coreference
        for c_i, cluster in enumerate(corefjson["clusters"]):
            sagNLP["coreference"]["clusters"].append([])
            for mention in cluster:
                sagNLP["coreference"]["mentions"].append({
                    "startToken": mention[0],
                    "endToken": mention[1]
                })
                sagNLP["coreference"]["clusters"][-1].append(len(sagNLP["coreference"]["mentions"]) - 1)
                
        return sagNLP, corefjson['subtoken_map'], corefjson['sentence_map']

    def sag_to_fb(self, sagNLP, subtoken_map, sentence_map):
        corefJSON = {
            'clusters': [],
            'speakers': [],
            'sentences': [],
            'constituents': [],
            'ner': [],
            'doc_key': [],
            'pronouns': [],
            "subtoken_map":subtoken_map,
            "sentence_map":sentence_map,
        }
        corefJSON["doc_key"] = sagNLP["meta"]["docName"]
        
        corefJSON["sentences"] = [[t["forma"] for t in sent] for sent in sagNLP["sentences"] ]
        corefJSON["speakers"] = [[t["speaker"] for t in sent] for sent in sagNLP["sentences"] ]
        
        tokenIdx = 0    
        openedConstituents = []
        for sent in sagNLP["sentences"]:
            for token in sent:
                if token["UPOS"] in ["PRP"]:  # , "PRP$", "WP", "WP$"]:
                    corefJSON["pronouns"].append(tokenIdx)
                if token["constituent"]!="*":
                    for openConst in re.findall(r"\((\w+)", token["constituent"]):
                        openedConstituents.append([tokenIdx, openConst])
                    closedConstCount = len(re.findall(r"\)", token["constituent"]))
                    if closedConstCount>0:
                        for const in openedConstituents[-closedConstCount:]:
                            corefJSON["constituents"].append([const[0], tokenIdx, const[1]])
                        openedConstituents = openedConstituents[:-closedConstCount]
                    
                tokenIdx += 1
                
        for ner in sagNLP["objects"]["NER"]:
            corefJSON["ner"].append([ner["startToken"], ner["endToken"], ner["Class"]])
        
        for c_i, cluster in enumerate(sagNLP["coreference"]["clusters"]):
            corefJSON["clusters"].append([])
            for m_i in cluster:
                mention = sagNLP["coreference"]["mentions"][m_i]
                corefJSON["clusters"][-1].append([mention["startToken"], mention["endToken"]])
        return corefJSON

    def DeMapTokens(self, sagNLP, subtoken_map, sentence_map):
        """
        Change tokenization in SagNLP from subtokens back to tokens
        """
        sagNLP = deepcopy(sagNLP)
        newSentences = []
        subtoken_idx =  0
        prevSentIdx = 0
        prevTokenIdx = 0
        currentToken = {}
        currentSent = []
        for sent in sagNLP["sentences"]:
            for t_i, token in enumerate(sent):
                if subtoken_map[subtoken_idx] == prevTokenIdx:
                    if token["forma"] not in ["[CLS]", "[SEP]"]:
                        if token["forma"][:2] == "##":
                            currentToken["forma"] += token["forma"][2:]
                        elif t_i==1:
                            currentToken = token
                        else:
                            currentToken["forma"] += token["forma"]
                else:
                    currentSent.append(currentToken)
                    if sentence_map[subtoken_idx] != prevSentIdx:
                        newSentences.append(currentSent)
                        currentSent = []
                        prevSentIdx = sentence_map[subtoken_idx]
                    currentToken = token
                    prevTokenIdx = subtoken_map[subtoken_idx]
                subtoken_idx += 1
        currentSent.append(currentToken)
        if len(currentSent)>0:
            newSentences.append(currentSent)
        sagNLP["sentences"] = newSentences
        # fix mention token idxes
        for mention in sagNLP["coreference"]["mentions"]:
            mention["startToken"] = subtoken_map[mention["startToken"]]
            mention["endToken"] = subtoken_map[mention["endToken"]]
        return sagNLP

    def makeSubtokens(self, sagNLP, tokenizer):
        sagNLP = deepcopy(sagNLP)
        newSentences = []
        subtoken_map = []
        idxesMapping = defaultdict(list)
        token_idx, subtoken_idx = 0, 0
        for sent in sagNLP["sentences"]:
            newSentences.append([])
            for t_i, token in enumerate(sent):
                subtokens = tokenizer.tokenize(token["forma"])
                for s_i, subtoken in enumerate(subtokens):
                    newSentences[-1].append(deepcopy(token))

                    # Это хрень конечно, но для сравнения кинтоновских json с FB пришлось сделать такой костыль. Много ошибок было для "'s"  когда ' была помечена, а s нет
                    if s_i !=0:
                        if newSentences[-1][-1]["UPOS"]=="PRP":
                            newSentences[-1][-1]["UPOS"] = ""
                    newSentences[-1][-1]["forma"]=subtoken
                    subtoken_map.append(token_idx)
                    idxesMapping[token_idx].append(subtoken_idx)
                    subtoken_idx += 1
                token_idx += 1
        sagNLP["sentences"] = newSentences

        # Fix coreference
        for mention in sagNLP["coreference"]["mentions"]:
            mention["startToken"] = idxesMapping[mention["startToken"]][0]
            mention["endToken"] = idxesMapping[mention["endToken"]][-1]

        return sagNLP, subtoken_map

    def independent_segmentation(self, sagNLP, subtoken_map, segment_len):
        sagNLP = deepcopy(sagNLP)
        tokens, sent_ends, tokens_ends, sentence_map = [], [], [], []
        subtoken_idx = 0
        for s_i, sent in enumerate(sagNLP["sentences"]):
            for t_i, token in enumerate(sent):
                tokens.append(token)
                sentence_map.append(s_i)
                if t_i==(len(sent)-1):
                    sent_ends.append(True)
                    tokens_ends.append(True)
                else:
                    sent_ends.append(False)
                    if subtoken_map[subtoken_idx]==subtoken_map[subtoken_idx+1]:
                        tokens_ends.append(False)
                    else:
                        tokens_ends.append(True)                    
                subtoken_idx += 1
        lastSegmentEnd = 0
        segments, subtoken_map_segments, sentence_map_segments  = [], [], []
        while lastSegmentEnd < len(tokens):
            nextEnd = min(lastSegmentEnd + segment_len - 1 - 2, len(tokens) - 1)
            while nextEnd >= lastSegmentEnd and not sent_ends[nextEnd]:
                nextEnd -= 1
            if nextEnd < lastSegmentEnd:
                nextEnd = min(lastSegmentEnd + segment_len - 1 - 2, len(tokens) - 1)
                while nextEnd >= lastSegmentEnd and not tokens_ends[nextEnd]:
                    nextEnd -= 1
                if nextEnd < lastSegmentEnd:
                    raise Exception("Can't find valid segment")
            new_segment = tokens[lastSegmentEnd:nextEnd + 1]
            new_segment = [deepcopy(new_segment[0])] + new_segment + [deepcopy(new_segment[-1])]
            new_segment[0]["forma"] = '[CLS]'
            new_segment[0]["speaker"] = '[SPL]'    
            new_segment[0]["UPOS"] = '[SPL]'       
            new_segment[-1]["forma"] = '[SEP]'
            new_segment[-1]["speaker"] = '[SPL]'
            new_segment[-1]["UPOS"] = '[SPL]'
            segments.append(new_segment)
            #print(" ".join([t["forma"] for t in new_segment]))
            subtoken_map_segments.append(subtoken_map[max(0, lastSegmentEnd-1)])
            subtoken_map_segments.extend(subtoken_map[lastSegmentEnd : nextEnd+1])
            subtoken_map_segments.append(subtoken_map[nextEnd])
            #print(subtoken_map_segments)
            
            sentence_map_segments.append(sentence_map[lastSegmentEnd])
            sentence_map_segments.extend(sentence_map[lastSegmentEnd : nextEnd+1])
            #sentence_map_segments.append(sentence_map[nextEnd]+1)  # works for the most of examples
            if nextEnd == len(sentence_map)-1:
                sentence_map_segments.append(sentence_map[nextEnd]+1)
            else:
                sentence_map_segments.append(sentence_map[nextEnd+1])
            #print(sentence_map_segments)
            lastSegmentEnd = nextEnd + 1
            #print()
        #sentence_map_segments[-1] +=1
        sagNLP["sentences"] = segments

        # Fix mentions borders:
        idxesMapping = defaultdict(int)
        oldIdx, newIdx = 0, 0
        for sent in sagNLP["sentences"]:
            for subtoken in sent:
                idxesMapping[oldIdx] = newIdx
                newIdx += 1
                if subtoken["forma"] not in ["[CLS]", "[SEP]"]:
                    oldIdx += 1
        # Fix coreference
        for mention in sagNLP["coreference"]["mentions"]:
            mention["startToken"] = idxesMapping[mention["startToken"]]
            mention["endToken"] = idxesMapping[mention["endToken"]]

        return sagNLP, subtoken_map_segments, sentence_map_segments

class CorefJsonCollection_old(object):
    def __init__(self):
        
        self.annotationLayers = ["speakers", "constituents", "morphology", "clusters", "doc_key", "sentences", "ner"]
        self.defaultVals = {
            "speaker": "_",
            "morphology": "_",
            "form": "_",
        }
        pass

    def read(self, filePath, predicted=False):
        # надо еще нёр и парсинг восстанавливать
        with open(filePath, "r", encoding="utf-8") as f:
            jsonlines = f.readlines()
        collectionData = []
        for line in jsonlines:
            docData = {"meta" : {}, "sentences": [], "coreference": {"clusters":[], "mentions": []}}
            docJson = json.loads(line)
            docData["meta"]["docName"] = docJson["doc_key"]
            for s_i in range(len(docJson["sentences"])):
                sentenceData = {"tokens":[]}
                for t_i in range(len(docJson["sentences"][s_i])):
                    tokenData = {}                    
                    tokenData["form"] = docJson["sentences"][s_i][t_i]
                    tokenData["speaker"] = docJson["speakers"][s_i][t_i]
                    if "morphology" in docJson:
                        tokenData["morph"] = docJson["morphology"][s_i][t_i]
                    sentenceData["tokens"].append(tokenData)
                docData["sentences"].append(sentenceData)

            for cluster in docJson["clusters"] if not predicted else docJson["predicted_clusters"]:
                clusterMentions = []
                for mention in cluster:
                    mentionData = {"startToken":mention[0], "endToken": mention[1]}
                    if mentionData in docData["coreference"]["mentions"]:
                        clusterMentions.append(docData["coreference"]["mentions"].index(mentionData))
                    else:
                        docData["coreference"]["mentions"].append(mentionData)
                        clusterMentions.append(len(docData["coreference"]["mentions"]) -1)
                docData["coreference"]["clusters"].append(clusterMentions)
            collectionData.append(docData)
        return collectionData

    def write(self, collectionData, filePath=None):
        jsonlines = []
        for docData in collectionData:
            documentJson = {}
            for layer in self.annotationLayers:
                documentJson[layer] = []
            if "genre" in docData["meta"]:
                documentJson["doc_key"] = docData["meta"]["genre"][:2] + "/" + docData["meta"]["fileName"]
            else:
                documentJson["doc_key"] = docData["meta"]["fileName"]
            documentJson["constituents"] = []
            for sentence in docData["sentences"]:
                documentJson["constituents"].append([-1, -1, "TOP"])  # я хз, что это
                documentJson["speakers"].append([])
                documentJson["morphology"].append([])
                documentJson["sentences"].append([])
                for token in sentence['tokens']:
                    documentJson["speakers"][-1].append(token.get("speaker", self.defaultVals["speaker"]))
                    documentJson["morphology"][-1].append(token.get("morph", self.defaultVals["morphology"]))
                    documentJson["sentences"][-1].append(token.get("form", self.defaultVals["form"]))
            documentJson["clusters"] = []
            for cluster in docData["coreference"]["clusters"]:
                documentJson["clusters"].append([])
                for m_i in cluster:
                    mentionsTokens = [-1, -1]
                    mentionsTokens[0] = docData["coreference"]["mentions"][m_i]["startToken"]
                    mentionsTokens[1] = docData["coreference"]["mentions"][m_i]["endToken"]
                    documentJson["clusters"][-1].append(mentionsTokens)
            jsonlines.append(json.dumps(documentJson))
        if filePath is not None:
            with open(filePath, "w", encoding="utf-8") as f:
                for line in jsonlines:
                    f.write(line + "\n")
