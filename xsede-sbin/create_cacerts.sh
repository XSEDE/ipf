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
mkdir tmp/certificates
cd tmp
tar -xzvxf ../xsede-certs.tar.gz
cd ..
#cp extra_certs/bundle-of-only-in-rabbitmq-certs.pem tmp/certificates
#cp aaa-intermediates-root.crt tmp/certificates
cp usertrust-intermediate-root.pem tmp/certificates
#cp usertrust-root-only.crt tmp/certificates

cp *.crt tmp/certificates/
cat tmp/certificates/*.pem > ca_certs.pem
