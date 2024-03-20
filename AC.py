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
    "Zon":"_Curves",
    "Wall":"_Walls_50",
    "Column":"_Columns_50",
    "Slab":"_Floors_20",
    "Stair":"_Floors_20",
    "Ceiling":"_Ceilings_70",
    "Roof":"_Roof_20",
    "Railing":"_Railings_20",
    "Mesh":"_Ground_20",
    "Morph":"_Context_30"
    }

yyy = Base()

print(type(yyy) == type(Base()))

#####Functions here#######
#Send to stream
def Send(DL_modell, Stream):
    #sWrap = StreamWrapper ("https://multiconsult.speckle.xyz/projects/8c1aca44f6")
    sWrap = StreamWrapper (Stream)
    sTransport = sWrap.get_transport()
    sClient = sWrap.get_client()

    sendID = operations.send(DL_modell, [sTransport])
    sClient.commit.create(sWrap.stream_id, sendID, message= " simple translate test" )

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
    
def createUstrings(obj,list = ["level.name", "layer", "height", "thickness", "room", "lengh", "area", "name", "number","elemenetType"]):

    ###Attempt to add specific attributes as user strings

    #list = ["level", "layer", "height", "thickness", "room", "lengh", "area", "name", "number","elemenetType"]
    #obj.userStrings = Base( level = obj.level.name, layer = str(obj.layer), applicationId = str(obj.applicationId), height = str(obj.height), thickness = str(obj.thickness), elementType = obj.elementType)
    obj.userStrings = Base (applicationId = str(obj.applicationId), speckle_type = str(obj.speckle_type))

    for i in list:
        if kCheck(obj,i) == True:
            if type(obj[i]) != type(Base()):
                 obj.userStrings[i] = obj[i]
            else:
                obj.userStrings[i]["Name"]

def translateModellAC(ACmodell):

    pass

    
#dupeStream("https://multiconsult.speckle.xyz/projects/6ade720ed8/models/40fbf9f301@e750056cd0")                      
                      
#urlStream = input ("Stream to receive: ")


###Receive AC Stream data
urlStream = "https://multiconsult.speckle.xyz/projects/8c1aca44f6/models/8819271698@91c950d961"
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

if len(acZones) > 0:

    dl_Inputs = [Collection(name = "_Curves",elements = [], collectionType = "layer")] + dl_Inputs
    zoneObjs = [i for i in elements if i.name == "Zone"]

    ###Adding userstrings to outline to get them in rhino

    
    #for i in zoneObjs[0].elements:
    #    i.outline.userStrings = Base(applicationID = str(i.applicationId), RoomName = str(i.name), RoomNumber = str(i.number), RoomArea = str(i.area), RoomHeight = str(i.height),elementType = str(i.elementType), speckle_type = str(i.speckle_type))

    crvZones = [i.outline for i in zoneObjs[0].elements]
    ### adding the Collection object containing the Curves
    daylightGeo = [Collection(name = "_Curves", elements = crvZones, collectionType = "layer")] + daylightGeo
    
    
print (f"daylight_Inputs found {len(dl_Inputs)} layers!")

#k.get_member_names
###add objects to Daylight layers from AC type collections
for i in range(0,len(dl_Inputs)):
    dl_Inputs[i].elements = daylightGeo[i].elements
    print (f"{dl_Inputs[i].name} found {len(daylightGeo[i].elements)} elements!")

    for j in dl_Inputs[i].elements:
        #if j.speckle_type != "Objects.Geometry.Polycurve":
            if "userStrings" not in j.get_member_names():
                createUstrings(j)

DL_modell.elements[0].elements = dl_Inputs

#print (DL_modell.elements[0].elements)

#send stream
Send(DL_modell, "https://multiconsult.speckle.xyz/projects/8c1aca44f6")



