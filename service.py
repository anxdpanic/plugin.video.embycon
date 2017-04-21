# coding=utf-8
# Gnu General Public License - see LICENSE.TXT

import xbmc
import xbmcgui
import xbmcaddon
import time
from datetime import datetime

from resources.lib.websocketclient import WebSocketThread
from resources.lib.downloadutils import DownloadUtils
from resources.lib.simple_logging import SimpleLogging
from resources.lib.play_utils import playFile

log = SimpleLogging("EmbyCon.service")
download_utils = DownloadUtils()

# auth the service
try:
    download_utils.authenticate()
except Exception, e:
    pass

websocket_thread = WebSocketThread()
websocket_thread.setDaemon(True)
websocket_thread.start()


def hasData(data):
    if data is None or len(data) == 0 or data == "None":
        return False
    else:
        return True


def callOnStopAddon(item_id, position):

    try:
        __settings__ = xbmcaddon.Addon(id='plugin.video.embycon')
        on_stop_addon_enabled = __settings__.getSetting('onStopAddonEnabled') == "true"
        addon_to_run = __settings__.getSetting('onStopAddon')
        if on_stop_addon_enabled and addon_to_run:
            log.debug("callOnStopAddon onStopAddon: " + str(addon_to_run))
            param_string = ""
            param_string += "item_id=" + str(item_id)
            param_string += "&position=" + str(position)
            param_string += "&token=" + str(download_utils.authenticate())
            param_string += "&user_id=" + str(download_utils.getUserId())
            log.debug("callOnStopAddon onStopAddon params: " + str(param_string))
            xbmc.executebuiltin("RunAddon(" + addon_to_run + ", " + param_string + ")")

    except Exception as error:
        log.error("callOnStopAddon Error: " + str(error))


def stopAll(played_information):

    if len(played_information) == 0:
        return
        
    log.info("played_information : " + str(played_information))
    
    for item_url in played_information:
        data = played_information.get(item_url)
        if data is not None:
            log.info("item_url  : " + item_url)
            log.info("item_data : " + str(data))
            
            current_position = data.get("currentPossition")
            emby_item_id = data.get("item_id")
            
            if hasData(emby_item_id):
                log.info("Playback Stopped at: " + str(int(current_position * 10000000)))
                websocket_thread.playbackStopped(emby_item_id, str(int(current_position * 10000000)))
                callOnStopAddon(emby_item_id, current_position)
        
    played_information.clear()
    
    
class Service(xbmc.Player):

    played_information = {}
    
    def __init__(self, *args):
        log.info("Starting monitor service: " + str(args))
        self.played_information = {}
        pass
    
    def onPlayBackStarted(self):
        # Will be called when xbmc starts playing a file
        stopAll(self.played_information)
        
        current_playing_file = xbmc.Player().getPlayingFile()
        log.info("onPlayBackStarted: " + current_playing_file)

        window_handle = xbmcgui.Window(10000)
        emby_item_id = window_handle.getProperty("item_id")

        # if we could not find the ID of the current item then return
        if emby_item_id is None or len(emby_item_id) == 0:
            return

        websocket_thread.playbackStarted(emby_item_id)
        
        data = {}
        data["item_id"] = emby_item_id
        self.played_information[current_playing_file] = data
        
        log.info("ADDING_FILE : " + current_playing_file)
        log.info("ADDING_FILE : " + str(self.played_information))

    def onPlayBackEnded(self):
        # Will be called when xbmc stops playing a file
        log.info("EmbyCon Service -> onPlayBackEnded")
        stopAll(self.played_information)

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        log.info("onPlayBackStopped")
        stopAll(self.played_information)

monitor = Service()
last_progress_update = datetime.today()
            
while not xbmc.abortRequested:

    window_handle = xbmcgui.Window(10000)

    if xbmc.Player().isPlaying():
        try:
            # send update
            td = datetime.today() - last_progress_update
            sec_diff = td.seconds
            if sec_diff > 5:
            
                play_time = xbmc.Player().getTime()
                current_file = xbmc.Player().getPlayingFile()
                
                if monitor.played_information.get(current_file) is not None:

                    monitor.played_information[current_file]["currentPossition"] = play_time
            
                if (monitor.played_information.get(current_file) is not None and
                        monitor.played_information.get(current_file).get("item_id") is not None):

                    item_id = monitor.played_information.get(current_file).get("item_id")
                    websocket_thread.sendProgressUpdate(item_id, str(int(play_time * 10000000)))
                    
                last_progress_update = datetime.today()
            
        except Exception, e:
            log.error("Exception in Playback Monitor : " + str(e))
            pass

    else:
        emby_item_id = window_handle.getProperty("play_item_id")
        emby_item_resume = window_handle.getProperty("play_item_resume")
        if emby_item_id and emby_item_resume:
            window_handle.clearProperty("play_item_id")
            window_handle.clearProperty("play_item_resume")
            playFile(emby_item_id, emby_item_resume)

    xbmc.sleep(1000)
    xbmcgui.Window(10000).setProperty("EmbyCon_Service_Timestamp", str(int(time.time())))

# clear user and token when loggin off
WINDOW = xbmcgui.Window(10000)
WINDOW.clearProperty("userid")
WINDOW.clearProperty("AccessToken")
WINDOW.clearProperty("EmbyConParams")

# stop the WebSocket client
websocket_thread.stopClient()

log.info("Service shutting down")
