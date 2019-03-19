#!/usr/bin/python








###############################################################################
## IMPORT                                                                    ##
###############################################################################
from __future__        import with_statement;

import sys;
import threading;
import mysql;
import time;
import os;
import json;
import io;
import csv;
import subprocess;

from flask import Flask;
from flask import request;


from multiprocessing             import Process, Queue, Lock;








###############################################################################
## DEFINITIONS                                                               ##
###############################################################################
SUCCESS    = 0x0000;
FINISHED   = 0x0001;
DONT_EXIST = 0x0002;
EXIST      = 0x0003;
RUNNING    = 0x0010;
GET_RESULT = 0x0011;
GET_K      = 0x0012;
ERROR      = 0x0013;
FAILED     = 0x0014;

WEB_DEBUG  = "False";
WEB_BIND   = "127.0.0.1";
WEB_PORT   = 9000;







###############################################################################
## PROCEDURES                                                                ##
###############################################################################
##
## BRIEF: log the event description.
## ----------------------------------------------------------------------------
## @PARAM text == text to log.
##
def log(text):

    ## Print text:
    print text;
## END.








###############################################################################
## CLASSES                                                                   ##
###############################################################################
class Instance_Privaaas(Process):

    """
    CLASSE Instance_Privaaas:
    ---------------------------------------------------------------------------
    """

    ###########################################################################
    ## ATTRIBUTES                                                            ##
    ###########################################################################
    status         = RUNNING;
    __instanceID   = None;
    __policy       = None;
    __rwdata       = None;
    storedK        = -1;
    anonymizedData= None;
   

    ###########################################################################
    ## SPECIAL METHODS                                                       ##
    ###########################################################################
    def __init__(self, instanceID, rwdata, policy):
        super(Instance_Privaaas, self).__init__();

        ## Set instance ID:
        self.__instanceID = instanceID;

        self.__rwdata = rwdata;
        self.__policy = policy;


    ###########################################################################
    ## PUBLIC METHODS                                                        ##
    ###########################################################################
    ##
    ## BRIEF: process main loop.
    ## ------------------------------------------------------------------------
    ##
    def run(self):
        while True:
            time.sleep(5);
        return 0;


    ##
    ## BRIEF: execute command.
    ## ------------------------------------------------------------------------
    ##
    def execute(self, k):

        if self.storedK >= k:
            self.status = FINISHED;
        else:    
            self.storedK = k;

            ## Get lines number from buffer;
            bashCommand = [];
            bashCommand.append("java");
            bashCommand.append("-jar");
            bashCommand.append("../PRIVAaaS/dist/PRIVAaaSAllInOneJar.jar");
            bashCommand.append(json.dumps(self.__policy));
            bashCommand.append(str(self.storedK));

            ## Command:
            process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE,
                                           stdin=subprocess.PIPE, shell=False);
        
            for line in self.__rwdata:
                process.stdin.write(line[0]+"\n");

            output, error = process.communicate();
        
            process.stdin.close();
            process.stdout.close();

            self.__parse_return(output, error);

            ## Send to monitor the metrics.
            if self.metrics != {}:
                self.__send_to_monitor();
            else:
                return ERROR;

        return SUCCESS;



    ###########################################################################
    ## PRIVATE METHODS                                                       ##
    ###########################################################################
    ##
    ## BRIEF: perform the parse of json to return.
    ## ------------------------------------------------------------------------
    ## @PARAM dataReceived == data output.
    ## @PARAM dataError    == if there are errors this variable is not empty.
    ## 
    def __parse_return(self, dataReceived, dataError):
        try:
            dataJson = json.loads(dataReceived);

            self.metrics        = dataJson['parameter'];
            self.anonymizedData = dataJson['data'];
        except:
            self.metrics        = {};
            self.anonymizedData = {};
            log(dataError);

            return FAILED;

        return SUCCESS;

    
    ##
    ## BRIEF: send metrics to monitor.
    ## ------------------------------------------------------------------------
    ##
    def __send_to_monitor(self):
        #print self.metrics;
        pass

## END CLASS.








class Handle_PrivaaaS(Process):

    """
    CLASSE Handle_PrivaaaS:
    ---------------------------------------------------------------------------
    """

    ###########################################################################
    ## ATTRIBUTES                                                            ##
    ###########################################################################
    __instances = {};
    webApp         = None;
    __uuid         = 0;



    ###########################################################################
    ## SPECIAL METHODS                                                       ##
    ###########################################################################


    ###########################################################################
    ## PUBLIC METHODS                                                        ##
    ###########################################################################

    ##
    ## BRIEF: process main loop.
    ## ------------------------------------------------------------------------
    ##
    def run(self):
        webApp = Flask(__name__);

        @webApp.route('/', methods=['POST'])
        def process_message_main():

            ## Load json file:
            inputReceived = request.get_json(force=True);

            ## Return Json result:
            return json.dumps('0');


        ## ----------------------------------------------------------------- ##
        ## CREATE request:
        ## ----------------------------------------------------------------- ##
        @webApp.route('/create', methods=['POST'])
        def create():
            ## new UUID.
            self.__uuid += 1;

            ## Parse the python file:
            parsedPolicy = self.__parse_policy_file(request.files['policy']);
            parsedRwData = self.__parse_rwdata_file(request.files['rwdata']);

            ## Get k:
            k = int(request.form['k']);

            ## Case all parameters are ok create a new instance in the system.
            valRet = self.__create(self.__uuid, parsedRwData, parsedPolicy, k);

            ## Return Json result:
            return json.dumps(valRet);

        ## ----------------------------------------------------------------- ##
        ## FINISH request:
        ## ----------------------------------------------------------------- ##
        @webApp.route('/finish', methods=['POST'])
        def finish():

            ## Load json file:
            inputReceived = request.get_json(force=True);

            try:
                instanceID = inputReceived['instanceID'];
            except:
                return json.dumps({"status":1});

            ## Case all parameters are ok create a new instance in the system.
            valRet = self.__finish(instanceID);

            ## Return Json result:
            return json.dumps(valRet);
        
        ## ----------------------------------------------------------------- ##
        ## STATUS request:
        ## ----------------------------------------------------------------- ##
        @webApp.route('/status', methods=['POST'])
        def status():

            ## Load json file:
            inputReceived = request.get_json(force=True);

            try:
                instanceID = inputReceived['instanceID'];
            except:
                return json.dumps({"status":"1"});

            ## Get the instanceID status:
            valRet = self.__status(inputReceived['instanceID']);

            ## Return Json result:
            return json.dumps(valRet);

        ## ----------------------------------------------------------------- ##
        ## LIST request:
        ## ----------------------------------------------------------------- ##
        @webApp.route('/list', methods=['POST'])
        def list():

            ## Print the status from all PRIVAaaS instances running in the sys-
            ## tem.
            valRet = self.__list();

            ## Return Json result:
            return json.dumps(valRet);

        ## ----------------------------------------------------------------- ##
        ## UPDATE K request:
        ## ----------------------------------------------------------------- ##
        @webApp.route('/update_k', methods=['POST'])
        def update_k():
            ## Load json file:
            inputReceived = request.get_json(force=True);

            try:
                instanceID = inputReceived['instanceID'];
            except:
                return json.dumps({"status":"1"});

            ## Get the instanceID status:
            valRet = self.__update_k(inputReceived['instanceID'], 
                                     inputReceived['k']);

            ## Return Json result:
            return json.dumps(valRet);


        ## Run app:
        webApp.run(host=WEB_BIND, port=WEB_PORT);
        return 0;



    ###########################################################################
    ## PRIVATE METHODS                                                       ##
    ###########################################################################
    ##
    ## BRIEF: create and execute a new PRIVAaaS instance.
    ## ------------------------------------------------------------------------
    ## @PARAM instanceId == instance identificator.
    ## @PARAM rwdata     == data to anonymizate.
    ## @PARAM policy     == policy.
    ## @PARAM k          == initial k to be used.
    ##
    def __create(self, instanceID, rwdata, policy, k):
        statusReturn = ERROR;

        instanceID = int(instanceID);

        ## Check if the requestId exist in system (other instace with same re-
        ## quest id is running.
        if self.__check_exist(instanceID) != EXIST:
            self.__instances[instanceID]=Instance_Privaaas(instanceID,
                                                           rwdata,
                                                           policy);
            self.__instances[instanceID].daemon = True;
            self.__instances[instanceID].start();
            self.__instances[instanceID].execute(k);

            statusReturn = SUCCESS;
        else:
            log("Instance with same ID is running! Stop it before create!");
        
        return  {'statusReturn': statusReturn, 'instanceID': instanceID};


    ##
    ## BRIEF: update k received from probe.
    ## ------------------------------------------------------------------------
    ## @PARAM instanceId == instance identificator.
    ## @PARAM k          == k to be used.
    ##
    def __update_k(self, instanceID, k):
        statusReturn = ERROR;

        instanceID = int(instanceID);

        ## Check if the requestId exist in system (other instace with same re-
        ## quest id is running.
        if self.__check_exist(instanceID) != EXIST:
            self.__instances[instanceID].execute(k);

            statusReturn = SUCCESS;
        else:
            log("Instance with same ID is running! Stop it before create!");

        return  {'statusReturn': statusReturn, 'instanceID': instanceID};


    ##
    ## BRIEF: finish instance.
    ## ------------------------------------------------------------------------
    ## @PARAM instanceID == instance identificator.
    ##
    def __finish(self, instanceID):
        status = 1;

        instanceID = int(instanceID);

        ## Verify if the instanceID exist in the system. If EXIST, finish the
        ## instance and remove from system:
        if self.__check_exist(instanceID) == EXIST:
            metrics = self.__instances[instanceID].metrics;
            data    = self.__instances[instanceID].anonymizedData;

            self.__instances[instanceID].terminate();
            self.__instances[instanceID].join();
            del self.__instances[instanceID];

            log("Deleting the instance: " + str(instanceID));

            return { 
                "status"         : 0,
                "metrics"        : metrics,
                "dataAnonymized" : data
             };
        else:
            log("Instance not found...: " + str(instanceID));

        return {"status":status};


    ##
    ## BRIEF: get the instance status.
    ## ------------------------------------------------------------------------
    ## @PARAM instanceID == instance identificator.
    ##
    def __status(self, instanceID):
        instanceID = int(instanceID);

        try:
            status = self.__instances[instanceID].status;
        except:
            ## InstanceID not found in the enviroment, verify the ID.
            status = "notFound";

        ## Return the dictionary:   
        return {"status":status};


    ##
    ## BRIEF: list all instance running.
    ## ------------------------------------------------------------------------
    ##
    def __list(self):
        dictReturn = {};

        ## Get all instances running:
        for key in self.__instances.keys():
            if self.__instances[key].is_alive() == True:
                dictReturn[key] = "running";
            else:
                dictReturn[key] = "finished";

        return dictReturn;


    ##
    ## BRIEF: set instance ID k.
    ## ------------------------------------------------------------------------
    ## @PARAM instanceId == instance identificator.
    ## @PARAM newK       == new k to set.
    ##
    def __update_k(self, instanceID, newK):
        return 0;


    ## 
    ## BRIEF: check if an instance exist.
    ## ------------------------------------------------------------------------
    ## @PARAM instanceId == instance identificator.
    ##
    def __check_exist(self, instanceID):

        if  not self.__instances.has_key(instanceID): 
            return DONT_EXIST;

        else:
            return EXIST;

        return 0;


    ##
    ## BRIEF: get the policy json data.
    ## ------------------------------------------------------------------------
    ## @PARAM fileStorage == json file descriptor.
    ##
    def __parse_policy_file(self, fileStorage):
        stream = io.StringIO(fileStorage.stream.read().decode("UTF8"), newline=None);
        policy = json.load(stream);

        return policy;


    ##
    ## BRIEF: get the data to annonymization.
    ## ------------------------------------------------------------------------
    ## @PARAM fileStorage == csv file descriptor.
    ##
    def __parse_rwdata_file(self, fileStorage):
        stream = io.StringIO(fileStorage.stream.read().decode("UTF8"), newline="\n");
        rwdata = csv.reader(stream);

        return rwdata;
## END CLASS.








###############################################################################
## MAIN                                                                      ##
###############################################################################
if __name__ == "__main__":

    try:
        main = Handle_PrivaaaS();
        main.run();

    except ValueError as exceptionNotice:
        log(exceptionNotice);

    except KeyboardInterrupt:
        main.purge();

    sys.exit(0);

## EOF.