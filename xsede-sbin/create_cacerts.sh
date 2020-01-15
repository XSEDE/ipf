#!/bin/bash

wget https://software.xsede.org/security/xsede-certs.tar.gz
wget https://software.xsede.org/security/xsede-certs.tar.gz.sig
gpg xsede-certs.tar.gz.sig | grep "Good signature"
retval=$?
if [ $? -eq 0 ];
then echo $?
echo "good sig"
else echo "bad signature on certs tarball"
exit 1
fi

echo continuing
mkdir tmp
cd tmp
tar -xzvxf ../xsede-certs.tar.gz
cd ..
cat tmp/certificates/*.pem > ca_certs.pem
