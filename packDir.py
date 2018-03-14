import os
import zipfile

def zipDirectory(packFileName,path):
	zipName = packFileName + '_tmp.zip'
	packPath = path + os.path.sep + packFileName
	zipPath = path + os.sep + zipName
	f = zipfile.ZipFile(zipPath,'w',zipfile.ZIP_DEFLATED)
	pre_len = len(os.path.dirname(packPath))
	for folderName,subFolderNames,fileNames in os.walk(packPath):
		f.write(folderName,folderName[pre_len:])
		for fileName in fileNames:
			filePath = os.path.join(folderName,fileName)
			relativePath = filePath[pre_len:].strip(os.path.sep)
			f.write(filePath,relativePath)
	f.close()
	return zipName

def unzipDirectory(currentPath,unzipName):
	zipPath = currentPath + os.path.sep + unzipName
	#print(zipPath)#test
	z = zipfile.ZipFile(zipPath)
	z.extractall(currentPath)
	z.close()
	
