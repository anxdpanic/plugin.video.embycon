
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import json

from downloadutils import DownloadUtils
from utils import getArt
from datamanager import DataManager
from simple_logging import SimpleLogging

log = SimpleLogging(__name__)
downloadUtils = DownloadUtils()
dataManager = DataManager()
kodi_version = int(xbmc.getInfoLabel('System.BuildVersion')[:2])

def getWigetContentCast(handle, params):
    log.debug("getWigetContentCast Called" + str(params))
    server = downloadUtils.getServer()

    id = params["id"]
    jsonData = downloadUtils.downloadUrl("{server}/emby/Users/{userid}/Items/" + id + "?format=json",
                                         suppress=False, popup=1)
    result = json.loads(jsonData)
    log.debug("ItemInfo: " + str(result))

    listItems = []
    people = result.get("People")
    if (people != None):
        for person in people:
            #if (person.get("Type") == "Director"):
            #    director = director + person.get("Name") + ' '
            #if (person.get("Type") == "Writing"):
            #    writer = person.get("Name")
            #if (person.get("Type") == "Writer"):
            #    writer = person.get("Name")
            if (person.get("Type") == "Actor"):
                person_name = person.get("Name")
                person_role = person.get("Role")
                person_id = person.get("Id")
                person_tag = person.get("PrimaryImageTag")
                person_thumbnail = downloadUtils.imageUrl(person_id, "Primary", 0, 400, 400, person_tag, server=server)

                if kodi_version > 17:
                    list_item = xbmcgui.ListItem(label=person_name, iconImage=person_thumbnail, offscreen=True)
                else:
                    list_item = xbmcgui.ListItem(label=person_name, iconImage=person_thumbnail)

                if person_role:
                    list_item.setLabel2(person_role)

                itemTupple = ("", list_item, False)
                listItems.append(itemTupple)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)

def getWigetContent(handle, params):
    log.debug("getWigetContent Called" + str(params))
    server = downloadUtils.getServer()

    type = params.get("type")
    if (type == None):
        log.error("getWigetContent type not set")
        return

    settings = xbmcaddon.Addon(id='plugin.video.embycon')
    select_action = settings.getSetting("widget_select_action")

    itemsUrl = ("{server}/emby/Users/{userid}/Items" +
                "?Limit={ItemLimit}" +
                "&format=json" +
                "&ImageTypeLimit=1" +
                "&IsMissing=False")

    if (type == "recent_movies"):
        xbmcplugin.setContent(handle, 'movies')
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=DateCreated" +
                     "&SortOrder=Descending" +
                     "&Filters=IsUnplayed,IsNotFolder" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Movie")
    elif (type == "inprogress_movies"):
        xbmcplugin.setContent(handle, 'movies')
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=DatePlayed" +
                     "&SortOrder=Descending" +
                     "&Filters=IsResumable" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Movie")
    elif (type == "random_movies"):
        xbmcplugin.setContent(handle, 'movies')
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=Random" +
                     "&SortOrder=Descending" +
                     "&Filters=IsUnplayed,IsNotFolder" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Movie")
    elif (type == "recent_episodes"):
        xbmcplugin.setContent(handle, 'episodes')
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=DateCreated" +
                     "&SortOrder=Descending" +
                     "&Filters=IsUnplayed,IsNotFolder" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Episode")
    elif (type == "inprogress_episodes"):
        xbmcplugin.setContent(handle, 'episodes')
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=DatePlayed" +
                     "&SortOrder=Descending" +
                     "&Filters=IsResumable" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Episode")
    elif (type == "nextup_episodes"):
        xbmcplugin.setContent(handle, 'episodes')
        itemsUrl = ("{server}/emby/Shows/NextUp" +
                        "?Limit={ItemLimit}"
                        "&userid={userid}" +
                        "&Recursive=true" +
                        "&format=json" +
                        "&ImageTypeLimit=1")

    log.debug("WIDGET_DATE_URL: " + itemsUrl)

    # get the items
    jsonData = downloadUtils.downloadUrl(itemsUrl, suppress=False, popup=1)
    log.debug("Recent(Items) jsonData: " + jsonData)
    result = json.loads(jsonData)

    if result is None:
        return []

    result = result.get("Items")
    if (result == None):
        result = []

    itemCount = 1
    listItems = []
    for item in result:
        item_id = item.get("Id")
        name = item.get("Name")
        episodeDetails = ""
        log.debug("WIDGET_DATE_NAME: " + name)

        title = item.get("Name")
        tvshowtitle = ""

        if (item.get("Type") == "Episode" and item.get("SeriesName") != None):

            eppNumber = "X"
            tempEpisodeNumber = "0"
            if (item.get("IndexNumber") != None):
                eppNumber = item.get("IndexNumber")
                if eppNumber < 10:
                    tempEpisodeNumber = "0" + str(eppNumber)
                else:
                    tempEpisodeNumber = str(eppNumber)

            seasonNumber = item.get("ParentIndexNumber")
            if seasonNumber < 10:
                tempSeasonNumber = "0" + str(seasonNumber)
            else:
                tempSeasonNumber = str(seasonNumber)

            episodeDetails = "S" + tempSeasonNumber + "E" + tempEpisodeNumber
            name = item.get("SeriesName") + " " + episodeDetails
            tvshowtitle = episodeDetails
            title = item.get("SeriesName")

        art = getArt(item, server, widget=True)

        if kodi_version > 17:
            list_item = xbmcgui.ListItem(label=name, iconImage=art['thumb'], offscreen=True)
        else:
            list_item = xbmcgui.ListItem(label=name, iconImage=art['thumb'])

        # list_item.setLabel2(episodeDetails)
        list_item.setInfo(type="Video", infoLabels={"title": title, "tvshowtitle": tvshowtitle})
        list_item.setProperty('fanart_image', art['fanart'])  # back compat
        list_item.setProperty('discart', art['discart'])  # not avail to setArt
        list_item.setArt(art)
        # add count
        list_item.setProperty("item_index", str(itemCount))
        itemCount = itemCount + 1

        list_item.setProperty('IsPlayable', 'true')

        totalTime = str(int(float(item.get("RunTimeTicks", "0")) / (10000000 * 60)))
        list_item.setProperty('TotalTime', str(totalTime))

        # add progress percent
        userData = item.get("UserData")
        if (userData != None):
            playBackTicks = float(userData.get("PlaybackPositionTicks"))
            if (playBackTicks != None and playBackTicks > 0):
                runTimeTicks = float(item.get("RunTimeTicks", "0"))
                if (runTimeTicks > 0):
                    playBackPos = int(((playBackTicks / 1000) / 10000) / 60)
                    list_item.setProperty('ResumeTime', str(playBackPos))

                    percentage = int((playBackTicks / runTimeTicks) * 100.0)
                    list_item.setProperty("complete_percentage", str(percentage))

        if select_action == "1":
            playurl = "plugin://plugin.video.embycon/?item_id=" + item_id + '&mode=PLAY'
        elif select_action == "0":
            playurl = "plugin://plugin.video.embycon/?item_id=" + item_id + '&mode=SHOW_MENU'

        itemTupple = (playurl, list_item, False)
        listItems.append(itemTupple)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
