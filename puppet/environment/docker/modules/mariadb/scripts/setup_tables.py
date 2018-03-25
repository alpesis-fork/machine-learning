#!/usr/bin/python

'''

This file initializes the following database tables within the
'db_machine_learning' database:

    @tbl_dataset_entity, record the dataset instance, and the corresponding
        userid who created, or modified the information, and the model type.

        @model_type, reference table containing all possible model types.

    @tbl_prediction_results, record the prediction result, with respect to the
        corresponding 'model_type' column. The following are associated tables:

        svm model type:

            @tbl_svm_results_class, record predicted classes, with respect
                to a given 'id_result'.
            @tbl_svm_results_probability, record predicted probabilities,
                with respect to a given 'id_result'.
            @tbl_svm_results_decision_function, record predicted decisision
                function, with respect to a given 'id_result'.

        svr model type:

            @tbl_svr_results_results_r2, record predicted r^2, with respect
                to a given 'id_result'.

'''

import yaml
from sys import argv
import MySQLdb as DB


# local variables
#
# @argv[1], first passed-in argument from command (argv[0] is the filename),
#     indicating the project root directory.
#
# @argv[2], second passed-in argument from command, or boolean value
#     indicating if build is vagrant instance.
if argv[2] == 'true':
    prepath = argv[1] + '/hiera'
else:
    prepath = argv[1] + '/hiera/test/hiera'

# yaml configuration: database attributes
with open(prepath + '/database.yaml', 'r') as stream:
    settings = yaml.load(stream)
    database = settings['database']['mariadb']
    db_ml = database['name']
    provisioner = database['provisioner']
    provisioner_password = database['provisioner_password']

# yaml configuration: application attributes
with open(prepath + '/application.yaml', 'r') as stream:
    settings = yaml.load(stream)
    model_types = settings['application']['model_type']
    result_types = settings['application']['result_type']

# yaml configuration: general attributes
with open(prepath + '/common.yaml', 'r') as stream:
    settings = yaml.load(stream)
    host = settings['general']['host']

# create connection
conn = DB.connect(
    host,
    provisioner,
    provisioner_password,
    db_ml
)

with conn:
    # create cursor object
    cur = conn.cursor()

    # ################################################################################# #
    # LEGACY TABLES: these tables will be iteratively phased out, as corresponding      #
    #                backend and frontend are developed.                                #
    # ################################################################################# #

    # create 'tbl_user'
    sql_statement = '''\
                    CREATE TABLE IF NOT EXISTS tbl_user (
                        id_user INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR (50) NOT NULL,
                        email VARCHAR (255) NOT NULL,
                        password VARCHAR (1069) NOT NULL,
                        datetime_joined DATETIME NOT NULL,
                        INDEX (username)
                    );
                    '''
    cur.execute(sql_statement)

    # create 'tbl_dataset_entity'
    sql_statement = '''\
                    CREATE TABLE IF NOT EXISTS tbl_dataset_entity (
                        id_entity INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        title VARCHAR (50) NOT NULL,
                        collection VARCHAR (50) NOT NULL UNIQUE,
                        model_type INT NOT NULL,
                        uid_created INT NOT NULL,
                        datetime_created DATETIME NOT NULL,
                        uid_modified INT NULL,
                        datetime_modified DATETIME NULL,
                        INDEX (id_entity)
                    );
                    '''
    cur.execute(sql_statement)

    # create 'tbl_model_type'
    sql_statement = '''\
                    CREATE TABLE IF NOT EXISTS tbl_model_type (
                        id_model INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        model VARCHAR (50) NOT NULL,
                        INDEX (id_model)
                    );
                    '''
    cur.execute(sql_statement)

    # populate 'tbl_model_type'
    sql_statement = '''\
                    INSERT INTO tbl_model_type (model) VALUES (%s);
                    '''
    cur.executemany(sql_statement, model_types)

    # create 'tbl_prediction_results'
    sql_statement = '''\
                    CREATE TABLE IF NOT EXISTS tbl_prediction_results (
                        id_result INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        model_type INT NOT NULL,
                        title VARCHAR (50) NOT NULL,
                        result VARCHAR (30) NOT NULL,
                        uid_created INT NOT NULL,
                        datetime_created DATETIME NOT NULL,
                        INDEX (title)
                    );
                    '''
    cur.execute(sql_statement)

    # create 'tbl_svm_results_class'
    sql_statement = '''\
                    CREATE TABLE IF NOT EXISTS tbl_svm_results_class (
                        id_class INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        id_result INT NOT NULL,
                        class VARCHAR (50) NOT NULL
                    );
                    '''
    cur.execute(sql_statement)

    # create 'tbl_svm_results_probability'
    sql_statement = '''\
                    CREATE TABLE IF NOT EXISTS tbl_svm_results_probability (
                        id_probability INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        id_result INT NOT NULL,
                        probability DECIMAL (65,12) NOT NULL
                    );
                    '''
    cur.execute(sql_statement)

    # create 'tbl_svm_results_decision_function'
    sql_statement = '''\
                    CREATE TABLE IF NOT EXISTS tbl_svm_results_decision_function (
                        id_decision_function INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        id_result INT NOT NULL,
                        decision_function DECIMAL (65,12) NOT NULL
                    );
                    '''
    cur.execute(sql_statement)

    # create 'tbl_svr_results_r2'
    sql_statement = '''\
                    CREATE TABLE IF NOT EXISTS tbl_svr_results_r2 (
                        id_r2 INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        id_result INT NOT NULL,
                        r2 DECIMAL (65,12) NOT NULL
                    );
                    '''
    cur.execute(sql_statement)

    # ################################################################################# #
    # NEW STRUCTURE: when the above legacy tables have been completely phased out, the  #
    #                below tables will completely define our sql implementation.        #
    # ################################################################################# #

    # ################################################################################# #
    #                                                                                   #
    # stored functions: time based uuid                                                 #
    #                                                                                   #
    # Note: https://mariadb.com/kb/en/library/guiduuid-performance/#code-to-do-it       #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            CREATE FUNCTION UuidToBin(_uuid BINARY(36))
                RETURNS BINARY(16)
                LANGUAGE SQL  DETERMINISTIC  CONTAINS SQL  SQL SECURITY INVOKER
            RETURN
                UNHEX(CONCAT(
                    SUBSTR(_uuid, 15, 4),
                    SUBSTR(_uuid, 10, 4),
                    SUBSTR(_uuid,  1, 8),
                    SUBSTR(_uuid, 20, 4),
                    SUBSTR(_uuid, 25)
                ));
            '''
    cur.execute(query)

    query = '''\
            CREATE FUNCTION UuidFromBin(_bin BINARY(16))
                RETURNS BINARY(36)
                LANGUAGE SQL  DETERMINISTIC  CONTAINS SQL  SQL SECURITY INVOKER
            RETURN
                LCASE(CONCAT_WS('-',
                    HEX(SUBSTR(_bin,  5, 4)),
                    HEX(SUBSTR(_bin,  3, 2)),
                    HEX(SUBSTR(_bin,  1, 2)),
                    HEX(SUBSTR(_bin,  9, 2)),
                    HEX(SUBSTR(_bin, 11))
                )
            );
            '''
    cur.execute(query)

    # ################################################################################# #
    #                                                                                   #
    # user and roles                                                                    #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            CREATE TABLE IF NOT EXISTS Account (
                UserID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                Username VARCHAR (50) NOT NULL,
                Password VARCHAR (1069) NOT NULL,
                Joined DATETIME NOT NULL
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS Role (
                RoleID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                Role VARCHAR (50) NOT NULL,
                UserID INT NOT NULL,
                FOREIGN KEY (UserID) REFERENCES Account(UserID)
            );
            '''
    cur.execute(query)

    # ################################################################################# #
    #                                                                                   #
    # general permission                                                                #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            CREATE TABLE IF NOT EXISTS PermissionUUID (
                PermissionUUID BINARY(16) NOT NULL PRIMARY KEY,
                PermissionType INT NOT NULL
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS OwnUUID (
                OwnUUID BINARY(16) NOT NULL PRIMARY KEY,
                OwnType INT NOT NULL
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS Own (
                OwnID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                OwnUUID BINARY(16) NOT NULL,
                UserID INT NOT NULL,
                PRIMARY KEY (OwnUUID, UserID),
                FOREIGN KEY (OwnUUID) REFERENCES PermissionUUID(OwnUUID),
                FOREIGN KEY (UserID) REFERENCES Account(UserID),
            );
                    '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS PermissionValue (
                PermissionUUID BINARY(16) NOT NULL,
                Code INT NOT NULL,
                PRIMARY KEY (PermissionUUID, Code),
                FOREIGN KEY (PermissionUUID) REFERENCES PermissionUUID(PermissionUUID)
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS Permission (
                PermissionUUID BINARY(16) NOT NULL,
                UserID INT NOT NULL,
                PermissionType INT NOT NULL,
                PRIMARY KEY (PermissionUUID, UserID, PermissionType),
                FOREIGN KEY (PermissionUUID) REFERENCES PermissionUUID(PermissionUUID),
                FOREIGN KEY (UserID) REFERENCES Account(UserID)
            );
            '''
    cur.execute(query)

    # ################################################################################# #
    #                                                                                   #
    # applied permission                                                                #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            CREATE TABLE IF NOT EXISTS PermissionCollection (
                PermissionUUID BINARY(16) NOT NULL,
                OwnID INT NOT NULL,
                PRIMARY KEY (PermissionUUID, OwnUUID),
                FOREIGN KEY (PermissionUUID) REFERENCES PermissionUUID(PermissionUUID),
                FOREIGN KEY (OwnID) REFERENCES Own(OwnID)
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS PermissionModel (
                PermissionUUID BINARY(16) NOT NULL,
                OwnID INT NOT NULL,
                PRIMARY KEY (PermissionUUID, OwnUUID),
                FOREIGN KEY (PermissionUUID) REFERENCES PermissionUUID(PermissionUUID),
                FOREIGN KEY (OwnID) REFERENCES Own(OwnID),
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS PermissionResult (
                PermissionUUID BINARY(16) NOT NULL,
                OwnID INT NOT NULL,
                PRIMARY KEY (PermissionUUID, OwnUUID),
                FOREIGN KEY (PermissionUUID) REFERENCES PermissionUUID(PermissionUUID),
                FOREIGN KEY (OwnID) REFERENCES Own(OwnID),
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS Collection (
                OwnUUID BINARY(16) NOT NULL,
                CollectionName VARCHAR (50) NOT NULL,
                CollectionVersion INT NOT NULL,
                FOREIGN KEY (OwnUUID) REFERENCES OwnUUID(OwnUUID),
                PRIMARY KEY (OwnUUID, CollectionName)
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS Model (
                OwnUUID BINARY(16) NOT NULL,
                ModelName VARCHAR (50) NOT NULL,
                Model BLOB NOT NULL,
                FOREIGN KEY (OwnUUID) REFERENCES OwnUUID(OwnUUID),
                PRIMARY KEY (OwnUUID, ModelName)
            );
            '''
    cur.execute(query)

    # ################################################################################# #
    #                                                                                   #
    # model                                                                             #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            CREATE TABLE IF NOT EXISTS ModelType (
                ModelTypeID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                ModelType VARCHAR (50) NOT NULL
            );
            '''
    cur.execute(query)

    # ################################################################################# #
    #                                                                                   #
    # results                                                                           #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            CREATE TABLE IF NOT EXISTS ResultLabel (
                ResultLabelID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                ResultLabel VARCHAR (50) NOT NULL
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS ResultValue (
                ResultValueID INT NOT NULL PRIMARY KEY,
                ResultValueActual DECIMAL (65,12) NOT NULL,
                ResultLabelID INT NOT NULL,
                PRIMARY KEY (ResultValueActual, ResultLabelID),
                FOREIGN KEY (ResultLabelID) REFERENCES ResultLabel(ResultLabelID)
            );
            '''
    cur.execute(query)

    query = '''\
            CREATE TABLE IF NOT EXISTS Result (
                OwnUUID BINARY(16) NOT NULL,
                ResultValueID INT NOT NULL,
                ModelTypeID INT NOT NULL,
                PRIMARY KEY (OwnUUID, ResultValueID, ModelTypeID),
                FOREIGN KEY (OwnUUID) REFERENCES OwnUUID(OwnUUID),
                FOREIGN KEY (ResultValueID) REFERENCES ResultValue(ResultValueID),
                FOREIGN KEY (ModelTypeID) REFERENCES ModelType(ModelTypeID)
            );
            '''
    cur.execute(query)

    # ################################################################################# #
    #                                                                                   #
    # populate OwnUUID                                                                  #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            INSERT INTO OwnUUID (OwnUUID, OwnType)
            VALUES (UuidToBin(UUID()), 'Collection');
            '''
    cur.executemany(query)

    query = '''\
            INSERT INTO OwnUUID (OwnUUID, OwnType)
            VALUES (UuidToBin(UUID()), 'Model');
            '''
    cur.executemany(query)

    query = '''\
            INSERT INTO OwnUUID (OwnUUID, OwnType)
            VALUES (UuidToBin(UUID()), 'Result');
            '''
    cur.executemany(query)

    # ################################################################################# #
    #                                                                                   #
    # populate PermissionUUID                                                           #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            INSERT INTO PermissionUUID (PermissionUUID, OwnType)
            VALUES (UuidToBin(UUID()), 'Collection');
            '''
    cur.executemany(query)

    query = '''\
            INSERT INTO PermissionUUID (PermissionUUID, OwnType)
            VALUES (UuidToBin(UUID()), 'Model');
            '''
    cur.executemany(query)

    query = '''\
            INSERT INTO PermissionUUID (PermissionUUID, OwnType)
            VALUES (UuidToBin(UUID()), 'Result');
            '''
    cur.executemany(query)

    # ################################################################################# #
    #                                                                                   #
    # populate ModelType                                                                #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            INSERT INTO ModelType (ModelType) VALUES (%s);
            '''
    cur.executemany(query, model_types)

    # ################################################################################# #
    #                                                                                   #
    # populate ResultLabel                                                              #
    #                                                                                   #
    # ################################################################################# #
    query = '''\
            INSERT INTO ResultLabel (ResultLabel) VALUES (%s);
            '''
    cur.executemany(query, result_types)
