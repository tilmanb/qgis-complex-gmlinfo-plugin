# -*- coding: utf-8 -*-

"""
pygml for parsing GML files (ISO19136)
"""

__title__ = 'pygml'
__author__ = 'Jürgen Weichand'
__version__ = '0.3.1'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2015 Jürgen Weichand'


from collections import OrderedDict
import logging
from xmltodict import xmltodict
import util
import json

class GmlException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)

class Dataset():

    logformat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logfile = util.getTempfile('pygml.log')
    logging.basicConfig(filename=logfile, level=logging.ERROR, format=logformat)
    logging.debug(dir())

    def __init__(self, filename, resolve_xlink_href=True):

        def is_geometry(key):
            for name in ['geometry', 'position', 'the_geom']:
                if name in key.lower():
                    return True
            return False

        def postprocessor(path, key, value):

            # remove wfs namespace
            key = key.replace('wfs:', '')

            # normalize FeatureCollection, member, featureMember, featureMembers
            if 'feature' in str(key.lower()) or 'member' in str(key.lower()):
                key = key.replace('gml:', '')

            if not is_geometry(key):
                return key, value


        features = {}
        f = open(filename, mode='r')
        logging.info('Open file %s' % filename)
        features = xmltodict.parse(f, postprocessor=postprocessor)

        # logging.info(json.dumps(features, indent=3))

        logging.debug('Container type(%s)' % str(type(features)))
        logging.debug('Container %s' % features.keys()[0])

        # convert single feature (count=1 or maxFeatures=1) to list
        def prepare(features):
            if type(features) == OrderedDict:
                return [features]
            return features


        self.__features = None

        # INSPIRE GML 3.2
        if 'base:SpatialDataSet' in features:
            self.__features = features['base:SpatialDataSet']['base:member']

        # WFS or GML
        if 'FeatureCollection' in features:

            # GML 3.2
            if 'member' in features['FeatureCollection']:
                self.__features = prepare(features['FeatureCollection']['member'])
                try:
                    self.__features.extend(features['FeatureCollection']['additionalObjects']['SimpleFeatureCollection']['member'])
                except KeyError:
                    pass

            # GML 3.1
            if 'featureMembers' in features['FeatureCollection']:
                list = []
                for key in features['FeatureCollection']['featureMembers'].keys():
                    for value in features['FeatureCollection']['featureMembers'][key]:
                        dict = OrderedDict()
                        dict[key] = value
                        list.append(dict)
                self.__features = list

            # GML 2.0
            if 'featureMember' in features['FeatureCollection']:
                self.__features = prepare(features['FeatureCollection']['featureMember'])



        if not self.__features:
            raise GmlException('Unsupported GML-Container!')


        logging.debug('Container type(%s)' % str(type(self.__features)))

        if resolve_xlink_href:
            logging.info('Resolving xlink:href references')
            self.__resolve(self.__features)


    def getFeatures(self):
        logging.debug('getFeatures()')
        logging.debug('type(getFeatures()) = %s' % type(self.__features))
        return self.__features

    def getFeature(self, id):

        logging.debug('getFeature(%s)' % id)

        features = self.getFeatures()
        for feature in features:
            for gml_id in ['@fid', '@gml:id']:
                if gml_id in feature.values()[0]:
                    if feature.values()[0][gml_id] == id:
                        return feature
        return None


    def __resolve(self, value):
        if type(value) == OrderedDict:
            for key, val in sorted(value.items()):
                if 'xlink:href' in key:
                    logging.debug('Resolving %s' % val)
                    val = val.replace('#', '')
                    feature = self.getFeature(val)
                    if feature:
                        logging.debug('Successful resolved %s' % val)
                        # value['@xlink:href'] = feature
                        value['@xlink:href [resolved]'] = feature
                    else:
                        logging.debug('Unable to resolve %s' % val)
                        pass
                else:
                    self.__resolve(val)

        if type(value) == list:
            for val in value:
                self.__resolve(val)