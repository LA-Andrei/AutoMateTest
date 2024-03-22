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
    "Stair":"_Floors_20",
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
def Send(DL_modell, Stream):
    #sWrap = StreamWrapper ("https://multiconsult.speckle.xyz/projects/8c1aca44f6")
    sWrap = StreamWrapper (Stream)
    sTransport = sWrap.get_transport()
    sClient = sWrap.get_client()

    sendID = operations.send(DL_modell, [sTransport])
    sClient.commit.create(sWrap.stream_id, sendID, message= " simple translate test" )
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
def kCheck(obj,key):
    ###check for attribute in Base
    try: 
        if key in obj.get_member_names():
            return True
        else:
            return False
    except:
        return False
    
def createUstrings(obj,list = ["level", "type", "layer", "height", "width", "thickness", "room", "lengh", "area", "name", "number","nummer","elemenetType"]):

    ###Attempt to add specific attributes as user strings 

    #list = ["level", "layer", "height", "thickness", "room", "lengh", "area", "name", "number","elemenetType"]
    #obj.userStrings = Base( level = obj.level.name, layer = str(obj.layer), applicationId = str(obj.applicationId), height = str(obj.height), thickness = str(obj.thickness), elementType = obj.elementType)
    userStrings = Base (appID = str(obj.applicationId), speckleType = str(obj.speckle_type))

    for i in list:
        if kCheck(obj,i) == True:
            if type(obj[i]) != type(Base()):
                userStrings[i] = str(obj[i])
            else:
                userStrings[i] = obj[i].name
    return userStrings

def getChildren(input):
    #get children elements from BaseObject

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


def findGlass(input):

    
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
            colList = [col.name for col in dl_Inputs]

            if (cTable[eleType] in colList):

                index = colList.index(cTable[eleType])
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

def translateModellAC(ACmodell):

    pass

    
#dupeStream("https://multiconsult.speckle.xyz/projects/8a2236a279/models/368a0dea30@49ff6e189b")                      
                      
#urlStream = input ("Stream to receive: ")


###Receive AC Stream data
#urlStream = "https://multiconsult.speckle.xyz/projects/8c1aca44f6/models/8819271698@91c950d961"
urlStream = "https://multiconsult.speckle.xyz/projects/8c1aca44f6/models/8819271698@9621d4f8bb"
wrapper = StreamWrapper(urlStream)
client = wrapper.get_client()
transport = wrapper.get_transport()

comm = client.commit.get(wrapper.stream_id, wrapper.commit_id)
cData = operations.receive(comm.referencedObject, transport)


"""if comm.sourceApplication == "Archicad":
    print ("AC")
"""

elements = cData.elements

for i in elements:
    print (f"{i.name} - {i.speckle_type} !!!" )


###Reverse engineer empty Commit structure from rhino stream

DL_modell = Collection(name = "DaylightModel", elements = [], collectionType = "Daylight Model")
DL_modell.elements.append(Collection(name = "Daylight_Inputs", elements = [], collectionType = "Layer",))
dl_Inputs = DL_modell.elements[0].elements

###Translate AC collection names to daylight layernames with the conversion dict

ac2Layers = [cTable[i.name] for i in elements if i.name in cTable.keys()]


###Filter geometry from the collections that made it through the dict
daylightGeo = [i for i in elements if i.name in cTable.keys()]

###create Collections from Daylight layernames
for i in ac2Layers:
    dl_Inputs.append(Collection(name = i, elements = [], collectionType = "layer"))

 

###Check for Zones
acZones = [i for i in elements if i.name == "Zone"]
print(f"Zones found in project: {len(acZones[0].elements)}")
  
print (f"daylight_Inputs found {len(dl_Inputs)} layers!")


###add objects to Daylight layers from AC type collections

for i in range(0,len(dl_Inputs)):
    subEleTypes = set()
    t2Collections = {}

    for ele in daylightGeo[i].elements:
        
        if daylightGeo[i].name not in ["Zone","CurtainWall"]:
            try:
                eleNames = ele.get_member_names()
                
                if "elements" in eleNames:
                    
                    for ii in ele.elements:

                        subEleTypes.append(ele.elements.elementType)
                        if ele.elements.elementType not in t2Collections.keys():
                            t2Collections[ele.elements.elementType] = Collection(name = ele.elements.elementType, elements=[ii], collectionType = "layer")
                        else: 
                            t2Collections[ele.elements.elementType].elements.append(ii)

            except:
                failCount = "things Failed"
                
            try:
                for dValue in ele.displayValue:
                    dValue.userStrings = createUstrings(ele)
                    dl_Inputs[i].elements.append(dValue)
            except:
                print("error on dValue to Daylight Base")

        elif daylightGeo[i].name == "Zone":
            try:
                ele.outline.userStrings = createUstrings(ele)
                dl_Inputs[i].elements.append(ele.outline)
            except:
                print(f"error on outline to Daylight Base: {ele.elementType}")
    if daylightGeo[i].name == "CurtainWall":
        #Collections based on mesh.rendermaterial.opacity
        cWalls = daylightGeo[i].elements
        meshCollection = [*findGlass(cWalls).values()]
        print(meshCollection)
        sum = dl_Inputs.extend(meshCollection)
        

    print (f"{dl_Inputs[i].name} found {len(daylightGeo[i].elements)} elements!")

test1 = daylightGeo[5].elements
test2 = daylightGeo[5]
#TestVars = getChildren(test)  
#subEle = getChildren(daylightGeo[0].elements)
testCol = list(findGlass(test1).values())
#print (testCol)
#print (testCol.values())
t2Collections

children = getChildren(daylightGeo[0].elements)["ALT1"]

#DL_modell.elements[0].elements += children.values()
DL_modell.elements[0].elements = dl_Inputs + [*children.values()]

print (DL_modell.elements[0].elements)

###send stream
Send(DL_modell, "https://multiconsult.speckle.xyz/projects/8c1aca44f6")



