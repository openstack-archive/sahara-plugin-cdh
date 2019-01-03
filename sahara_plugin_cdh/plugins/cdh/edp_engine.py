# Copyright (c) 2014 Mirantis Inc.
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

from sahara.plugins import edp
from sahara.plugins import exceptions as pl_ex
from sahara.plugins import kerberos
from sahara.plugins import utils as u
from sahara_plugin_cdh.i18n import _


class EdpOozieEngine(edp.PluginsOozieJobEngine):

    def __init__(self, cluster):
        super(EdpOozieEngine, self).__init__(cluster)
        # will be defined in derived classes
        self.cloudera_utils = None

    def get_client(self):
        if kerberos.is_kerberos_security_enabled(self.cluster):
            return super(EdpOozieEngine, self).get_remote_client()
        return super(EdpOozieEngine, self).get_client()

    def get_hdfs_user(self):
        return 'hdfs'

    def create_hdfs_dir(self, remote, dir_name):
        edp.create_dir_hadoop2(remote, dir_name, self.get_hdfs_user())

    def get_oozie_server_uri(self, cluster):
        oozie_ip = self.cloudera_utils.pu.get_oozie(cluster).management_ip
        return 'http://%s:11000/oozie' % oozie_ip

    def get_name_node_uri(self, cluster):
        if len(self.cloudera_utils.pu.get_jns(cluster)) > 0:
            return 'hdfs://%s' % self.cloudera_utils.NAME_SERVICE
        else:
            namenode_ip = self.cloudera_utils.pu.get_namenode(cluster).fqdn()
            return 'hdfs://%s:8020' % namenode_ip

    def get_resource_manager_uri(self, cluster):
        resourcemanager = self.cloudera_utils.pu.get_resourcemanager(cluster)
        return '%s:8032' % resourcemanager.fqdn()

    def get_oozie_server(self, cluster):
        return self.cloudera_utils.pu.get_oozie(cluster)

    def validate_job_execution(self, cluster, job, data):
        oo_count = u.get_instances_count(cluster, 'OOZIE_SERVER')
        if oo_count != 1:
            raise pl_ex.InvalidComponentCountException(
                'OOZIE_SERVER', '1', oo_count)

        super(EdpOozieEngine, self).validate_job_execution(cluster, job, data)


class EdpSparkEngine(edp.PluginsSparkJobEngine):

    edp_base_version = ""

    def __init__(self, cluster):
        super(EdpSparkEngine, self).__init__(cluster)
        self.master = u.get_instance(cluster, "SPARK_YARN_HISTORY_SERVER")
        self.plugin_params["spark-user"] = "sudo -u spark "
        self.plugin_params["spark-submit"] = "spark-submit"
        self.plugin_params["deploy-mode"] = "cluster"
        self.plugin_params["master"] = "yarn-cluster"
        driver_cp = u.get_config_value_or_default(
            "Spark", "Executor extra classpath", self.cluster)
        self.plugin_params["driver-class-path"] = driver_cp

    @classmethod
    def edp_supported(cls, version):
        return version >= cls.edp_base_version

    def validate_job_execution(self, cluster, job, data):
        if not self.edp_supported(cluster.hadoop_version):
            raise pl_ex.PluginInvalidDataException(
                _('Cloudera {base} or higher required to run {type}'
                  'jobs').format(base=self.edp_base_version, type=job.type))

        shs_count = u.get_instances_count(
            cluster, 'SPARK_YARN_HISTORY_SERVER')
        if shs_count != 1:
            raise pl_ex.InvalidComponentCountException(
                'SPARK_YARN_HISTORY_SERVER', '1', shs_count)

        super(EdpSparkEngine, self).validate_job_execution(
            cluster, job, data)
