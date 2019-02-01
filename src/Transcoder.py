# -*- coding: UTF-8 -*-

class Transcoder(object):
    """
    Класс для перевода из одного выбранного формата в другое
    """
    def __init__(self, reader, writer):
        """
        reader - импортер для чтения данных исходного формата из файла
        writer - экспортер для записи целевого формата в файл
        """
        self.reader = reader
        self.writer = writer   
        self.data = {}
        pass
    
    def fillDocMeta(self, data, inputFilePath):
        if "docMeta" not in data:
            data["docMeta"] = {}
        if "docName" not in data["docMeta"]:
            data["docMeta"]["docName"] = ".".join(os.path.basename(inputFilePath).split(".")[:-1])
        if "genre" not in data["docMeta"]:
            data["docMeta"]["genre"] = None
        if "partId" not in data["docMeta"]:
            data["docMeta"]["partId"] = 0
    
    def processFile(self, inputFilePath, outputFilePath):
        if self.reader == "raw":
            with open(outputFilePath, "r", encoding="utf-8") as f:
                self.data["rawText"] = f.read()
        else:
            self.data = self.reader.read(inputFilePath)

        self.fillDocMeta(self.data, inputFilePath)
        if self.writer == "raw":
            strData = self.data["rawText"]
            
        else:
            strData = self.writer.write(self.data)

        with open(outputFilePath, "w", encoding="utf-8") as f:
            f.write(strData)
        
        