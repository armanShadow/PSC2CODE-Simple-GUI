import cv2
from darkflow.net.build import TFNet
import matplotlib.pyplot as plt
import os
import lxml.etree as etree
import pandas as pd
import random
import math
def FindGroundTruth(file):
    Annotation_folder = os.path.join(r"H:\NewAnnotations\NewAnnotation",file)
    doc = etree.parse(Annotation_folder)
    return [doc.find("object").find("bndbox").find("xmin").text,doc.find("object").find("bndbox").find("ymin").text,
                    doc.find("object").find("bndbox").find("xmax").text,doc.find("object").find("bndbox").find("ymax").text ]





def bb_contours(img):
    image = cv2.imread(img, 1)

    ratio = image.shape[0] / 300.0


    # convert the image to grayscale, blur it, and find edges
    # in the image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)
    im2, contours, hierarchy = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    try:
        hierarchy = hierarchy[0]
    except:
        hierarchy = []

    height, width, _ = image.shape
    min_x, min_y = width, height
    max_x = max_y = 0

    # computes the bounding box for the contour, and draws it on the frame,
    i = 0
    AllContours=[]
    for contour, hier in zip(contours, hierarchy):
        (x, y, w, h) = cv2.boundingRect(contour)
        min_x, max_x = min(x, min_x), max(x + w, max_x)
        min_y, max_y = min(y, min_y), max(y + h, max_y)

        if w > 1000 and h > 80:
            #cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
            AllContours.append([x,y,x+w,y+h])
            i += 1

    print("IMAGE:",img," Contours",AllContours)
    # if max_x - min_x > 0 and max_y - min_y > 0:
    #     cv2.rectangle(image, (min_x, min_y), (max_x, max_y), (255, 0, 0), 2)

    #cv2.imshow("H", image)
    return AllContours


def bb_intersection_over_union(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])#maxX, boxA[0] = minX
    yA = max(boxA[1], boxB[1])#minY
    xB = min(boxA[2], boxB[2])#maxX
    yB = min(boxA[3], boxB[3])#maxY

    # compute the area of intersection rectangle
    interArea = (xB - xA + 1) * (yB - yA + 1)

    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1) #prediction
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1) #ground-truth

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / (float(boxAArea + boxBArea - interArea))
    if(iou<0):
        iou=0

    # return the intersection over union value
    return iou


def contourCorrection(bb_box,imgPath):
    print(imgPath)
    predictedBox = [bb_box[0]['topleft']['x'], bb_box[0]['topleft']['y'], bb_box[0]['bottomright']['x'],
                    bb_box[0]['bottomright']['y']]
    predictedBox = list(map(int, predictedBox))

    allContours=bb_contours(imgPath)
    maxIOU=0
    if(len(allContours)>0):
        matchedContor=allContours[0]
        for cntr in allContours:
            countor = list(map(int, cntr))
            iou = bb_intersection_over_union(predictedBox, countor)
            print("IOU:",iou)
            if(iou > maxIOU and iou > .4):
                maxIOU=iou
                matchedContor=countor
        print(matchedContor)
        if(maxIOU!=0):
            if(imgPath.endswith("new_27_img516.png")):
                return allContours
            else:
                return matchedContor


#%config InlineBackend.figure_format = 'svg'
#4000, 3750, 3625, 3500, 3375, 3250
options = {
    'model': 'cfg/tiny-yolo-voc-1c.cfg',
    'load': 22500,
    'threshold': 0.1,
}
tfnet = TFNet(options)

img_folder=r"H:\NewAnnotations\NewIDE"
outputDir=r"H:\NewAnnotations\NewIDE\Result"
# outputDir2=r"new_model_data\TestImages\BadPrediction"


#for test correction
lstRows=[]

for n, image_file in enumerate(os.scandir(img_folder)):
    dRow = dict()

    path = image_file.path
    if(not path.endswith(".png")):
        continue
    # if(not image_file.name.endswith("new_27_img516.png")):
    #      continue

    img = image_file
    name=str(image_file.name)[:str(image_file.name).find(".")]
    name+=".xml"

    img=cv2.imread(path)
    img= cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    print(path)
    result = tfnet.return_predict(img)

    if (len(result) != 0):
        maxConf = 0
        topleftX = 0
        toprightY = 0
        bottomLeftX = 0
        bottomRightY = 0
        count = 0
        index = 0
        index = 0
        found = False
        for i in result:
            for key, data in i.items():
                if (key == "confidence"):
                    if (data > maxConf):
                        maxConf = data
                        index = count
                    count += 1

        print(index, " max Conf=", maxConf)
        tl = (result[index]['topleft']['x'], result[index]['topleft']['y'])
        br = (result[index]['bottomright']['x'], result[index]['bottomright']['y'])
        predictedBox=[result[index]['topleft']['x'],  result[index]['topleft']['y'], result[index]['bottomright']['x'], result[index]['bottomright']['y']]
        predictedBox=list(map(int, predictedBox))
        GroundTruth=list(map(int, FindGroundTruth(name)))
        #print("IOU:",bb_intersection_over_union(predictedBox,GroundTruth))
        print(tl, "  ", br)
        label = result[index]['label']
        dRow['FileName'] = str(image_file.name)
        iou=bb_intersection_over_union(predictedBox,GroundTruth)
        dRow["IOU"] = iou
        lstRows.append(dRow)
        img = cv2.rectangle(img,(GroundTruth[0],GroundTruth[1]), (GroundTruth[2],GroundTruth[3]), (0, 5, 0), 3)
        img = cv2.rectangle(img, tl, br, (255, 0, 0), 3)  # red box, line thickness 7
        # convert the image into rbg image
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        #plt.imshow(img)
        outputPath=os.path.join(outputDir,image_file.name)
        # outputPath2 = os.path.join(outputDir2, image_file.name)
        print("IOU = ",iou)
        cv2.imwrite(outputPath, img)
        #plt.show()
        # add the box
        print(result)
    else:
        print("dicrease the confidence please")



df = pd.DataFrame(lstRows)
print( df.sort_values(by=['IOU']))
print("\tMax: %f" % df['IOU'].max())
print("\tMin: %f" % df['IOU'].min())
print("\tAvg: %f" % df['IOU'].mean())



# badPredictionFolder=r"new_model_data\TestImages\BadPrediction"
# for n, image_file in enumerate(os.scandir(badPredictionFolder)):
#     imgName=image_file.name
#     path=image_file.path
#     if(not path.endswith(".png")):
#         continue
#     # if(not image_file.name.endswith("new_27_img516.png")):
#     #      continue
#     path=os.path.join("new_model_data\TestImages",imgName) # We need the original image
#     img = cv2.imread(path)
#     img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     result = tfnet.return_predict(img)
#     if (len(result) != 0):
#         expectedContor=contourCorrection(result,path)
#         if(expectedContor is not None):
#             tl = (result[0]['topleft']['x'], result[0]['topleft']['y'])
#             br = (result[0]['bottomright']['x'], result[0]['bottomright']['y'])
#             img = cv2.rectangle(img, tl, br, (0, 255, 0), 3)
#             if (imgName.endswith("new_27_img516.png")):
#                 for i in expectedContor:
#                     r = lambda: random.randint(0, 255)
#                     print('#%02X%02X%02X' % (r(), r(), r()))
#                     img = cv2.rectangle(img, (i[0], i[1]), (i[2], i[3]),
#                                         (r(), r(), r()), 3)
#
#             else:
#                 tl = (result[0]['topleft']['x'], result[0]['topleft']['y'])
#                 br = (result[0]['bottomright']['x'], result[0]['bottomright']['y'])
#                 #img = cv2.rectangle(img, tl, br, (0, 5, 0), 3)
#                 img = cv2.rectangle(img, (expectedContor[0],expectedContor[1]), (expectedContor[2],expectedContor[3]), (0, 0, 255), 3)
#             correctedPath=r"new_model_data\TestImages\BadPrediction\Corrected"
#             correctedPath=os.path.join(correctedPath,imgName)
#             cv2.imwrite(correctedPath, img)
#     else:
#         print(imgName,"There is no predicted box")