import sublime, sublime_plugin
import os
import shutil

storeFileName = "mthuylocalsync"
storeDirName  = ".mthuylocalsync"

class MThuyLocalSyncAfterSave(sublime_plugin.EventListener):
    def on_post_save(self, view):
        global storeFileName
        global storeDirName
        home = os.path.expanduser("~");
        storeDir = os.path.join(home, storeDirName)
        if (not os.path.exists(storeDir)):
            return 0

        storeFile = os.path.join(storeDir, storeFileName)
        if (not os.path.exists(storeFile)):
            return 0

        currentPath = view.file_name()
        splitPath   = os.path.split(currentPath)
        currentDir  = splitPath[0]
        fileName    = splitPath[1]
        file = open(storeFile, "r")
        lines = file.read().splitlines()
        file.close()

        # loop for all lines
        for line in lines:
            splitPaths     = line.split("::")
            sourceDir      = splitPaths.pop(0)
            destinationDir = splitPaths.pop(0)

            indexFound = currentDir.find(sourceDir)

            if (indexFound != 0):
                # the curent file is not in source dir so we don't need to sync
                continue

            if (currentDir == sourceDir):
                if (not os.path.isdir(destinationDir)):
                    continue
                destinationPath = os.path.join(destinationDir, fileName)
                if (os.path.exists(destinationPath)):
                    self.makeBackup(destinationPath)
                
                shutil.copy(currentPath, destinationPath)
                print("MThuyLocalSync - file copied to: " + destinationPath)
            else:
                if (len(currentDir) > len(sourceDir)):
                    diffPath = os.path.relpath(currentDir, sourceDir)
                    subDestinationDir = os.path.join(destinationDir, diffPath)
                    if (not os.path.isdir(subDestinationDir)):
                        os.makedirs(subDestinationDir)
                    subDestinationPath = os.path.join(subDestinationDir, fileName)
                    self.makeBackup(subDestinationPath)
                    shutil.copy(currentPath, subDestinationPath)
                    print("MThuyLocalSync - file copied to: " + subDestinationPath)


    def makeBackup(self, filePath):
        fileLimit = 3

        splitPath   = os.path.split(filePath)
        fileDir     = splitPath[0]
        fileName    = splitPath[1]

        #loop form 3 down to 1 to create backup
        for i in range(fileLimit, 0, -1):
            newBackupFileName = fileName + "." + str(i)
            newBackupFilePath = os.path.join(fileDir, newBackupFileName)
            if (i == fileLimit):
                if (os.path.exists(newBackupFilePath)):
                    os.remove(newBackupFilePath)

            if (i == 1):
                previousBackupFileName = fileName
            else:
                previousBackupFileName = fileName + "." + str(i - 1)

            previousBackupFilePath  = os.path.join(fileDir, previousBackupFileName)
            if (os.path.exists(previousBackupFilePath)):
                print("MThuyLocalSync move backup: " + previousBackupFilePath + " > " + newBackupFilePath)
                os.rename(previousBackupFilePath, newBackupFilePath)

#class for m_thuy_local_sync_add command in Side Bar.sublime-menu
class MThuyLocalSyncAddCommand(sublime_plugin.WindowCommand):
    
    def run(self, paths = [], new = False):
        import functools
        currentPath = paths[0]
        existingPath = self.checkPathIsEnabledSync(currentPath)
        self.window.show_input_panel("Path to sync to:", existingPath, functools.partial(self.on_done, currentPath), None, None)
        return 1

    def on_done(self, selectedPath, syncDestinationPath):
        # syncDestinationPath is take from user input
        
        global storeFileName
        global storeDirName

        lineToWrite = selectedPath + "::" + syncDestinationPath
        linesToWrite = []
        home = os.path.expanduser("~");
        storeDir = os.path.join(home, storeDirName)
        if (not os.path.exists(storeDir)):
            os.mkdir(storeDir)

        storeFile = os.path.join(storeDir, storeFileName)
        if (os.path.exists(storeFile)):
            file = open(storeFile, "r")
            linesToWrite = file.read().splitlines()
            isReplaceExistingLine = False
            if len(linesToWrite): 
                # for loop each line in file
                for lineIndex,line in enumerate(linesToWrite):
                    pathsInLine = line.split("::")
                    if (pathsInLine[0] == selectedPath):
                        isReplaceExistingLine = True
                        if (syncDestinationPath == ""):
                            # if syncDestinationPath path is blank then remove selected path to sync list
                            linesToWrite.pop(lineIndex)
                        else:
                            linesToWrite[lineIndex] = lineToWrite
                        
                        # break for
                        break
                        

            if (isReplaceExistingLine == False and syncDestinationPath != ""):
                linesToWrite.append(lineToWrite)

            file.close()
        else:
            if (syncDestinationPath == ""):
                return 0

            linesToWrite.append(lineToWrite)

        
        file = open(storeFile, "w")
        if len(linesToWrite):
            for lineIndex,line in enumerate(linesToWrite):
                # append new line for all line except last line
                if (lineIndex != (len(linesToWrite) - 1)):
                    line = line + "\n"
                file.write(line)
        else:
            file.write("")

        file.close()
        return 1

    def checkPathIsEnabledSync(self, pathToCheck):
        global storeFileName
        global storeDirName
        home = os.path.expanduser("~");
        storeDir = os.path.join(home, storeDirName)
        if (not os.path.exists(storeDir)):
            return ""

        storeFile = os.path.join(storeDir, storeFileName)
        if (not os.path.exists(storeFile)):
            return ""

        file = open(storeFile, "r")
        lines = file.read().splitlines()
        file.close()
        for line in lines:
            pathsInLine = line.split("::")
            if (pathsInLine[0] == pathToCheck):
                # remove first path because it is selected path
                # only need put sync to path
                pathsInLine.pop(0)
                return "::".join(pathsInLine)
        return ""

    def is_enabled(self, paths = []):
        if (len(paths) != 1):
            return False

        if (os.path.isdir(paths[0]) != True):
            return False

        return True