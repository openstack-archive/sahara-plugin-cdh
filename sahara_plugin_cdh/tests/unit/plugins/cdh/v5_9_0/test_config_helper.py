# Copyright (c) 2016 Intel Corporation
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

from sahara_plugin_cdh.plugins.cdh.v5_9_0 import config_helper
from sahara_plugin_cdh.tests.unit.plugins.cdh import base_config_helper_test


class TestConfigHelperV590(base_config_helper_test.TestConfigHelper):

    def setUp(self):
        super(TestConfigHelperV590, self).setUp()
        self.c_h = config_helper.ConfigHelperV590()
        self.path_to_config = 'plugins/cdh/v5_9_0/resources/'
