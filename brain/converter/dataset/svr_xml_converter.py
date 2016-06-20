#!/usr/bin/python

'''@svr_xml_converter.py

This file restructures only the supplied dataset(s), from an xml file to a
python dictionary format.

'''

import xmltodict
from brain.validator.validate_dataset import Validate_Dataset
from log.logger import Logger


def svr_xml_converter(raw_data):
    '''@svr_xml_converter

    This method converts the supplied xml file-object to a python dictionary.

    @raw_data, generally a file (or json string) containing the raw dataset(s),
        to be used when computing a corresponding model. If this argument is a
        file, it needs to be closed.

    @list_observation_label, is a list containing dependent variable
        labels.

    '''

    feature_count = None
    list_dataset = []
    list_observation_label = []
    logger = Logger(__name__, 'error', 'error')

    # convert xml file to python 'dict'
    dataset = xmltodict.parse(raw_data)

    # build 'list_dataset'
    for observation in dataset['dataset']['observation']:
        for key in observation:
            if key == 'criterion':
                list_observation_label.append(observation[key])
            elif key == 'predictor':
                for predictor in observation[key]:
                    predictor_label = str(predictor['label'])
                    predictor_value = predictor['value']

                    validate_value = Validate_Dataset(predictor_value)
                    validate_value.validate_value()
                    list_error_value = validate_value.get_errors()
                    if list_error_value:
                        logger.log(list_error_value)
                        return None
                    else:
                        list_dataset.append({
                            'dep_variable_label': observation['criterion'],
                            'indep_variable_label': predictor_label,
                            'indep_variable_value': predictor_value
                        })

        # generalized feature count in an observation
        if not feature_count:
            feature_count = len(observation['predictor'])

    # save observation labels, and return
    raw_data.close()
    return {
        'dataset': list_dataset,
        'observation_labels': list_observation_label,
        'feature_count': feature_count
    }
