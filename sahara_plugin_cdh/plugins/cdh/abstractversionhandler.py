# Copyright (c) 2014 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc

import six

from sahara.plugins import conductor
from sahara.plugins import context
from sahara.plugins import kerberos
from sahara_plugin_cdh.plugins.cdh import db_helper as dh
from sahara_plugin_cdh.plugins.cdh import health


@six.add_metaclass(abc.ABCMeta)
class AbstractVersionHandler(object):

    @abc.abstractmethod
    def get_node_processes(self):
        return

    @abc.abstractmethod
    def get_plugin_configs(self):
        return

    @abc.abstractmethod
    def configure_cluster(self, cluster):
        return

    @abc.abstractmethod
    def start_cluster(self, cluster):
        return

    @abc.abstractmethod
    def validate(self, cluster):
        return

    @abc.abstractmethod
    def scale_cluster(self, cluster, instances):
        return

    @abc.abstractmethod
    def decommission_nodes(self, cluster, instances):
        return

    @abc.abstractmethod
    def validate_scaling(self, cluster, existing, additional):
        return

    @abc.abstractmethod
    def get_edp_engine(self, cluster, job_type):
        return

    @abc.abstractmethod
    def get_edp_job_types(self):
        return []

    @abc.abstractmethod
    def get_edp_config_hints(self, job_type):
        return {}

    @abc.abstractmethod
    def get_open_ports(self, node_group):
        return

    def on_terminate_cluster(self, cluster):
        dh.delete_passwords_from_keymanager(cluster)

    @abc.abstractmethod
    def get_image_arguments(self):
        return NotImplemented

    @abc.abstractmethod
    def pack_image(self, hadoop_version, remote, test_only=False,
                   image_arguments=None):
        pass

    @abc.abstractmethod
    def validate_images(self, cluster, test_only=False, image_arguments=None):
        pass


class BaseVersionHandler(AbstractVersionHandler):

    def __init__(self):
        # Need to be specified in subclass
        self.config_helper = None  # config helper
        self.cloudera_utils = None  # ClouderaUtils
        self.deploy = None  # to deploy
        self.edp_engine = None
        self.plugin_utils = None  # PluginUtils
        self.validation = None  # to validate

    def get_plugin_configs(self):
        result = self.config_helper.get_plugin_configs()
        result.extend(kerberos.get_config_list())
        return result

    def get_node_processes(self):
        return {
            "CLOUDERA": ['CLOUDERA_MANAGER'],
            "HDFS": ['HDFS_NAMENODE', 'HDFS_DATANODE',
                     'HDFS_SECONDARYNAMENODE', 'HDFS_JOURNALNODE'],
            "YARN": ['YARN_RESOURCEMANAGER', 'YARN_NODEMANAGER',
                     'YARN_JOBHISTORY', 'YARN_STANDBYRM'],
            "OOZIE": ['OOZIE_SERVER'],
            "HIVE": ['HIVE_SERVER2', 'HIVE_METASTORE', 'HIVE_WEBHCAT'],
            "HUE": ['HUE_SERVER'],
            "SPARK_ON_YARN": ['SPARK_YARN_HISTORY_SERVER'],
            "ZOOKEEPER": ['ZOOKEEPER_SERVER'],
            "HBASE": ['HBASE_MASTER', 'HBASE_REGIONSERVER'],
            "FLUME": ['FLUME_AGENT'],
            "IMPALA": ['IMPALA_CATALOGSERVER', 'IMPALA_STATESTORE', 'IMPALAD'],
            "KS_INDEXER": ['KEY_VALUE_STORE_INDEXER'],
            "SOLR": ['SOLR_SERVER'],
            "SQOOP": ['SQOOP_SERVER'],
            "SENTRY": ['SENTRY_SERVER'],
            "KMS": ['KMS'],
            "KAFKA": ['KAFKA_BROKER'],

            "YARN_GATEWAY": [],
            "RESOURCEMANAGER": [],
            "NODEMANAGER": [],
            "JOBHISTORY": [],

            "HDFS_GATEWAY": [],
            'DATANODE': [],
            'NAMENODE': [],
            'SECONDARYNAMENODE': [],
            'JOURNALNODE': [],

            'REGIONSERVER': [],
            'MASTER': [],

            'HIVEMETASTORE': [],
            'HIVESERVER': [],
            'WEBCAT': [],

            'CATALOGSERVER': [],
            'STATESTORE': [],
            'IMPALAD': [],
            'Kerberos': [],
        }

    def validate(self, cluster):
        self.validation.validate_cluster_creating(cluster)

    def configure_cluster(self, cluster):
        self.deploy.configure_cluster(cluster)
        conductor.cluster_update(
            context.ctx(), cluster, {
                'info':
                self.cloudera_utils.get_cloudera_manager_info(cluster)})

    def start_cluster(self, cluster):
        self.deploy.start_cluster(cluster)

        self._set_cluster_info(cluster)

    def decommission_nodes(self, cluster, instances):
        self.deploy.decommission_cluster(cluster, instances)

    def validate_scaling(self, cluster, existing, additional):
        self.validation.validate_existing_ng_scaling(cluster, existing)
        self.validation.validate_additional_ng_scaling(cluster, additional)

    def scale_cluster(self, cluster, instances):
        self.deploy.scale_cluster(cluster, instances)

    def _set_cluster_info(self, cluster):
        info = self.cloudera_utils.get_cloudera_manager_info(cluster)
        hue = self.cloudera_utils.pu.get_hue(cluster)
        if hue:
            info['Hue Dashboard'] = {
                'Web UI': 'http://%s:8888' % hue.get_ip_or_dns_name()
            }

        ctx = context.ctx()
        conductor.cluster_update(ctx, cluster, {'info': info})

    def get_edp_engine(self, cluster, job_type):
        oozie_type = self.edp_engine.EdpOozieEngine.get_supported_job_types()
        spark_type = self.edp_engine.EdpSparkEngine.get_supported_job_types()
        if job_type in oozie_type:
            return self.edp_engine.EdpOozieEngine(cluster)
        if job_type in spark_type:
            return self.edp_engine.EdpSparkEngine(cluster)
        return None

    def get_edp_job_types(self):
        return (self.edp_engine.EdpOozieEngine.get_supported_job_types() +
                self.edp_engine.EdpSparkEngine.get_supported_job_types())

    def get_edp_config_hints(self, job_type):
        return self.edp_engine.EdpOozieEngine.get_possible_job_config(job_type)

    def get_open_ports(self, node_group):
        return self.deploy.get_open_ports(node_group)

    def recommend_configs(self, cluster, scaling):
        self.plugin_utils.recommend_configs(
            cluster, self.get_plugin_configs(), scaling)

    def get_health_checks(self, cluster):
        return health.get_health_checks(cluster, self.cloudera_utils)

    def get_image_arguments(self):
        if hasattr(self, 'images'):
            return self.images.get_image_arguments()
        else:
            return NotImplemented

    def pack_image(self, hadoop_version, remote, test_only=False,
                   image_arguments=None):
        if hasattr(self, 'images'):
            self.images.pack_image(
                remote, test_only=test_only, image_arguments=image_arguments)

    def validate_images(self, cluster, test_only=False, image_arguments=None):
        if hasattr(self, 'images'):
            self.images.validate_images(
                cluster, test_only=test_only, image_arguments=image_arguments)
