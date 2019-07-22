import operator
import numpy
import math
import random
import copy

mode = 'None'  # ??????????

class MainWindow(QtWidgets.QMainWindow):
    loadPoint = []  # ?????list??????list
    listPointCount = []  # ??????????????????
    listConvexLine = []  # ???????
    resultPoint = [] # Output point
    resultLine = [] # Output line
    listStep = []  # ????
    indexStep = 0
    # --------------------------------------------------------

    def listenerRun(self):
        global mode
        self.resultPoint.clear()
        self.resultLine.clear()
        self.listConvexLine.clear()
        self.listStep.clear()
        self.scene.clear()
        self.indexStep = 0

        self.listStep.append([None])
        listPoint = []
        if len(self.listPointCount) == 0:
            mode = 'None'
            self.dialog = MessageDialog.MessageDialog('Out of data!')
            self.dialog.exec_()
        else:
            for i in range(0, self.listPointCount[0]):
                listPoint.append(self.loadPoint[0])
                self.loadPoint.pop(0)
            self.listPointCount.pop(0)

            self.labelAutoAmount.setText(str(len(self.listPointCount)))
            self.resultPoint, listPoint = self.sortPoint(listPoint)  # resultPoint???list?listPoint???PointF

            if len(listPoint) <= 6:
                self.listStep.append(listPoint)
                self.dividePoint(listPoint)

                # ??step????
                for item in self.listStep[len(self.listStep)-1]:
                    typeItem = str(type(item))
                    if typeItem == self.typePoint:
                        self.scene.addEllipse(item.x(), item.y(), 1, 1, self.penBlue, self.brush)
                    elif typeItem == self.typeLine:
                        self.scene.addLine(item, self.penBlack)
                    elif typeItem == self.typeNone:
                        self.scene.clear()

    def sortPoint(self, listPoint):
        resultList = sorted(listPoint, key=operator.itemgetter(0, 1))
        for i in range(0, len(listPoint)):
            listPoint[i] = QtCore.QPointF(resultList[i][0], resultList[i][1])

        return resultList, listPoint

    def sortLine(self):
        resultList = []
        for i in range(0, len(self.listConvexLine)):
            line = [round(self.listConvexLine[i][1].x1(), 0), round(self.listConvexLine[i][1].y1(), 0), round(self.listConvexLine[i][1].x2(), 0), round(self.listConvexLine[i][1].y2(), 0)]
            resultList.append(line)
        resultList = sorted(resultList, key=operator.itemgetter(0, 1, 2, 3))

        return resultList

    def dividePoint(self, listPoint):
        amount = len(listPoint)
        listLocalConvexLine = []
        if amount > 3:
            listLocalConvexLine1 = self.dividePoint(listPoint[:math.ceil(amount/2)])    # ??
            listLocalConvexLine2 = self.dividePoint(listPoint[math.ceil(amount/2):])    # ??

            listMergeConvexLine, listLeftInnerConvexLine, listLeftPerpendicularBisector, listRightInnerConvexLine, listRightPerpendicularBisector = self.mergeConvex(listLocalConvexLine1, listLocalConvexLine2)

            # For step by step
            self.listStep.append([None])  # ????
            point = []
            for item in listMergeConvexLine:
                point.append(item.p1())
            self.listStep.append(point)  # ??merge?convex hull?
            temp = []   # ?? convex????????
            temp.extend(listMergeConvexLine)
            temp.extend(listLeftPerpendicularBisector)
            temp.extend(listRightPerpendicularBisector)
            self.listStep.append(temp)  # ???????

            # ?????
            tempResult = []
            tempResult.extend(listPoint)
            listAllHyperplane, listModifyPerpendicularBisector = self.getHyperplane(listLeftInnerConvexLine, listLeftPerpendicularBisector, listRightInnerConvexLine, listRightPerpendicularBisector)

            tempResult.extend(listAllHyperplane)
            tempResult.extend(listModifyPerpendicularBisector)
            self.listStep.append([None])
            self.listStep.append(tempResult)
            # ---------------------------------------------------------------------------------------------

        else:
            #?divid???
            self.listStep.append(listPoint)

            listLocalConvexLine = self.drawConvex(listPoint)
            listLocalConvexLine = self.drawPerpendicularBisector(listLocalConvexLine)
            if len(listLocalConvexLine) < 2:
                intersectionPoint = None
            else:
                intersectionPoint = self.findIntersectionPoint(listLocalConvexLine[0][1], listLocalConvexLine[1][1], 'PerpendicularBisector')

            # ??????
            if intersectionPoint != None:
                for i in range(0, len(listLocalConvexLine)):
                    position = self.determineIntersectionRelativePosition(listLocalConvexLine[i][0], intersectionPoint)
                    listLocalConvexLine[i].append(position)
                    self.deleteExceedLine(listLocalConvexLine[i], intersectionPoint)

            #?convex???
            temp = []
            temp.extend(listPoint)
            for item in listLocalConvexLine:
                temp.append(item[1])
            self.listStep.append(temp)

            return listLocalConvexLine

    def getHyperplane(self, listLeftInnerConvexLine, listLeftPerpendicularBisector, listRightInnerConvexLine, listRightPerpendicularBisector):
        listAuxiliaryLine = []  # ???
        listHyperplane = []
        # For ??
        listAllHyperplane = []
        listModifyPerpendicularBisector = []
        # ????convex hull?
        listLeftPoint = self.getConvexPoint(listLeftInnerConvexLine)
        listRightPoint = self.getConvexPoint(listRightInnerConvexLine)
        listLeftPoint = sorted(listLeftPoint, key=lambda s: s.y())
        listRightPoint = sorted(listRightPoint, key=lambda s: s.y())

        # ?????????????
        indexLeft = 0
        indexRight = 0
        indexHyperplane = 0
        latestX2 = 0
        latestY2 = 0
        isFirstHyperplane = True

        while 1:
            # Hyperplane???
            if indexRight >= len(listRightPoint) or indexLeft >= len(listLeftPoint):
                break
            listAuxiliaryLine.append(QtCore.QLineF(listRightPoint[indexRight], listLeftPoint[indexLeft]))
            self.listStep.append([QtCore.QLineF(listRightPoint[indexRight], listLeftPoint[indexLeft])])

            # ?????????????
            temp = copy.deepcopy(listAuxiliaryLine)
            listHyperplane.append(self.drawPerpendicularBisector(temp)[indexHyperplane])

            #??P1????P2???
            if listHyperplane[indexHyperplane][1].y1() > listHyperplane[indexHyperplane][1].y2():
                temp = listHyperplane[indexHyperplane][1].p1()
                listHyperplane[indexHyperplane][1].setP1(listHyperplane[indexHyperplane][1].p2())
                listHyperplane[indexHyperplane][1].setP2(temp)
            elif listHyperplane[indexHyperplane][1].y1() == listHyperplane[indexHyperplane][1].y2():
                print('Error in getHyperplane()')

            if isFirstHyperplane == False:
                listHyperplane[indexHyperplane][1].setP1(QtCore.QPointF(latestX2, latestY2))

            touchPos = 'Null'
            if not(len(listLeftPoint)-1 == indexLeft and len(listRightPoint)-1 == indexRight):
                #????????????
                intersectionPoint = QtCore.QPointF(600, 600) # Initialize
                deletePerpendicularBisector = None
                for item in listLeftPerpendicularBisector:
                    point = self.findIntersectionPoint(listHyperplane[indexHyperplane][1], item, 'Hyperplane')
                    if point != None and point.y() < intersectionPoint.y() and point.y() > listHyperplane[indexHyperplane][1].y1():
                        intersectionPoint = point
                        touchPos = 'Left'
                        deletePerpendicularBisector = item
                for item in listRightPerpendicularBisector:
                    point = self.findIntersectionPoint(listHyperplane[indexHyperplane][1], item, 'Hyperplane')
                    if point != None and point.y() < intersectionPoint.y() and point.y() > listHyperplane[indexHyperplane][1].y1():
                        intersectionPoint = point
                        touchPos = 'Right'
                        deletePerpendicularBisector = item

                print(indexHyperplane, ':', touchPos)
                listHyperplane[indexHyperplane][1].setP2(intersectionPoint)
                latestX2 = intersectionPoint.x()
                latestY2 = intersectionPoint.y()

                # ??????hyperplane
                modifyPerpendicularBisector = copy.deepcopy(deletePerpendicularBisector)
                if touchPos == 'Left':
                    if modifyPerpendicularBisector.x1() == 600:
                        modifyPerpendicularBisector.setP1(QtCore.QPointF(latestX2, latestY2))
                    elif modifyPerpendicularBisector.x2() == 600:
                        modifyPerpendicularBisector.setP2(QtCore.QPointF(latestX2, latestY2))
                    elif modifyPerpendicularBisector.x1() == modifyPerpendicularBisector.x2():
                        modifyPerpendicularBisector.setP1(QtCore.QPointF(latestX2, latestY2))
                elif touchPos == 'Right':
                    if modifyPerpendicularBisector.x1() == 0:
                        modifyPerpendicularBisector.setP1(QtCore.QPointF(latestX2, latestY2))
                    elif modifyPerpendicularBisector.x2() == 0:
                        modifyPerpendicularBisector.setP2(QtCore.QPointF(latestX2, latestY2))
                    elif modifyPerpendicularBisector.x1() == modifyPerpendicularBisector.x2():
                        modifyPerpendicularBisector.setP2(QtCore.QPointF(latestX2, latestY2))
                listModifyPerpendicularBisector.append(modifyPerpendicularBisector)

            self.listStep.append([listHyperplane[indexHyperplane][1]])
            listAllHyperplane.append(listHyperplane[indexHyperplane][1])
            if touchPos == 'Null':
                break
            # --------------------------------------------------------------------


            if len(listLeftPoint)-1 <= indexLeft and len(listRightPoint)-1 <= indexRight:
                break
            indexHyperplane += 1
            if touchPos == 'Left' and deletePerpendicularBisector != None:
                listLeftPerpendicularBisector.remove(deletePerpendicularBisector)
                indexLeft += 1
            elif touchPos == 'Right' and deletePerpendicularBisector != None:
                listRightPerpendicularBisector.remove(deletePerpendicularBisector)
                indexRight += 1
            else:
                print('Hyperplane error')

            isFirstHyperplane = False

        listModifyPerpendicularBisector.extend(listLeftPerpendicularBisector)
        listModifyPerpendicularBisector.extend(listRightPerpendicularBisector)

        return listAllHyperplane, listModifyPerpendicularBisector

    def drawConvex(self, listPoint):
        listLocalConvexLine = []
        # ?????????
        if len(listPoint) == 2:
            listLocalConvexLine.append(QtCore.QLineF(
                listPoint[0].x(), listPoint[0].y(), listPoint[1].x(), listPoint[1].y()))
        elif len(listPoint) == 3:
            # ??????
            order = (listPoint[1].x()-listPoint[0].x())*(listPoint[2].y()-listPoint[0].y()) - (
                    listPoint[1].y()-listPoint[0].y())*(listPoint[2].x()-listPoint[0].x())
            if order < 0:   # ????
                listLocalConvexLine.append(QtCore.QLineF(
                    listPoint[0].x(), listPoint[0].y(), listPoint[1].x(), listPoint[1].y()))
                listLocalConvexLine.append(QtCore.QLineF(
                    listPoint[1].x(), listPoint[1].y(), listPoint[2].x(), listPoint[2].y()))
                listLocalConvexLine.append(QtCore.QLineF(
                    listPoint[2].x(), listPoint[2].y(), listPoint[0].x(), listPoint[0].y()))
            elif order > 0:     # ????
                listLocalConvexLine.append(QtCore.QLineF(
                    listPoint[0].x(), listPoint[0].y(), listPoint[2].x(), listPoint[2].y()))
                listLocalConvexLine.append(QtCore.QLineF(
                    listPoint[2].x(), listPoint[2].y(), listPoint[1].x(), listPoint[1].y()))
                listLocalConvexLine.append(QtCore.QLineF(
                    listPoint[1].x(), listPoint[1].y(), listPoint[0].x(), listPoint[0].y()))
            else:
                listLocalConvexLine.append(QtCore.QLineF(
                    listPoint[0].x(), listPoint[0].y(), listPoint[1].x(), listPoint[1].y()))
                listLocalConvexLine.append(QtCore.QLineF(
                    listPoint[1].x(), listPoint[1].y(), listPoint[2].x(), listPoint[2].y()))

        temp = copy.deepcopy(listLocalConvexLine)
        self.listStep.append(temp)

        return listLocalConvexLine

    def mergeConvex(self, listLocalConvexLine1, listLocalConvexLine2):
        # merge??
        listMergeConvexLine1 = []
        listMergeConvexLine2 = []
        listLeftInnerConvexLine = []
        listRightInnerConvexLine = []
        # ????convex hull???
        listPoint1 = self.getConvexPoint(listLocalConvexLine1)
        listPoint2 = self.getConvexPoint(listLocalConvexLine2)
        # ???????????????
        max_X = 0
        max_Y = 0
        min_X = 600
        min_Y = 600
        for item in listPoint1:
            if item.x() > max_X:
                max_X = item.x()
            if item.y() > max_Y:
                max_Y = item.y()
        for item in listPoint2:
            if item.x() < min_X:
                min_X = item.x()
            if item.y() < min_Y:
                min_Y = item.y()

        # ??
        temp1 = []
        temp2 = []
        for i in range(len(listLocalConvexLine1)):
            temp1.append(listLocalConvexLine1[i][0])
        listMergeConvexLine1 = copy.deepcopy(temp1)
        listLeftInnerConvexLine = copy.deepcopy(listMergeConvexLine1)
        for i in range(len(listLocalConvexLine2)):
            temp2.append(listLocalConvexLine2[i][0])
        listMergeConvexLine2 = copy.deepcopy(temp2)
        listRightInnerConvexLine = copy.deepcopy(listMergeConvexLine2)

        if len(listMergeConvexLine1) == 1:  # ??????????
            listMergeConvexLine1.append(QtCore.QLineF(listMergeConvexLine1[0].x2(), listMergeConvexLine1[0].y2(), listMergeConvexLine1[0].x1(), listMergeConvexLine1[0].y1()))
        # ??????????????
        for i in range(len(listPoint2)):
            for j in range(len(listMergeConvexLine1)):
                if listMergeConvexLine1[j] != None:
                    direction = self.determineIntersectionRelativePosition(listMergeConvexLine1[j], listPoint2[i])
                    if direction == 'right':
                        if listMergeConvexLine1[j].y1() == max_Y:
                            listMergeConvexLine1[j].setP2(listPoint2[i])
                        else:
                            listMergeConvexLine1[j] = None  # ?????????None

        if len(listMergeConvexLine2) == 1:  # ??????????
            listMergeConvexLine2.append(QtCore.QLineF(listMergeConvexLine2[0].x2(), listMergeConvexLine2[0].y2(), listMergeConvexLine2[0].x1(), listMergeConvexLine2[0].y1()))
            # ??????????????
        for i in range(len(listPoint1)):
            for j in range(len(listMergeConvexLine2)):
                if listMergeConvexLine2[j] != None:
                    direction = self.determineIntersectionRelativePosition(listMergeConvexLine2[j], listPoint1[i])
                    if direction == 'right':
                        if listMergeConvexLine2[j].y1() == min_Y:
                            listMergeConvexLine2[j].setP2(listPoint1[i])
                        else:
                            listMergeConvexLine2[j] = None  # ?????????None

        try:
            listMergeConvexLine1.remove(None)
        except ValueError:
            pass

        for item in listMergeConvexLine2:
            if item not in listMergeConvexLine1 and item != None:
                listMergeConvexLine1.append(item)

        # ?????
        listLeftPerpendicularBisector = []
        listRightPerpendicularBisector = []
        for item in listLocalConvexLine1:
            listLeftPerpendicularBisector.append(item[1])
        for item in listLocalConvexLine2:
            listRightPerpendicularBisector.append(item[1])

        # ????????convex?(?)
        if len(listLeftInnerConvexLine) > 2:
            for item in listMergeConvexLine1:
                if item in listLeftInnerConvexLine:
                    listLeftInnerConvexLine.remove(item)
        # ?inner convex hull??????(????)
        for i in range(len(listLeftInnerConvexLine)):
            for j in range(len(listLocalConvexLine1)):
                if listLeftInnerConvexLine[i] == listLocalConvexLine1[j][0]:
                    listLeftInnerConvexLine[i] = [
                        listLeftInnerConvexLine[i], listLocalConvexLine1[j][1]]

        # ????????convex?(?)
        if len(listRightInnerConvexLine) > 2:
            for item in listMergeConvexLine2:
                if item in listRightInnerConvexLine:
                    listRightInnerConvexLine.remove(item)
        # ?inner convex hull??????(????)
        for i in range(len(listRightInnerConvexLine)):
            for j in range(len(listLocalConvexLine2)):
                if listRightInnerConvexLine[i] == listLocalConvexLine2[j][0]:
                    listRightInnerConvexLine[i] = [
                        listRightInnerConvexLine[i], listLocalConvexLine2[j][1]]

        return listMergeConvexLine1, listLeftInnerConvexLine, listLeftPerpendicularBisector, listRightInnerConvexLine, listRightPerpendicularBisector

    def getConvexPoint(self, listLocalConvexLine):
        listPoint = []
        for i in range(len(listLocalConvexLine)):
            point1 = QtCore.QPointF(listLocalConvexLine[i][0].x1(), listLocalConvexLine[i][0].y1())
            point2 = QtCore.QPointF(listLocalConvexLine[i][0].x2(), listLocalConvexLine[i][0].y2())
            if point1 not in listPoint:
                listPoint.append(point1)
            if point2 not in listPoint:
                listPoint.append(point2)
        return listPoint

    def drawPerpendicularBisector(self, listLocalConvexLine):

        for i in range(0, len(listLocalConvexLine)):
            # ??????????
            midpointX = (listLocalConvexLine[i].x1()+listLocalConvexLine[i].x2())/2
            midpointY = (listLocalConvexLine[i].y1()+listLocalConvexLine[i].y2())/2
            # Perpendicular Bisector slope
            if (listLocalConvexLine[i].y2()-listLocalConvexLine[i].y1()) != 0:
                # ??????
                m = -(listLocalConvexLine[i].x2()-listLocalConvexLine[i].x1()) / (listLocalConvexLine[i].y2()-listLocalConvexLine[i].y1())
                c = midpointY-(m*midpointX)
                # ?????
                if m > 0 or m < 0:
                    x1New = 0
                    y1New = m*x1New+c
                    x2New = 600
                    y2New = m*x2New+c
                #?????
                else:
                    x1New = 0
                    x2New = 600
                    y1New = midpointY
                    y2New = midpointY
            #?????
            else:
                x1New = midpointX
                x2New = midpointX
                # Y???????
                y1New = -10000
                y2New = 10000

            line = QtCore.QLineF(x1New, y1New, x2New, y2New)

            # ??convex line????????list??
            listLocalConvexLine[i] = [listLocalConvexLine[i], line]

        return listLocalConvexLine

    def findIntersectionPoint(self, line1, line2, mode):
        IntersectionPoint = QtCore.QPointF(0, 0)
        result = line1.intersect(line2, IntersectionPoint)
        if mode == 'PerpendicularBisector':
            if result == 0:
                return None
            else:
                return IntersectionPoint
        elif mode == 'Hyperplane':
            if result == 1:
                return IntersectionPoint
            else:
                return None

    def determineIntersectionRelativePosition(self, convexLine, point):
        result = (convexLine.x2()-convexLine.x1())*(point.y()-convexLine.y1()) - (convexLine.y2()-convexLine.y1())*(point.x()-convexLine.x1())
        if result > 0:
            return 'right'
        elif result < 0:
            return 'left'
        else:
            return 'line'

    def deleteExceedLine(self, convexLine, point):
        midPointX = (convexLine[0].x1()+convexLine[0].x2())/2
        midPointY = (convexLine[0].y1()+convexLine[0].y2())/2
        # ??function???????????
        if abs(midPointX-point.x()) < 0.01:
            midPointX = point.x()
        if abs(midPointY-point.y()) < 0.01:
            midPointY = point.y()

        # ??????????????
        if convexLine[2] == 'left':
            vectorX = point.x()-midPointX
            vectorY = point.y()-midPointY
        elif convexLine[2] == 'right':
            vectorX = midPointX-point.x()
            vectorY = midPointY-point.y()
        else:
            vectorX = 0
            vectorY = 0

        if (point.x()-midPointX) != 0:  # ????
            m = (point.y()-midPointY) / (point.x()-midPointX)
            c = point.y()-(m*point.x())
        else:
            if (point.y()-midPointY) == 0:  # ?????
                m = -(convexLine[0].x1()-convexLine[0].x2()) / (convexLine[0].y1()-convexLine[0].y2())
                c = point.y()-(m*point.x())

        if vectorX > 0:
            drawPointX = 600
            if vectorY != 0:
                drawPointY = m*drawPointX+c
            else:
                drawPointY = point.y()
        elif vectorX < 0:
            drawPointX = 0
            if vectorY != 0:
                drawPointY = m*drawPointX+c
            else:
                drawPointY = point.y()
        else:
            drawPointX = point.x()
            if vectorY > 0:  # ??
                drawPointY = 600
            elif vectorY < 0:  # ??
                drawPointY = 0
            else:  # ????
                if convexLine[0].x1()-convexLine[0].x2() > 0 and convexLine[0].y1()-convexLine[0].y2() > 0:
                    drawPointX = 0
                elif convexLine[0].x1()-convexLine[0].x2() > 0 and convexLine[0].y1()-convexLine[0].y2() < 0:
                    drawPointX = 600
                elif convexLine[0].x1()-convexLine[0].x2() < 0 and convexLine[0].y1()-convexLine[0].y2() > 0:
                    drawPointX = 0
                elif convexLine[0].x1()-convexLine[0].x2() < 0 and convexLine[0].y1()-convexLine[0].y2() < 0:
                    drawPointX = 600
                drawPointY = m*drawPointX+c

        if drawPointX != point.x() or drawPointY != point.y():
            distance1 = self.calculateDistance(convexLine[1].x1(), convexLine[1].y1(), drawPointX, drawPointY)
            distance2 = self.calculateDistance(convexLine[1].x2(), convexLine[1].y2(), drawPointX, drawPointY)
            if distance1 < distance2:
                convexLine[1].setP1(QtCore.QPointF(point.x(), point.y()))
            else:
                convexLine[1].setP2(QtCore.QPointF(point.x(), point.y()))

    def calculateDistance(self, x1, y1, x2, y2):
        return numpy.sqrt(pow(x1-x2, 2) + pow(y1-y2,2))

    def hasDuplicate(self, list):
        temp = []
        for item in list:
            if item not in temp:
                temp.append(item)

        if len(temp) != len(list):
            return True
        else:
            return False