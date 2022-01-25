# -*- coding: UTF-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this
# file except in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#

"""
flutter控件管理
"""
import re
import time

from manager import BaseManager
from manager.activitymanager import ActivityManager
from manager.windowmanager import WindowManager
from qt4f.flutterdriver import FlutterDriver


REG_EXP = "Observatory listening on ((http|\/\/)[a-zA-Z0-9:/=_\\-\.\\[\\]]+)"


class FlutterControlManager(BaseManager):
    """
    flutter控件管理
    """

    def __init__(self, device):
        self._device = device
        self._activity_manager = ActivityManager.get_instance(device)
        self._window_manager = WindowManager.get_instance(device)
        self._driver_dict = {}

    @property
    def flutter_driver(self):
        """
        获取flutter driver实例
        """
        ws_addr_or_sock = self.ws_addr_or_sock
        driver = FlutterDriver(ws_addr_or_sock=ws_addr_or_sock)
        return driver


    def _get_ws_address(self, duration=60, interval=1.0):
        """
        获取flutter应用调试地址
        """
        debugger_url_list = []
        time_start = time.time()
        while time.time() - time_start < duration:
            log_list = self._device.adb.get_log(False)
            log_list = [i.decode("utf-8") for i in log_list]
            for item in log_list:
                res = re.search(REG_EXP, item)
                if res:
                    url = res.group(1)
                    debugger_url_list.append(url)
            if len(debugger_url_list) > 0:
                url = debugger_url_list[-1]
                _, domain, port_info =url.split(":")
                port = (url.split(":")[-1]).split("/")[0]
                args = "/".join(url.split(":")[-1].split("/")[1:])
                self._device.adb.forward(int(port), int(port))
                ws = "ws:" + domain + ":" + str(port) + "/" + args + "ws"
                return ws
            time.sleep(interval)
        else:
            raise RuntimeError("Get flutter debugger url error.")

    @property
    def ws_addr_or_sock(self):
        return self._get_ws_address(duration=60)

    def _get_window_process(self, window_hashcode_or_title):
        '''获取窗口所在的进程名
        '''
        from manager.windowmanager import Window
        target_window = None
        pattern = re.compile(r'^\w{6,8}$')
        if isinstance(window_hashcode_or_title, Window):
            target_window = window_hashcode_or_title
            if target_window.attached_window != None:
                target_window = target_window.attached_window
        else:
            is_hashcode = pattern.match(window_hashcode_or_title) != None
            if window_hashcode_or_title == 'StatusBar':
                return 'com.android.systemui'
            for window in self._window_manager.get_window_list():
                if (is_hashcode and window.hashcode == window_hashcode_or_title) or (not is_hashcode and window.title == window_hashcode_or_title):
                    if window.attached_window != None:
                        target_window = window.attached_window
                    else:
                        target_window = window
                    break
            else:
                raise RuntimeError(u'查找窗口： %s 失败' % window_hashcode_or_title)

        for activity in self._activity_manager.get_activity_list():
            if activity.name == target_window.title:
                return activity.process_name

    def find_flutter_view(self, control_dict):
        """
        查找控件树中是否存在flutter控件
        """
        result = []
        for key, control in control_dict.items():
            self._get_control_type(control[1], result)

        for item in result:
            if 'FlutterView' in item:
                return True

    def get_control_tree(self, group_name=""):
        """
        获取flutter相关控件树
        """
        driver = self.flutter_driver
        return driver.get_control_tree(group_name=group_name)

    def get_flutter_control(self, qpath):
        """
        获取flutter控件
        """
        from utils.qpath import QPath
        if isinstance(qpath, str):
            qpath = qpath.encode("utf-8")
        driver = self.flutter_driver
        try:
            controls = driver.find_controls(locator=qpath._parsed_qpath)
            if len(controls) == 0:
                raise RuntimeError("Get control failed.")
            if len(controls) > 1:
                raise RuntimeError("Control is not unique.")
            return controls[0]
        except RuntimeError as e:
            raise e

    def get_control_type(self, window_title):
        """
        获取控件类型
        """
        pass

    def get_flutterview(self):
        """
        获取flutterview实例
        """
        driver = self.flutter_driver
        return FlutterView(driver)



class FlutterView(object):
    """
    FlutterView功能封装
    """

    def __init__(self, driver):
        self._driver = driver
        self._type = self.get_flutterview_type()

    @staticmethod
    def is_flutterview(control_manager):
        """
        是否flutterview控件
        """
        flutterview = FlutterView(control_manager.flutter_driver)
        return flutterview

    def get_flutterview_type(self):
        pass
