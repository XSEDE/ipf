
class AccessLatency(object):
    NEARLINE = "nearline"
    OFFLINE = "offline"
    ONLINE = "online"

class AppEnvState(object):
    INSTALLABLE = "installable"
    INSTALLATION_FAILED = "installationfailed"
    INSTALLED_BROKEN = "installedbroken"
    INSTALLED_NOT_VERIFIED = "installednotverified"
    INSTALLED_VERIFIED = "installedverified"
    INSTALLING_AUTOMATICALLY = "installingautomatically"
    INSTALLING_MANUALLY = "installingmanually"
    NON_INSTALLABLE = "noninstallable"
    PENDING_REMOVAL = "pendingremoval"
    REMOVING = "removing"

class ApplicationHandle(object):
    EXECUTABLE = "executable"
    MODULE = "module"
    PATH = "Path"
    SOFTENV = "softenv"
    VALET = "valet"

class Benchmark(object):
    BOGOMIPS = "bogomips"
    CFP2006 = "cfp2006"
    CINT2006 = "cint2006"
    LINPACK = "linpack"
    SPECFP2000 = "specfp2000"
    SPECINT2000 = "specint2000"

class Capability(object):
    DATA_ACCESS_FLATFILES = "data.access.flatfiles"
    DATA_ACCESS_RELATIONAL = "data.access.relational"
    DATA_ACCESS_XML = "data.access.xml"
    DATA_MANAGEMENT_REPLICA = "data.management.replica"
    DATA_MANAGEMENT_STORAGE = "data.management.storage"
    DATA_MANAGEMENT_TRANSFER = "data.management.transfer"
    DATA_NAMING_RESOLVER = "data.naming.resolver"
    DATA_NAMING_SCHEME = "data.naming.scheme"
    DATA_TRANSFER = "data.transfer"
    EXECUTION_MANAGEMENT_CANDIDATE_SET_GENERATOR = "executionmanagement.candidatesetgenerator"
    EXECUTION_MANAGEMENT_DYNAMIC_VM_DEPLOY = "executionmanagement.dynamicvmdeploy"
    EXECUTION_MANAGEMENT_EXECUTION_AND_PLANNING = "executionmanagement.executionandplanning"
    EXECUTION_MANAGEMENT_JOB_DESCRIPTION = "executionmanagement.jobdescription"
    EXECUTION_MANAGEMENT_JOB_EXECUTION = "executionmanagement.jobexecution"
    EXECUTION_MANAGEMENT_JOB_MANAGER = "executionmanagement.jobmanager"
    EXECUTION_MANAGEMENT_RESERVATION = "executionmanagement.reservation"
    INFORMATION_DISCOVERY = "information.discovery"
    INFORMATION_LOGGING = "information.logging"
    INFORMATION_MODEL = "information.model"
    INFORMATION_MONITORING = "information.monitoring"
    INFORMATION_PROVENANCE = "information.provenance"
    INFORMATION_ACCOUNTING = "information.accounting"
    INFORMATION_ATTRIBUTEAUTHORITY = "information.attributeauthority"
    INFORMATION_AUTHENTICATION = "information.authentication"
    INFORMATION_AUTHORIZATION = "information.authorization"
    INFORMATION_CREDENTIALSTORAGE = "information.credentialstorage"
    SECURITY_DELEGATION = "security.delegation"
    SECURITY_IDENTITYMAPPING = "security.identitymapping"

class ComputeActivityState(object):
    BES_FAILED = "bes:failed"
    BES_FINISHED = "bes:finished"
    BES_PENDING = "bes:pending"
    BES_RUNNING = "bes:running"
    BES_TERMINATED = "bes:terminated"

    IPF_PENDING = "ipf:pending"
    IPF_HELD = "ipf:held"
    IPF_STARTING = "ipf:starting"
    IPF_RUNNING = "ipf:running"
    IPF_SUSPENDED = "ipf:suspended"
    IPF_TERMINATING = "ipf:terminating"
    IPF_TERMINATED = "ipf:terminated"
    IPF_FINISHING = "ipf:finishing"
    IPF_FINISHED = "ipf:finished"
    IPF_FAILED = "ipf:failed"
    IPF_UNKNOWN = "ipf:unknown"
    
class ComputingActivityType(object):
    COLLECTION_ELEMENT = "collectionelement"
    PARALLEL_ELEMENT = "parallelelement"
    SINGLE = "single"
    WORKFLOW_NODE = "workflownode"

class ComputingManagerType(object):
    BQS = "bqs"
    CONDOR = "condor"
    FORK = "fork"
    LOADLEVELER = "loadleveler"
    LSF = "lsf"
    OPENPBS = "openpbs"
    SGE = "sungridengine"
    TORQUE = "torque"
    TORQUE_MAUI = "torquemaui"

class ContactType(object):
    GENERAL = "general"
    SECURITY = "security"
    SYSADMIN = "sysadmin"
    USERSUPPORT = "usersupport"

class CPUMultiplicity(object):
    MULTICPU_MULTICORE = "multicpu-multicore"
    MULTICPU_SINGLECORE = "multicpu-singlecore"
    SINGLECPU_MULTICORE = "singlecpu-multicore"
    SINGLECPU_SINGLECORE = "singlecpu-singlecore"

class DataStoreType(object):
    DISK = "disk"
    OPTICAL = "optical"
    TAPE = "tape"

class EndpointHealthState(object):
    CRITICAL = "critical"
    OK = "ok"
    OTHER = "other"
    UNKNOWN = "unknown"
    WARNING = "warning"

class EndpointTechnology(object):
    CORBA = "corba"
    JNDI = "jndi"
    WEB_SERVICE = "webservice"

class ExpirationMode(object):
    NEVER_EXPIRE = "neverexpire"
    RELEASE_WHEN_EXPIRED = "releasewhenexpired"
    WARN_WHEN_EXPIRED = "warnwhenexpired"

class ExtendedBoolean(object):
    FALSE = "false"
    TRUE = "true"
    UNDEFINED = "undefined"

class InterfaceName(object):
    OGF_BES = "ogf.bes"
    OGF_SRM = "ogf.srm"

class JobDescription(object):
    CONDOR = "condor"
    EGEE_JDL = "egee:jdl"
    GLOBUS_RSL = "globus:rsl"
    NORDUGRID_XRSL = "nordugrid:xrsl"
    OGF_JSDL_1_0 = "ogf:jsdl:1.0"

class License(object):
    COMMERCIAL = "commercial"
    OPEN_SOURCE = "opensource"
    UNKNOWN = "unknown"

class NetworkInfo(object):
    HUNDRED_MEGABIT_ETHERNET = "100megabitethernet"
    GIGABIT_ETHERNET = "gigabitethernet"
    INFINIBAND = "infiniband"
    MYRINET = "myrinet"

class OSFamily(object):
    LINUX = "linux"
    MACOSX = "macosx"
    SOLARIS = "solaris"
    WINDOWS = "windows"

class OSName(object):
    AIX = "aix"
    CENTOS = "centos"
    DEBIAN = "debian"
    FEDORA = "fedoracore"
    GENTOO = "gentoo"
    LEOPARD = "leopard"
    LINUX_ROCKS = "linux-rocks"
    MANDRAKE = "mandrake"
    REDHAT_ENTERPRISE = "redhatenterpriseas"
    SCIENTIFIC_LINUX = "scientificlinux"
    SCIENTIFIC_LINUX_CERN = "scientificlinuxcern"
    SUSE = "suse"
    UBUNTU = "ubuntu"
    WINDOWS_VISTA = "windowsvista"
    WINDOWS_XP = "windowsxp"

class ParallelSupport(object):
    MPI = "mpi"
    NONE = "none"
    OPENMP = "openmp"

class Platform(object):
    AMD64 = "amd64"
    I386 = "i386"
    ITANIUM = "itanium"
    POWERPC = "powerpc"
    SPARC = "sparc"

class PolicyScheme(object):
    BASIC = "basic"
    GACL = "gacl"

class QualityLevel(object):
    DEVELOPMENT = "development"
    PRE_PRODUCTION = "pre-production"
    PRODUCTION = "production"
    TESTING = "testing"

class ReservationPolicy(object):
    MANDATORY = "mandatory"
    NONE = "none"
    OPTIONAL = "optional"

class SchedulingPolicy(object):
    FAIR_SHARE = "fairshare"
    FIFO = "fifo"
    RANDOM = "random"

class ServiceType(object):
    GLITE_FTS = "org.glite.fts"
    GLITE_LB = "org.glite.lb"
    GLITE_WMS = "org.glite.wms"
    NORDUGRID_AREX = "org.nordugrid.arex"
    NORDUGRID_ISIS = "org.nordugrid.isis"
    NORDUGRID_STORAGE = "org.nordugrid.storage"
    TERAGRID_GRIDFTP = "org.tergrid.gridftp"
    TERAGRID_CONDORG = "org.teragrid.condor-g"
    TERAGRID_GLOBUS_MDS4 = "org.teragrid.globus-mds4"
    TERAGRID_GPFS = "org.teragrid.gpfs"
    TERAGRID_GSI_OPENSSH = "org.teragrid.gsi-openssh"
    TERAGRID_PREWS_GRAM = "org.teragrid.prewsgram"
    TERAGRID_RFT = "org.teragrid.rft"
    TERAGRID_SRB = "org.teragrid.srb"
    TERAGRID_WS_DELEGATION = "org.teragrid.ws-delegation"
    TERAGRID_WS_GRAM = "org.teragrid.ws-gram"
    TERAGRID_WS_OGSADAI = "org.teragrid.ogsadai"

class ServingState(object):
    CLOSED = "closed"
    DRAINING = "draining"
    PRODUCTION = "production"
    QUEUING = "queuing"

class Staging(object):
    NONE = "none"
    IN = "stagingin"
    INOUT = "staginginout"
    OUT = "stagingout"

class StorageAccessProtocol(object):
    AFS = "afs"
    DCAP = "dcap"
    FILE = "file"
    GSI_DCAP = "gsidcap"
    GSI_FTP = "gsiftp"
    GSI_RFIO = "gsirfio"
    HTTP = "http"
    HTTPS = "https"
    NFS = "nfs"
    RFIO = "rfio"
    ROOT = "root"
    XROOTD = "xrootd"

class StorageCapacity(object):
    ONLINE = "online"
    INSTALLED_ONLINE = "installedonline"
    NEAR_LINE = "nearline"
    INSTALLED_NEAR_LINE = "installednearline"
    OFFLINE = "offline"
    CACHE = "cache"

class StorageManagerType(object):
    CASTOR = "castor"
    DCACHE = "dcache"
    ENSTORE = "enstore"
    GPFS = "gpfs"
    SSE = "sse"
    TSM = "tsm"

class RetentionPolicy(object):
    CUSTODIAL = "custodial"
    OUTPUT = "output"
    REPLICA = "replica"
