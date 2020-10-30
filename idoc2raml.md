## idoc2raml.py

Convert IDOCs to RAML Schema

#### Syntax:
To run the script, use the following syntax:

`idoc2raml.py -e -d -o="target directory" inputfile`

where the following optional input parameter are used as follows:
- `-d`: debug mode
- `-e`: generate example data structures using the IDOC file
- `-h`: the command line description above as help
- `-o="target directory"`: the output directory if different from the current directory

mandatory parameter:
- `inputfile`: path and file name of the IDOC document (XML file)

#### To Do:

- adding **arrays**: 

#### Directory Structure:
`./idoc2raml` - project directory
`./idoc2raml/tst` - test cases

#### Require Python Packages

- `xml.dom` - hosting the `minidom` package
