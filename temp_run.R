

library(fltest3)
library(dplyr)
# USER INPUTS
#=======================
# The folder where the study intermediate and result files will be written:
outputFolder <- "fltest3Results"

# Specify where the temporary files (used by the ff package) will be created:
options(fftempdir = "./temp")

# Details for connecting to the server:
dbms <- "sql server"
user <- 'cbj'
pw <- 'qwer1234!@'
server <- '128.1.99.58'
port <- '1433'

downloadJdbcDrivers('sql server','./fltest3')
connectionDetails <- DatabaseConnector::createConnectionDetails(dbms = dbms,
                                                            server = server,
                                                            user = user,
                                                            password = pw,
                                                            port = port,
                                                            pathToDriver='./fltest3')

# Add the database containing the OMOP CDM data
cdmDatabaseSchema <- 'CDMPv532.dbo'
# Add a sharebale name for the database containing the OMOP CDM data
cdmDatabaseName <- 'AUSOM'
# Add a database with read/write access as this is where the cohorts will be generated
cohortDatabaseSchema <- 'cohortDB.dbo'

oracleTempSchema <- NULL

# table name where the cohorts will be generated
cohortTable <- 'fltest3Cohort'
#=======================

execute(connectionDetails = connectionDetails,
    cdmDatabaseSchema = cdmDatabaseSchema,
    cdmDatabaseName = cdmDatabaseName,
    cohortDatabaseSchema = cohortDatabaseSchema,
    oracleTempSchema = oracleTempSchema,
    cohortTable = cohortTable,
    outputFolder = outputFolder,
    createProtocol = F,
    createCohorts = T,
    runAnalyses = T,
    createResultsDoc = F,
    packageResults = F,
    createValidationPackage = F,  
    #analysesToValidate = 1,
    minCellCount= 5,
    createShiny = F,
    createJournalDocument = F,
    analysisIdDocument = 1)
