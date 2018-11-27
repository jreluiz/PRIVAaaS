#!/usr/bin/env python








###############################################################################
## IMPORT                                                                    ##
###############################################################################
import os;
import json;

from jsonschema import Draft4Validator;
from flask import Flask;
from flask import request;

import logging
import logging.config



logger = logging.getLogger(__name__)
logger.info('Starting Monitor Server Python')






###############################################################################
## DEFINES                                                                   ##
###############################################################################
DEBUG="False"

BIND="0.0.0.0"
PORT=9002








###############################################################################
## PROCEDURES                                                                ##
###############################################################################
app = Flask(__name__)

print "-----------------------------------------------------------------------"
print "Starting Monitor Server Python";
print "-----------------------------------------------------------------------"



##
## BRIEF: Receive messages: 
## ----------------------------------------------------------------------------
##
@app.route('/', methods=['GET', 'POST'])
def process_message_root():
    logger.info('Processing Request %s', str(request))

    ## Reject GET:
    if request.method == 'GET':
        return "Method GET is not supported!"

    ## Load json file:
    input = request.get_json(force=True);

    print "Processing Request " + str(input);

    return validate_schema(input);
## END.





##
## BRIEF: Update the k: 
## ----------------------------------------------------------------------------
##
@app.route('/update', methods=['POST'])
def process_message_update():
    print 'Processing Request ' + str(request);

    if request.method == 'POST':

        ## Load json file:
        try: 
            print request.get_json(force=True);
        except:
            return "Error";

    else:
        return "Method GET is not supported!"

    return "Ok";
## END.






###############################################################################
## MAIN                                                                      ##
###############################################################################
if __name__ == '__main__':
    app.run(debug=DEBUG, host=BIND, port=PORT);

## EOF.