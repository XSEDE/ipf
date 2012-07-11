
import os
import shutil
import stat
import sys

if len(sys.argv) != 2:
    sys.stderr.write("usage: python install.py <install directory>\n")
    sys.exit(1)

install_path = sys.argv[1]
print("installing to %s" % install_path)

min_version = (2,6)
max_version = (2,9)
if sys.version_info < min_version or sys.version_info > max_version:
    sys.stderr.write("Python version between %d.%d and %d.%d is required\n" %
          (min_version[0],min_version[1],max_version[0],max_version[1]))
    sys.exit(1)

ig=shutil.ignore_patterns("*~","*.pyc","*.pem")

#shutil.copytree("bin",os.path.join(install_path,"bin"),ignore=ig)
shutil.copytree("libexec",os.path.join(install_path,"libexec"),ignore=ig)
shutil.copytree("lib",os.path.join(install_path,"lib"),ignore=ig)
shutil.copytree("etc",os.path.join(install_path,"etc"),ignore=ig)
os.mkdir(os.path.join(install_path,"var"))

os.mkdir(os.path.join(install_path,"bin"))
for name in os.listdir("bin"):
    in_name = os.path.join("bin",name)
    out_name = os.path.join(install_path,"bin",name)
    if in_name.endswith("~"):  # bit of a hack
        continue
    in_file = open(in_name,"r")
    out_file = open(out_name,"w")
    for line in in_file:
        line = line.replace("@install_dir@",install_path)
        line = line.replace("@python@",sys.executable)
        out_file.write(line)
    in_file.close()
    out_file.close()
    shutil.copystat(in_name,out_name)
