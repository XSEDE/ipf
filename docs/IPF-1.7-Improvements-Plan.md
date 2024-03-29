IPF 1.7 Improvements Plan

-	Scheduler improvements: 
	-	make all aspects of interaction between IPF and schedulers parameterizable so that changes in the schedulers do not require new IPF code
	-	Fix IPF utilization 
	-	Improve configuration, bootstrapping of position files for monitoring slurmctl.log
-	Modules improvements:
	-	Do not publish modules with a don’t publish flag
-	Configuration and documentation
	-	Refactor IPF configuration  (clarify entire process, add command line parameters to (re)configure single specific workflows)
	-	Top to bottom revision of IPF documentation for clarity and completeness
-	Address keeping ca_certs.pem up to date with XSEDE trusted CAs
-	Move to python-amqp 2.4
-	Internal Release process improvements
	-	Revise test plan to explicitly rely on the end-to-end tests
