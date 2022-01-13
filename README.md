# rotmg_efficient_clear
Tool to help groups efficiently map clear. Should work on all platforms.

Shows all RotMG minimaps with potential hero spawns marked
Overlays your minimap ontop of marked RotMG maps
Networking allows you to share your markers with friends

**How To Install**
There are two ways to "install" this package
1. Pull repository, install packages from requriements.txt (probably a few unnecessary ones) and run with python 3.8.8 (or later)
2. Download the whole package 
    https://mega.nz/file/B4s1WYJC#e4Wlep58WvhDkemnHcr5WVp52mi4Cfq1qPNBOruJVFE (Windows)
    https://mega.nz/file/lkcjXYSB#LqsVv3f3ZVJsoeVGCZwg-IeQUcHG7XP67wUm7AUBoyQ (MacOS)

Once you have it, please make necessary changes to config.ini before running. **You will likely have to change these values: MINIMAP_WIDTH, MINIMAP_HEIGHT, MAP_X, MAP_Y, ROOM.** See bottom for full explanation of config settings.

# Controls:
Space - Toggle pause

Left and Right arrow - cycle through maps

Left Click - Sets marker to green (denotes a hero is alive at this location)

Right Click - Sets marker to red (denotes this location has no hero)

T - Toggles the color of the closest nearby marker (Rebindable in config, a Windows-only feature)

S - Download and sync data from server (This will change your map and markers to what the server has. Use this if you join a run)

U - Uploads your current map data (map number and marker statuses) to the server
For networking the circle at the bottom right should tell you what your status is:
  White - You are not connected to a server
  Green - You are connected to the server; you are on the correct map; your left/right clicks will be uploaded to the server
  Red - You are connected to the server, but not on the right map. You can overwrite the server's data with **U** or sync with **S**


# Peasant Mode: (WINDOWS ONLY)
Enabling this overlays the application ontop of your minimap. You will be able to "click through" the app, so it will not stop you from TP'ing to other players. Since you are unable to click (focus) the app in this mode, there are alternative hotkeys (All changable):

F1 - Pause/Unpause (Pausing the app will automatically hide it)

F2 - Download and sync data from server

F5 - Quit

T - Toggles the color of the closest nearby marker (Rebindable in config, a Windows-only feature)

You cannot change maps or upload while in this mode. This is a feature to prevent players from accidentally screwing up the map while typing.

# config.ini
**GUI_WIDTH and GUI_HEIGHT**
controls the dimensions of the application when you launch it

**GUI_FRESH_RATE**
determines how frequent the the GUI should check for network or overlay updates (in milliseconds). If your computer isn't terrible, you can lower this from 50 to 10.

**USE_NETWORK**
Determines whether or not to use the networking capabilities. Set this to False if you are not collaborating with others.

**SERVER_URL**
The URL of the server. The default one hits a tiny AWS EC2 instance of mine.

**ROOM**
The "room" that you will share with other players. Players in the same room will share each other's data. **Please change this from the default**

**NETWORK_REFRESH_RATE**
How often the app should try to sync the map with the server (milliseconds)

**MAP_WIDTH and MAP_HEIGHT**
are the dimensions of the premade maps. These should not be changed unless you know what you're doing

**MAP_X and MAP_Y**
Where the map starts relative to your monitor. If you have used Ontop Overlay before, you can pull the values from your saved settings.
Common settings:

  1920x1080: MAP_X=1564, MAP_Y=4

  2560x1440: MAP_X=2085, MAP_Y=5
  
**MINIMAP_WIDTH and MINI_MAP_HEIGHT**
The width and height on the rotmg minimap  on your screen
Common settings:

  1920x1080: MINIMAP_WIDTH=352 , MINIMAP_HEIGHT=360

  2560x1440: MINIMAP_WIDTH=468 , MINIMAP_HEIGHT=478
  
**ALPHA**
Transparency of the overlay (0-255)

**OVERLAY_REFRESH_RATE**
How frequently the app should read your map. You can set this to 10 to 60 if you have a decent computer. This value should be higher than **GUI_REFRESH_RATE**

**PEASANT MODE** (WINDOWS ONLY)
Should Peasant Mode be enabled
