#AC typeTranslate test

import pandas as pd

from specklepy.api.wrapper import StreamWrapper
from specklepy.api.client import SpeckleClient
from specklepy.api import operations

from specklepy.objects import Base
from specklepy.objects.other import Collection
from specklepy.objects.geometry import Mesh
from specklepy.objects.other import RenderMaterial

from flatten import flatten_base

######conversion DICT hard coded

cTable = {
    "Zone":"_Curves",
    "Wall":"_Walls_50",
    "Column":"_Columns_50",
    "Slab":"_Floors_20",
    "Stair":"_Stairs_20",
    "Ceiling":"_Ceilings_70",
    "Roof":"_Roof_20",
    "Railing":"_Railings_20",
    "Mesh":"_Ground_20",
    "Morph":"_Context_30",
    "CurtainWall":"_CurtainWall",
    "Window":"_Windows",
    "Door":"_Door"
    }


#####Functions here#######
#Send to stream
def SendDL(DL_modell, Stream, source):
    #sWrap = StreamWrapper ("https://multiconsult.speckle.xyz/projects/8c1aca44f6")
    sWrap = StreamWrapper (Stream)
    #sourceWrap = StreamWrapper(source)
    sTransport = sWrap.get_transport()
    sClient = sWrap.get_client()
    dStream = sClient.stream.get(sWrap.stream_id)

    if "daylight_models" in [i.name for i in dStream.branches.items]:
        dl_branch = sClient.branch.get(sWrap.stream_id,"daylight_models", 1)
        print (dl_branch.name)
    else:
        dl_branchID = sClient.branch.create(dStream.id ,"daylight_models",f"AC2Daylight via Python")
        print(dl_branchID + " created!")    
    sendID = operations.send(DL_modell, [sTransport])
    sClient.commit.create(sWrap.stream_id, sendID, branch_name="daylight_models",  message= f"daylight model source:{source}" )

def stripString(string):
    noSpaces = string.replace(" ", "")
    return noSpaces

def dupeStream(source, target = "https://multiconsult.speckle.xyz/projects/8c1aca44f6"):



    #receive source
    SarehACurl = source
    dupWrapper = StreamWrapper(SarehACurl)
    dupClient = dupWrapper.get_client()
    dupTrans = dupWrapper.get_transport()
    dupComm = dupClient.commit.get(dupWrapper.stream_id, dupWrapper.commit_id)
    dupObj = operations.receive(dupComm.referencedObject, dupTrans)

    #send copy of Stream
    sWrap = StreamWrapper (target)

    sTransport = sWrap.get_transport()
    sClient = sWrap.get_client()

    sendID = operations.send(dupObj, [sTransport])
    sClient.commit.create(sWrap.stream_id, sendID, message= f"duppped from soruce: {source}")

    print ("DUP COMPLETE")

    return
  
def createUstrings(obj,list = ["level", "type", "layer", "height", "width", "thickness", "room", "lengh", "area", "name", "number","nummer","elemenetType"]):

    ###Attempt to add specific attributes as user strings 

    #list = ["level", "layer", "height", "thickness", "room", "lengh", "area", "name", "number","elemenetType"]
    #obj.userStrings = Base( level = obj.level.name, layer = str(obj.layer), applicationId = str(obj.applicationId), height = str(obj.height), thickness = str(obj.thickness), elementType = obj.elementType)
    userStrings = Base (appID = str(obj.applicationId), speckleType = str(obj.speckle_type))

    for i in list:
        if hasattr(obj,i) == True:
            if type(obj[i]) != type(Base()):
                userStrings[i] = str(obj[i])
            else:
                userStrings[i] = obj[i].name
    return userStrings

def getChildrenGlass(input):
    #get children elements from BaseObject
    #Takes Collection
    subEle = {}
    returnThis = {"ALT1":subEle, "ALT2":[]}

      
    if type(input) == Collection:
        objList = input.elements
        isCol = True
    elif type(input) != list:
        objList = [input]
    else:
        objList = input

    for obj in objList:
        if "elements" in obj.get_member_names() and obj.elements is not None:
            for j in obj.elements:
                
                parentStrings = createUstrings(j)
                
                if (j.elementType in cTable.keys()) and (cTable[j.elementType] not in [col.name for col in dl_Inputs]) and (j.displayValue is not None) :
                    for dMesh in j.displayValue:
                        dMesh.userStrings = parentStrings
                        ###ALT1: adding each dValue mesh at a time as a new object in collection elements. Worth trying to separate into one object for Solids and one Object for Glass?
                        if dMesh.renderMaterial.opacity < 1 and (cTable[stripString(j.elementType)] + ">Glass_70%") not in subEle.keys():
                            subEle[cTable[stripString(j.elementType)] + ">Glass_70%"] = (Collection(name = j.elementType + ">Glass_70%", elements = [dMesh], collectionType = "layer"))

                        elif dMesh.renderMaterial.opacity < 1 and (cTable[stripString(j.elementType)] + ">Glass_70%") in subEle.keys():
                            subEle[cTable[stripString(j.elementType)] + ">Glass_70%"].elements.append(dMesh)

                        elif dMesh.renderMaterial.opacity == 1 and (cTable[stripString(j.elementType)] + ">Solid_50") not in subEle.keys():
                            subEle[cTable[stripString(j.elementType)] + ">Solid_50"] = (Collection(name = j.elementType + ">Solid_50", elements = [dMesh], collectionType = "layer"))
                        
                        elif dMesh.renderMaterial.opacity == 1 and (cTable[stripString(j.elementType)] + ">Solid_50") in subEle.keys():
                            subEle[cTable[stripString(j.elementType)] + ">Solid_50"].elements.append(dMesh)

                        ###ALT2: Create dValueSolid base with all the opaque meshes and dValueGlass with all the transparent meshes
                        if dMesh.renderMaterial.opacity == 1:
                            if "dValueSolid" in j.get_member_names():
                                j.dValueSolid.append(dMesh)
                            else:
                                j.dValueSolid = [dMesh]
                        if dMesh.renderMaterial.opacity <1:
                            if "dValueGlass" in j.get_member_names():
                                j.dValueGlass.append(dMesh)
                            else:
                                j.dValueGlass = [dMesh]
                                
                returnThis["ALT2"].append(j)

    return returnThis

def getChildren(input):
    #get children elements from Base() / list of Base() / collection of Base()
    #returns one list
    subEle = {}
    returnThis = []

      
    if type(input) == Collection:
        objList = input.elements
        isCol = True
    elif type(input) != list:
        objList = [input]
    else:
        objList = input

    for obj in objList:
        if "elements" in obj.get_member_names() and obj.elements is not None:
            returnThis.extend(obj.elements)
            """for j in obj.elements:
                
                parentStrings = createUstrings(j)
                if (j.elementType in cTable.keys()) and (cTable[j.elementType] not in [col.name for col in dl_Inputs]) and (j.displayValue is not None) :
                    for dMesh in j.displayValue:
                        dMesh.userStrings = parentStrings
                        ###ALT1: adding each dValue mesh at a time as a new object in collection elements."""
    return returnThis        

def findGlass(input):

    #Takes Collection, List of Base() or Base()
    #format input to list
    if type(input) == Collection:
        objList = input.elements
        isCol = True
    elif type(input) != list:
        objList = [input]
    else:
        objList = input

    #Separate displayMeshes by opacity
    subEle = {}
    for j in objList:
        parentStrings = createUstrings(j)
            
        eleType = stripString(j.elementType)

        if (eleType in cTable.keys()) and (j.displayValue is not None) :
            #colList = [col.name for col in dl_Inputs]

            #if (cTable[eleType] in colList):

                #index = colList.index(cTable[eleType])
                #dl_Inputs.pop(index)

            for dMesh in j.displayValue:
                dMesh.userStrings = parentStrings
                
                
                ###ALT1: adding each dValue mesh at a time as a new object in collection elements. Worth trying to separate into one object for Solids and one Object for Glass?
                if dMesh.renderMaterial.opacity < 1 and (cTable[eleType] + ">Glass_70%") not in subEle.keys():
                    subEle[cTable[eleType] + ">Glass_70%"] = (Collection(name = cTable[eleType] + ">Glass_70%", elements = [dMesh], collectionType = "layer"))

                elif dMesh.renderMaterial.opacity < 1 and (cTable[eleType] + ">Glass_70%") in subEle.keys():
                    subEle[cTable[eleType] + ">Glass_70%"].elements.append(dMesh)

                elif dMesh.renderMaterial.opacity == 1 and (cTable[eleType] + ">Solid_50") not in subEle.keys():
                    subEle[cTable[eleType] + ">Solid_50"] = (Collection(name = cTable[eleType] + ">Solid_50", elements = [dMesh], collectionType = "layer"))
                
                elif dMesh.renderMaterial.opacity == 1 and (cTable[eleType] + ">Solid_50") in subEle.keys():
                    subEle[cTable[eleType] + ">Solid_50"].elements.append(dMesh)

    return subEle

def filterCeilings(inputCollection):

    itakList = []
    slabList = []
    keywords = ["innertak","undertak"]
    if type(inputCollection) == Collection:
        objList = inputCollection.elements
        isCol = True
    elif type(inputCollection) != list:
        objList = [inputCollection]
    else:
        objList = inputCollection

    for i in objList:
        layername = i.layer.lower()
        if any( x in i.layer.lower() for x in keywords) or i.thickness<0.05:
            itakList.append(i)
            
        else:
            slabList.append(i)
    slabCol = Collection(name = "_Floors_20", elements = slabList, collectionType = "layer")
    if itakList != []:
        ceilingCol = Collection(name="_Ceilings_70", elements = itakList, collectionType = "layer")
        return {
                "Floors":slabCol,
                "Ceilings":ceilingCol
                }
    else:
        return {"Floors":slabCol}
    

def genDaylightModel(CommitData):

    AC_Collections = CommitData

    ###Reverse engineer empty Commit structure from rhino stream // GLOBALS

    DL_modell = Collection(name = "DaylightModel", elements = [], collectionType = "Daylight Model")
    DL_modell.elements.append(Collection(name = "Daylight_Inputs", elements = [], collectionType = "Layer",))
    dl_Inputs = DL_modell.elements[0].elements

    ###Filter geometry from the collections that made it through the dict
    daylightGeo = [i for i in AC_Collections if i.name in cTable.keys()]

    ###add objects to Daylight layers from AC type collections

    for i in range(0,len(daylightGeo)):
            
        ###add relevant collectionss to dl_imputs if not already present
        if cTable[daylightGeo[i].name] not in [col.name for col in dl_Inputs]:
            
            if cTable[daylightGeo[i].name].count("_") == 2 or daylightGeo[i].name == "Zone":
                dl_Inputs.append(Collection(name = cTable[daylightGeo[i].name], elements = [], collectionType = "layer" ))
                print (f"daylight_Inputs added {cTable[daylightGeo[i].name]} layer!") 
                targetIndex = [col.name for col in dl_Inputs].index(cTable[daylightGeo[i].name])
        ###iterate over relevant AC collections    
        for ele in daylightGeo[i].elements:
            
            ### handle regular geometry
            if daylightGeo[i].name not in ["Zone","CurtainWall"]:
    
                try:
                    for dValue in ele.displayValue:
                        dValue.userStrings = createUstrings(ele)

                        dl_Inputs[targetIndex].elements.append(dValue)
                except:
                    pass
            ### special case: zones
            elif daylightGeo[i].name == "Zone":
                failcount = 0
                try:
                    ele.outline.userStrings = createUstrings(ele)
                    dl_Inputs[targetIndex].elements.append(ele.outline)
                except:
                    failcount +=1

            ### special case: ceilings
            elif daylightGeo[i].name == "Slab":
                filteredSlabs = filterCeilings(daylightGeo[i].elements)

        ### special case: curtain walls
        if daylightGeo[i].name == "CurtainWall":
            #Collections based on mesh.rendermaterial.opacity
            cWalls = daylightGeo[i].elements
            meshCollection = [*findGlass(cWalls).values()]
            print(meshCollection)
            sum = dl_Inputs.extend(meshCollection)
            

    ###Get windows doors from walls
    walCols = [i for i in daylightGeo if i.name == "Wall"]
    allWalls = []
    for i in walCols:
        allWalls.extend(i.elements)

    winDoors = getChildren(allWalls)
    winDoorsByGlass = findGlass(winDoors)

    #DL_modell.elements[0].elements += children.values()
    DL_modell.elements[0].elements = dl_Inputs + [*filteredSlabs.values()] + [*winDoorsByGlass.values()]

    return DL_modell
    


##############LOGICTESTING###############

if __name__ == "__main__":
    
    #urlStream = input ("Stream to receive: ")
    ###Receive AC Stream data
    #urlStream = "https://multiconsult.speckle.xyz/projects/8c1aca44f6/models/8819271698@91c950d961"
    #urlStream = "https://multiconsult.speckle.xyz/projects/8c1aca44f6/models/8819271698@9621d4f8bb"
    urlStream =  "https://multiconsult.speckle.xyz/projects/e35c47291d/models/dc14e721c8@2551d279f4"
    wrapper = StreamWrapper(urlStream)
    client = wrapper.get_client()
    transport = wrapper.get_transport()

    comm = client.commit.get(wrapper.stream_id, wrapper.commit_id)
    cData = operations.receive(comm.referencedObject, transport)

    AC_Collections = cData.elements

    for i in AC_Collections:
        print (f"{i.name} - {i.speckle_type} !!!" )


    ###Reverse engineer empty Commit structure from rhino stream // GLOBALS

    DL_modell = Collection(name = "DaylightModel", elements = [], collectionType = "Daylight Model")
    DL_modell.elements.append(Collection(name = "Daylight_Inputs", elements = [], collectionType = "Layer",))
    dl_Inputs = DL_modell.elements[0].elements

    ###Translate AC collection names to daylight layernames with the conversion dict

    ac2Layers = [cTable[i.name] for i in AC_Collections if i.name in cTable.keys()]


    ###Filter geometry from the collections that made it through the dict
    daylightGeo = [i for i in AC_Collections if i.name in cTable.keys()]

    ###create Collections from Daylight layernames
    #for i in ac2Layers:
    #    dl_Inputs.append(Collection(name = i, elements = [], collectionType = "layer"))

    

    ###Check for Zones
    acZones = [i for i in AC_Collections if i.name == "Zone"]
    print(f"Zones found in project: {len(acZones[0].elements)}")
    #print (f"daylight_Inputs found {len(dl_Inputs)} layers!")


    ###add objects to Daylight layers from AC type collections

    for i in range(0,len(daylightGeo)):
            
        ###add relevant collectionss to dl_imputs if not already present
        if cTable[daylightGeo[i].name] not in [col.name for col in dl_Inputs]:
            
            if cTable[daylightGeo[i].name].count("_") == 2 or daylightGeo[i].name == "Zone":
                dl_Inputs.append(Collection(name = cTable[daylightGeo[i].name], elements = [], collectionType = "layer" ))
                print (f"daylight_Inputs added {cTable[daylightGeo[i].name]} layer!") 
                targetIndex = [col.name for col in dl_Inputs].index(cTable[daylightGeo[i].name])
        ###iterate over relevant AC collections    
        for ele in daylightGeo[i].elements:
            
            ### handle regular elements
            if daylightGeo[i].name not in ["Zone","CurtainWall","Slab"]:
    
                try:
                    for dValue in ele.displayValue:
                        dValue.userStrings = createUstrings(ele)

                        dl_Inputs[targetIndex].elements.append(dValue)
                except:
                    pass
            ### special case: zones
            elif daylightGeo[i].name == "Zone":
                failcount = 0
                try:
                    ele.outline.userStrings = createUstrings(ele)
                    dl_Inputs[targetIndex].elements.append(ele.outline)
                except:
                    failcount +=1

            ### special case: ceilings
            elif daylightGeo[i].name == "Slab":
                filteredSlabs = filterCeilings(daylightGeo[i].elements)


                
        ### special case: curtain walls
        if daylightGeo[i].name == "CurtainWall":
            #Collections based on mesh.rendermaterial.opacity
            cWalls = daylightGeo[i].elements
            meshCollection = [*findGlass(cWalls).values()]
            print(meshCollection)
            sum = dl_Inputs.extend(meshCollection)
            

        

    test1 = daylightGeo[5].elements
    test2 = daylightGeo[5]
    #TestVars = getChildren(test)  
    #subEle = getChildren(daylightGeo[0].elements[:11])
    #testCol = list(findGlass(test1).values())
    #print (testCol)
    #print (testCol.values())

    ###Get windows doors from walls
    walCols = [i for i in daylightGeo if i.name == "Wall"]
    allWalls = []
    for i in walCols:
        allWalls.extend(i.elements)

    winDoors = getChildren(allWalls)
    winDoorsByGlass = findGlass(winDoors)

    #DL_modell.elements[0].elements += children.values()
    DL_modell.elements[0].elements = dl_Inputs + [*filteredSlabs.values()]+[*winDoorsByGlass.values()]

    print (DL_modell.elements[0].elements)

    ###send stream
    SendDL(DL_modell, "https://multiconsult.speckle.xyz/projects/e35c47291d", urlStream)
    



