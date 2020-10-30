#
# idoc2raml.py
#
# /******************************************************************************
#  **                                                                          **
#  ** Convert IDOCs to RAML Schema                                             **
#  **                                                                          **
#  ** Original program (C) 2020 by Andreas Grimm                               **
#  ** <andreas.grimm@gricom.eu> or <andreas.grimm@mulesoft.com>                **
#  **                                                                          **
#  ******************************************************************************
#
# Copyright (C) 2020 Andreas Grimm
#
# Portions Copyright (C) 2020 by MuleSoft, used with permission.
#
# This program is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation;
# either version 2 of the License, or (at your option) any later version. This program
# is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details. You should have received a copy of
# the GNU General Public License along with this program; if not, write to the Free
# Software Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

from xml.dom import minidom
import logging, sys, argparse, os
import re as regEx


def main():
    outputDirectory = ''
    segmentAttributes = []
    generateExamples = False

    # handle the command line parameter
    logging.disable(logging.ERROR)
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--example", help="generate example files", action="store_true")
    parser.add_argument("-d", "--debug", help="activate the debugging function", action="store_true")
    parser.add_argument("-o", "--output", help="define the output directory")
    parser.add_argument("input", help="define the input file")

    args = parser.parse_args()

    if args.debug:
        logging.disable(logging.NOTSET)

    if args.output:
        outputDirectory = args.output
    else:
        outputDirectory = os.getcwd()
    logger.info("selected output directory: " + outputDirectory)

    if args.example:
        generateExamples = True

    inputFile = args.input

    # generate a list of all XML segments with names, types, and values in the idoc
    logger.info("starting the parsing process...")
    segments = getXMLSegments('/Users/andreas/Projects/Sources/Python/python-tools/idoc2raml/tst/ORDERS_IDOC.xml')
    segmentNames = getListOfSegments(segments)
    for segmentName in segmentNames:
        segmentAttributes.append(segmentName)
        segmentAttributes.append(object)
        segmentAttributes.append(getAttributesForSegment(segmentName, segments))
    logger.info("IDOC Document parsed...")

    # normalize the segment list
    logger.info("normalizing the parsed result...")
    normalizedSegmentList = normalize(segmentAttributes)

    # try to adjust the type
    logger.info("adjusting type...")
    normalizedSegmentList = adjustType(normalizedSegmentList)

    # generate the RAML
    logger.info("create RAMLs...")
    numberOfRAMLFiles = generateRamlFiles(outputDirectory, normalizedSegmentList)
    logger.info("Generated RAML files: " + str(numberOfRAMLFiles))

    # generate the Example Files
    if generateExamples == True:
        logger.info("create example files...")
        numberOfExampleFiles = generateExampleFiles(outputDirectory, normalizedSegmentList)
        logger.info("Number of generated example files: " + str(numberOfExampleFiles))

    # terminate program with error code 0
    sys.exit(0)


#
# generateExampleFiles: create the different examples files in JSON format.
# input: outputDirectory, normalized structure of the Python list
# output: number of generated generated files
#
def generateExampleFiles(outputDirectory, normalizedList):
    logger.debug(normalizedList)
    numberOfGeneratedFiles = 0

    i = 0
    while i < len(normalizedList):
        numberOfGeneratedFiles = numberOfGeneratedFiles + buildExampleFiles(outputDirectory, normalizedList[i],
                                                                            normalizedList[i + 1])
        i = i + 2

    return (numberOfGeneratedFiles)


def buildExampleFiles(outputDirectory, segmentName, segment):
    numberOfGeneratedFiles = 0

    outputDirectory = outputDirectory + "/examples"
    if not os.path.isdir(outputDirectory):
        os.mkdir(outputDirectory)

    fileName = outputDirectory + '/' + segmentName + ".json"
    logger.debug("generating file: " + fileName)

    fileDesc = open(fileName, "w")
    fileDesc.write('{\n  "' + segmentName + '": {\n')

    i = 0
    while i < len(segment):
        element = segment[i]
        if element[1] == "object":
            fileDesc.write('    "' + element[0] + '": {\n' + constructIndentedJSONGroup(element[2], 1) + '    }')
        else:
            fileDesc.write('    "' + element[0] + '": "' + element[2] + '"')
        if i < len(segment) - 1:
            fileDesc.write(',\n')
        else:
            fileDesc.write('\n')
        i = i + 1

    fileDesc.write("  }\n}\n")
    fileDesc.close()
    return (numberOfGeneratedFiles + 1)


def constructIndentedJSONGroup(segment, indent):
    logger.debug("indenting JSON file: " + str(segment))

    i = 0
    jsonString = ""
    while i < len(segment):
        element = segment[i]
        for x in range(indent):
            jsonString = jsonString + '    '
        if element[1] == "object":
            jsonString = jsonString + '    "' + element[0] + '": "' + constructIndentedJSONGroup(element[2],
                                                                                                 indent + 1) + '"'
        else:
            jsonString = jsonString + '    "' + element[0] + '": "' + element[2] + '"'
        if i < len(segment) - 1:
            jsonString = jsonString + ',\n'
        else:
            jsonString = jsonString + '\n'
        i = i + 1
    return (jsonString)


#
# generateRAMLFiles: create the different RAML files.
# input: outputDirectory, normalized structure of the Python list
# output: number of generated Files
#
def generateRamlFiles(outputDirectory, normalizedList):
    logger.debug(normalizedList)
    numberOfGeneratedFiles = 0

    i = 0
    while i < len(normalizedList):
        numberOfGeneratedFiles = numberOfGeneratedFiles + buildRamlFiles(outputDirectory, normalizedList[i],
                                                                         normalizedList[i + 1])
        i = i + 2

    return (numberOfGeneratedFiles)


def buildRamlFiles(outputDirectory, segmentName, segment):
    numberOfGeneratedFiles = 0

    if not os.path.isdir(outputDirectory):
        os.mkdir(outputDirectory)

    fileName = outputDirectory + '/' + segmentName + ".raml"
    logger.debug("generating file: " + fileName)

    fileDesc = open(fileName, "w")
    fileDesc.write("#%RAML 1.0 Library\n\ntypes:\n  " + segmentName + ":\n    type: object\n")
    fileDesc.write("    properties:\n")

    for element in segment:
        if element[1] == "float":
            element[1] = "number"
        if element[1] == "object":
            numberOfGeneratedFiles = numberOfGeneratedFiles + buildRamlFiles(outputDirectory, element[0], element[2])
        fileDesc.write("      " + element[0] + ": " + element[1] + "\n")

    fileDesc.write("")

    fileDesc.close()
    return (numberOfGeneratedFiles + 1)


#
# adjustType: use best guess to look for the type.
# input: normalized structure of the Python list
# output: normalized structure of the Python list with adjusted types
#
def adjustType(normalizedList):
    logger.debug(normalizedList)

    adjustedList = []
    length = len(normalizedList)
    i = 0
    while i < length:
        adjustedList.append(normalizedList[i])
        adjustedItemList = []

        for item in normalizedList[i + 1]:
            if item != None:
                if item[1] == object:
                    item[1] = "object"
                    temp = []
                    temp.append(normalizedList[i])
                    temp.append(item[2])
                    item[2] = adjustType(temp)[1]
                else:
                    if regEx.match(r'^-?\d+(?:\.\d+)?$', item[2]) is None:
                        item[1] = "string"
                    else:
                        item[1] = "float"
            adjustedItemList.append(item)
        i = i + 2
        adjustedList.append(adjustedItemList)

    logger.debug(adjustedList)
    return (adjustedList)


#
# normalize: remove duplicates of the same group.
# input: structure of the IDOC segments as a Python list
# output: normalized structure of the Python list
# to do: change ignoring the duplicates to adding missing fields.
#
def normalize(segments):
    logger.debug(segments)

    normalizedAttributes = []
    length = len(segments)
    i = 0
    while i < length:
        normalizedAttributes.append(segments[i])
        normalizedAttributes.append(normalizeGroup(segments[i + 2]))
        i = i + 3

    logger.debug(normalizedAttributes)
    return (normalizedAttributes)


def normalizeGroup(segments):
    logger.debug(segments)
    normalizedGroup = []

    for segment in segments:
        found = False
        for item in normalizedGroup:
            if item[0] == segment[0]:
                found = True

        if found == False:
            normalizedGroup.append(segment)

    logger.debug(normalizedGroup)
    return normalizedGroup


#
# getAttributesForSegment: create a multi-dimensional list containing the attributes, type, and current value
# input: IDOC XML Document, not parsed
# output: list of the different segments found
#
def getAttributesForSegment(nodeName, segments):
    listOfAttributes = []
    for segment in segments:
        parsedSegment = minidom.parseString(segment)
        if parsedSegment.childNodes[0].nodeName == nodeName:
            for attribute in parsedSegment.childNodes[0].childNodes:
                if (not attribute.firstChild is None):
                    attributeValues = []
                    if (isinstance(attribute, minidom.Text) == False):
                        attributeValues.append(attribute.nodeName)
                        if ord(attribute.firstChild.nodeValue[0]) == 10:
                            attributeType = object
                            attributeValues.append(attributeType)
                            tempAttributeList = []
                            tempAttributeList.append(attribute.toxml())
                            attributeValues.append(getAttributesForSegment(attribute.nodeName, tempAttributeList))
                        else:
                            attributeType = type(attribute.firstChild.nodeValue)
                            attributeValues.append(attributeType)
                            attributeValues.append(attribute.firstChild.nodeValue)
                    listOfAttributes.append(attributeValues)
    return listOfAttributes


#
# getListOfSegments: create a list of all different found segment names of the IDOC
# input: IDOC XML Document, not parsed
# output: list of the different segments found
#
def getListOfSegments(listOfSegments):
    listOfSegmentNames = []

    for segment in listOfSegments:
        parsedSegment = minidom.parseString(segment)

        found = False
        for name in listOfSegmentNames:
            if parsedSegment.childNodes[0].nodeName == name:
                found = True

        if found == False:
            listOfSegmentNames.append(parsedSegment.childNodes[0].nodeName)

    return listOfSegmentNames


def getXMLSegments(xmlFileName):
    # parse an xml file by name
    doc = minidom.parse(xmlFileName)
    groups = doc.getElementsByTagName("IDOC")

    xmlSegments = []

    for group in groups:
        for xmlSegment in group.childNodes:
            if (isinstance(xmlSegment, minidom.Text) == False):
                xmlSegments.append(xmlSegment.toxml())

    return xmlSegments


if __name__ == "__main__":
    FORMAT = '%(asctime)-15s %(name)s %(funcName)s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    logger = logging.getLogger('idoc2raml')

    main()
