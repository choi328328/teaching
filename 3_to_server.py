# %%
# CLI vs GUI

# Terminal, CMD

# SSH, SCP

# tar, gzip, tar.gz, zip...

# Configuration : XML, JSON, YAML, Dataclass (id, pw나 기타 등등 자주 바뀌는 변수들을 담아놓은 별도의 공간) 

# 위 키워드로 검색해서 구글에서 많이 읽어보세요~~
# 특히 SSH, SCP 명령어 잘 기억해놓으세요.

# %%
# 1. SSH connect to server

#pip install paramiko
#pip install scp

import paramiko
from scp import SCPClient
from datetime import datetime
from datetime import timedelta

def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

ssh = createSSHClient('10.5.12.43', '22', 'cbj', 'choi328328')




# %%
# SCP
scp = SCPClient(ssh.get_transport())
base_path = '/home/cbj/ssh_test'
scp.put('test.zip',base_path)

# %%
# unzip

stdin, stdout, stderr=ssh.exec_command(f'unzip {base_path}/test.zip')
lines = stdout.readlines()
print(lines)

# %%
# build
build_command = (
	f"R CMD INSTALL --no-multiarch --with-keep.source {base_path}"
)

# %%
# configuration
from omegaconf import OmegaConf
db_conf = OmegaConf.load('client_conf.yaml').db_conf

# %%
# Make script
project= 'fltest3'
rscript=f'''

library({project})
library(dplyr)
# USER INPUTS
#=======================
# The folder where the study intermediate and result files will be written:
outputFolder <- "{project}Results"

# Specify where the temporary files (used by the ff package) will be created:
options(fftempdir = "./temp")

# Details for connecting to the server:
dbms <- "{db_conf.dbms}"
user <- '{db_conf.user}'
pw <- '{db_conf.pw}'
server <- '{db_conf.server}'
port <- '{db_conf.port}'

downloadJdbcDrivers('{db_conf.dbms}','./{project}')
connectionDetails <- DatabaseConnector::createConnectionDetails(dbms = dbms,
                                                            server = server,
                                                            user = user,
                                                            password = pw,
                                                            port = port,
                                                            pathToDriver='./{project}')

# Add the database containing the OMOP CDM data
cdmDatabaseSchema <- '{db_conf.cdmDatabaseSchema}'
# Add a sharebale name for the database containing the OMOP CDM data
cdmDatabaseName <- '{db_conf.cdmDatabaseName}'
# Add a database with read/write access as this is where the cohorts will be generated
cohortDatabaseSchema <- '{db_conf.cohortDatabaseSchema}'

oracleTempSchema <- NULL

# table name where the cohorts will be generated
cohortTable <- '{project}Cohort'
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
'''

with open('./temp_run.R','w') as f:
    f.write(rscript)



# %%
# transport script
scp = SCPClient(ssh.get_transport())
base_path = '/home/cbj/ssh_test'
scp.put('temp_run.R',f'{base_path}/extras/')

# %%
# run Rscript
stdin, stdout, stderr=ssh.exec_command(f'Rscript {base_path}/extras/temp_run.R')
lines = stdout.readlines()
print(lines)

# %%
# 숙제 : 
# 	다운로드 받은 패키지를 서버로 옮겨서 실행해서 결과까지 확인하는 코드 작성
#	이전 시간에 작성한 Feedernet or ATLAS 코드와 이어지도록 코드 작성해서 순수 파이썬으로 패키지 다운받고 서버로 보내서 실행할 수 있도록 코드 작성


