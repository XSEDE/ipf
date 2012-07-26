#!/bin/sh

export PYTHONPATH=@install_dir@/lib

@python@ @install_dir@/libexec/subscribe.py $@
