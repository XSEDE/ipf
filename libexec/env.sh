
# get the path to the IPF directory using the location of this cript
IPF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"

# assume the messaging toolkit is a sibling of $IPF_DIR and named 'mtk'
MTK_DIR="$( cd $IPF_DIR/../mtk && pwd )"

export PYTHONPATH=$IPF_DIR/lib:$MTK_DIR/lib

# python 2.6 or 2.7 is needed

# loading a module may be needed:
#module load python

# or specifying a specific python executable:
#PYTHON=python2.6
PYTHON=python
