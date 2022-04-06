# This script will create a PositionDB file that pre-populates files as 
# completely processed.  Syntax:  
#            python3 pre_populate_position.py position_file files_to_include
import os
import sys

position_file = open(sys.argv[1], "w")

for file in sys.argv[2:]:
    st = os.stat(file)
    ID = "%s-%d" % (st.st_dev, st.st_ino)
    position = "%s %d\n" % (ID,st.st_size)
    position_file.write(position)

position_file.close()

