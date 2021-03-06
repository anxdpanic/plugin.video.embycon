from uuid import uuid4 as uuid4
import logging
import xbmcaddon
import xbmc
import xbmcgui

log = logging.getLogger("EmbyCon." + __name__)

class ClientInformation():

    def getMachineId(self):
    
        WINDOW = xbmcgui.Window( 10000 )
        
        clientId = WINDOW.getProperty("client_id")
        
        if(clientId == None or clientId == ""):
            log.info("CLIENT_ID - > No Client ID in WINDOW")
            addonSettings = xbmcaddon.Addon(id='plugin.video.embycon')
            clientId = addonSettings.getSetting("client_id")
        
            if(clientId == None or clientId == ""):
                log.info("CLIENT_ID - > No Client ID in SETTINGS")
                uuid = uuid4()
                clientId = "%012X" % uuid
                WINDOW.setProperty("client_id", clientId)
                addonSettings.setSetting("client_id",clientId)
                log.info("CLIENT_ID - > New Client ID : " + clientId)
            else:
                WINDOW.setProperty("client_id", clientId)
                log.info("CLIENT_ID - > Client ID saved to WINDOW from Settings : " + clientId)
                
        return clientId
        
    def getVersion(self):
        version = xbmcaddon.Addon(id="plugin.video.embycon").getAddonInfo("version")
        return version
