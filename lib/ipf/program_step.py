
class StepEngine(Engine):
    """This class is used to run a Step as a stand alone process."""
    
    def __init__(self, step):
        Engine.__init__(self)
        self.step = step
        self.handle()
        
    def handle(self):
        parser = optparse.OptionParser(usage="usage: %prog [options] <param=value>*")
        parser.set_defaults(info=False)
        parser.add_option("-i","--info",action="store_true",dest="info",
                          help="output information about this step in JSON")
        (options,args) = parser.parse_args()

        if options.info:
            info = {}
            info["name"] = self.step.name
            info["description"] = self.step.description
            info["time_out"] = self.step.time_out
            info["requires_types"] = self.step.requires_types
            info["produces_types"] = self.step.produces_types
            info["accepts_params"] = self.step.accepts_params
            print(json.dumps(info,sort_keys=True,indent=4))
            sys.exit(0)

        # someone wants to run the step and all arguments are name=value properties

        params = {}
        for arg in args:
            (name,value) = arg.split("=")
            params[name] = value
            
        self.step.setup(self,params)

        self.step_thread = threading.Thread(target=self._runStep)
        self.step_thread.start()
        self.run()

    def _runStep(self):
        try:
            self.step.run()
        except Exception, e:
            self.stepError(self.step,str(e))

    def run(self):
        wait_time = 0.2
        while not sys.stdin.closed and self.step_thread.isAlive():
            try:
                rfds, wfds, efds = select.select([sys.stdin], [], [], wait_time)
            except KeyboardInterrupt:
                sys.stdin.close()
                self.step.noMoreInputs()
            if len(rfds) == 0:
                continue
            
            try:
                document = Document.read(sys.stdin)
                self.step.input(document)
            except ReadDocumentError:
                sys.stdin.close()
                self.step.noMoreInputs()
        self.step_thread.join()

    def output(self, step, document):
        document.source = step.id
        document.write(sys.stdout)

    def error(self, message):
        sys.stderr.write("ERROR: %s\n" % message)

    def warn(self, message):
        sys.stderr.write("WARN: %s\n" % message)

    def info(self, message):
        sys.stderr.write("INFO: %s\n" % message)

    def debug(self, message):
        sys.stderr.write("DEBUG: %s\n" % message)

#######################################################################################################################

class ProgramStep(Step):
    def __init__(self):
        Step.__init__(self)
        self.executable = None
        self.modification_time = None
        self.name = None
        self.description = None
        self.time_out = None
        self.requires_types = []
        self.produces_types = []
        self.accepts_params = {}

    def __eq__(self, other):
        if other == None:
            return False
        return self.executable == other.executable

    def __str__(self):
        sstr = "Step\n"
        sstr += "  name:  %s\n" % self.name
        sstr += "  description: %s\n" % self.description
        sstr += "  executable: %s\n" % self.executable
        sstr += "  time out: %d secs\n" % self.time_out
        sstr += "  requires types:\n"
        for type in self.requires_types:
            sstr += "    %s\n" % type
        sstr += "  produces types:\n"
        for type in self.produces_types:
            sstr += "    %s\n" % type
        sstr += "  accepts parameters:\n"
        for param in self.accepts_params:
            sstr += "    %s: %s\n" % (param,self.accepts_params[param])
        return sstr

    def toJson(self):
        doc = {}
        if self.executable is None:
            raise StepError("executable not specified")
        doc["executable"] = self.executable
        if self.modification_time is None:
            raise StepError("modification time not specified")
        doc["modification_time"] = self.modification_time
        if self.name is not None:
            doc["name"] = self.name
        if self.description is not None:
            doc["description"] = self.description
        if self.time_out is not None:
            doc["time_out"] = self.time_out
        doc["requires_types"] = self.requires_types
        doc["produces_types"] = self.produces_types
        doc["accepts_params"] = self.accepts_params
        return doc

    def fromJson(self, doc):
        try:
            self.executable = doc["executable"]
            self.modification_time = doc["modification_time"]
        except KeyError, e:
            print("didn't find required information for the step: %s" % e)
            raise e
        self.name = doc.get("name")
        self.description = doc.get("description")
        self.time_out = doc.get("time_out")
        self.requires_types = doc.get("requires_types",[])
        self.produces_types = doc.get("produces_types",[])
        self.accepts_params = doc.get("accepts_params",{})
    
    def discover(self, executable):
        self.executable = executable
        
        proc = subprocess.Popen([executable,"-i"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        proc.wait()

        if stderr != "":
            print(stderr)

        if proc.returncode != 0:
            raise StepError("    failed (error code %d)" % (proc.returncode))
            #raise StepError("    failed (error code %d):\n%s" % (proc.returncode,stderr))

        try:
            doc = json.loads(stdout)
        except ValueError, e:
            print("failed to parse step information: %s" % e)
            print(stdout)
            raise e

        #print(json.dumps(doc,sort_keys=True,indent=4))
        try:
            self.name = doc["name"]
            self.description = doc["description"]
            self.time_out = doc["time_out"]
            self.requires_types = doc["requires_types"]
            self.produces_types = doc["produces_types"]
            self.accepts_params = doc["accepts_params"]
        except KeyError, e:
            print("didn't find required information for the step: %s" % e)
            raise e
        #print("    discovered %s" % self)

#######################################################################################################################


class WorkflowStep(Step, threading.Thread):
    def __init__(self, step):
        threading.Thread.__init__(self)
        Step.__init__(self)

        self.executable = prog_step.executable
        self.name = prog_step.name
        self.description = prog_step.description
        self.time_out = prog_step.time_out
        self.requires_types = copy.copy(prog_step.requires_types)
        self.produces_types = copy.copy(prog_step.produces_types)
        self.accepts_params = copy.copy(prog_step.accepts_params)

        self.id = None
        self.params = {}
        self.inputs = Queue.Queue()    # input documents
        self.no_more_inputs_time = None
        self.outputs = {}    # document type -> [step, ...]    used when running the workflow
        self.proc = None

    def __str__(self, indent=""):
        sstr = indent+"Step %s\n" % self.id
        sstr += indent+"  name:  %s\n" % self.name
        sstr += indent+"  description: %s\n" % self.description
        sstr += indent+"  executable: %s\n" % self.executable
        sstr += indent+"  time out: %d secs\n" % self.time_out
        sstr += indent+"  parameters:\n"
        for param in self.params:
            sstr += indent+"    %s: %s\n" % (param,self.params[param])
        sstr += indent+"  requires types:\n"
        for type in self.requires_types:
            sstr += indent+"    %s\n" % type
        sstr += indent+"  outputs types:\n"
        for type in self.outputs:
            for step in self.outputs[type]:
                sstr += indent+"    %s -> %s\n" % (type,step.id)
        return sstr

    def run(self):
        if len(self.outputs) > 0:
            requested_types = None
            for type in self.outputs:
                if requested_types is None:
                    requested_types = type
                else:
                    requested_types += "," + type
            self.params["requested_types"] = requested_types

        command = self.executable
        for name in self.params:
            command += " %s=%s" % (name,self.params[name])

        self.debug("running %s" % command)
        self.proc = subprocess.Popen(command,shell=True,
                                     stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        thread = threading.Thread(target=self._readOutputs)
        thread.start()

        while self.proc.poll() is None:
            try:
                document = self.inputs.get(True,0.25)
                self.debug("writing document to stdin of process")
                document.write(self.proc.stdin)
            except Queue.Empty:
                pass
            if self.no_more_inputs_time != None:
                self.info("closing stdin")
                self.proc.stdin.close()
                break
        self.info("waiting for process to complete")
        while self.proc.poll() is None:
            cur_time = time.time()
            if cur_time - self.no_more_inputs_time > self.time_out:
                self.proc.kill()
                self.error("failed to complete in %d seconds" % self.time_out)
            time.sleep(0.25)

        self.debug("waiting for output thread to complete...")
        thread.join()
        err_msgs = self.proc.stderr.read()
        if err_msgs != "":
            self.error(err_msgs)
        self.info("done")

    def _readOutputs(self):
        try:
            while True:
                doc = Document.read(self.proc.stdout)
                #self.debug("read output document:\n %s" % doc.body)
                self.engine.output(self,doc)
        except ReadDocumentError:
            self.info("no more outputs for step %s" % self.id)
            pass

    def input(self, document):
        self.debug("input received")
        self.inputs.put(document)

    def noMoreInputs(self):
        if self.no_more_inputs_time is None:
            self.no_more_inputs_time = time.time()

#######################################################################################################################
