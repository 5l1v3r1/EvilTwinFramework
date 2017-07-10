'''
This class is responsible for performing 
the deauthentication attacks, targeted or general
'''

import os
import logging
import traceback
from time import sleep
from threading import Thread, Lock
from utils.utils import DEVNULL
from utils.networkmanager import NetworkCard
from utils.wifiutils import AccessPoint, WiFiClient
from Plugins.deauthenticator import Deauthenticator

class AirInjector(object):

    def __init__(self, targeted_only=False, burst_count=5):
        self.injection_running = False
        self.injection_interface = None

        self._previous_mode = None              # Previous mode to restore network card to
        self._targeted_only = targeted_only     # Flag if we only want to perform targeted deauthentication attacks
        self._burst_count = burst_count         # Number of sequential deuathentication packet bursts to send
        self._ap_targets = set()                # MAC addresses of APs, used to send deauthentication packets to broadcast
        self._client_targets = set()            # Pairs clients to their connected AP to send targeted deauthentication attacks
        self.plugins = []

    def add_ap(self, bssid, ssid, channel):
        deauth_ap = AccessPoint(len(self._ap_targets), ssid, bssid, channel)
        self._ap_targets.add(deauth_ap) # Don't verify duplicates because it's a set

    def add_client(self, client_mac, associated_bssid, associated_ssid):
        deauth_client = WiFiClient(len(self._client_targets), client_mac, associated_bssid, associated_ssid)
        self._client_targets.add(deauth_client) # Don't verify duplicates because it's a set

    def del_aps(self, aps = ()):
        self._ap_targets -= aps

    def del_clients(self, clients = ()):
        self._client_targets -= clients

    def get_ap_targets(self):
        return self._ap_targets

    def get_client_targets(self):
        return self._client_targets

    def add_plugin(self, plugin):
        self.plugins.append(plugin)

    def injection_attack(self):
        # Packet creation based on:
        # https://raidersec.blogspot.pt/2013/01/wireless-deauth-attack-using-aireplay.html
        if len(self.plugins) == 0:
            self.add_plugin(Deauthenticator()) # Deauthentication is default behaviour of injector

        for plugin in self.plugins:
            plugin.interpret_targets(self._ap_targets, self._client_targets)
            plugin.set_injection_interface(self.injection_interface)

        # Launches all added plugins' post injection methods and waits for finish
        self.injection_thread_pool_start("pre_injection")

        # Launches all added plugins' injection attacks and waits for finish
        self.injection_thread_pool_start("inject_packets")
            
        print "[+] Injection attacks finished executing."
        print "[+] Starting post injection methods"

        # Launches all added plugins' post injection methods and waits for finish
        self.injection_thread_pool_start("post_injection")
        del self.plugins[:] # Plugin cleanup for next use
        
        print "[+] Post injection methods finished"

        # Restore state after all threads finishing
        self.injection_running = False
        self._restore_deauthor_state()

    def injection_thread_pool_start(self, plugin_method):
        plugin_threads = []
        for plugin in self.plugins:
            plugin_injection_thread = Thread(target =   plugin.pre_injection if plugin_method == "pre_injection" else
                                                        plugin.inject_packets if plugin_method == "inject_packets" else
                                                        plugin.post_injection)
            plugin_threads.append(plugin_injection_thread)
            plugin_injection_thread.start()

        for thread in plugin_threads:
            thread.join()       # Wait to finish execution
        del plugin_threads[:]   # Cleanup

    def _restore_deauthor_state(self):
        try:
            card = NetworkCard(self.running_interface)
            if card.get_mode().lower() != self._previous_mode:
                card.set_mode(self._previous_mode)
                self._previous_mode = None
        except: pass

        self.running_interface = None

    def start_injection_attack(self, interface):
        # Restart services to avoid conflicts

        self.injection_interface = interface
        card = NetworkCard(interface)
        current_mode = card.get_mode().lower()
        self._previous_mode = current_mode
        if not (current_mode == 'monitor' or current_mode == 'ap'):
            card.set_mode('monitor')

        self.injection_running = True
        injection_thread = Thread(target=self.injection_attack)
        injection_thread.start()


    def stop_injection_attack(self):
        for plugin in self.plugins:
            plugin.should_stop = True # Stop every plugin

    def is_running(self):
        return self.injection_running
