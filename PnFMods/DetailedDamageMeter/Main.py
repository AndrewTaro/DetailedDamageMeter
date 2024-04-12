API_VERSION = 'API_v1.0'

MOD_NAME = 'DetailedDamageMeter'

try:
    import battle, events, ui
except:
    pass

MAX_LOGS_COUNT = 10
PARAMETER_ID = 'modDetailedDamageMeterEntityIds'


class DetailedDamageMeter(object):

    def __init__(self):
        events.onReceiveShellInfo(self.onReceiveShellInfo)
        events.onBattleStart(self.onBattleStart)
        events.onBattleQuit(self.onBattleQuit)

    def onReceiveShellInfo(self, victimId, shooterId, ammoId, matId, shotId, booleans, damage, shotPosition, yaw, hlinfo):
        # skip shots without damage
        if damage < 1:
            return
        
        victim = battle.getPlayerByVehicleId(victimId)
        shooter = battle.getPlayerByVehicleId(shooterId)
        player = battle.getSelfPlayerInfo()

        damagedPlayer = shooter if player.shipId == victim.shipId else victim
        damageLog = self.__getDamageLog(ammoId, damage, damagedPlayer)

        if player.shipId == victimId:
            self.incomingDamageLogs.update(damageLog)
        elif player.shipId == shooterId:
            self.outgoingDamageLogs.update(damageLog)

    def __getDamageLog(self, ammoId, damage, damagedPlayer):
        """
        Get info about damage (will be sent to flash)
        :type ammoId: long
        :type damage: float
        :type damagedPlayer: PlayerInfo.PlayerInfo
        :return:
        """
        data = self.__getPlayerData(damagedPlayer)
        data['ammoType'] = self.__getAmmoType(ammoId)
        data['lastDamage'] = damage
        data['totalDamage'] = damage
        return data

    def __getPlayerData(self, player):
        """
        Create dict with information about player.
        :type player: PlayerInfo.PlayerInfo
        :rtype: dict
        """
        info = dict(
            victimId=player.id,
            playerName=player.name,
            clanTag=player.clanTag,
            subtype=player.shipInfo.subtype,
            shipNameIDS=player.shipInfo.nameIDS,
        )
        return info

    def __getAmmoType(self, ammoId):
        """
        Get ammo type by ammo id
        :type ammoId: long
        :rtype: str
        """
        ammoInfo = battle.getAmmoParams(ammoId)
        ammoType = ammoInfo.ammoType
        return ammoType

    def onBattleStart(self):
        self.incomingDamageLogs = DamageLogsController()
        self.outgoingDamageLogs = DamageLogsController()

        incomingEntityId = self.incomingDamageLogs.damageLogEntityId
        outgoingEntityId = self.outgoingDamageLogs.damageLogEntityId

        self.parameterEntityId = ui.createUiElement()
        ui.addDataComponent(self.parameterEntityId, {'data': {'outgoingDamageLogEntityId': outgoingEntityId, 'incomingDamageLogEntityId': incomingEntityId}})
        ui.addParameterComponent(self.parameterEntityId, PARAMETER_ID)

    def onBattleQuit(self, arg):
        """
        Called when player leaves battle. Clean damage info here.
        :return:
        """
        self.incomingDamageLogs.kill()
        self.outgoingDamageLogs.kill()
        ui.deleteUiElement(self.parameterEntityId)


class DamageLogsController(object):
    def __init__(self):
        self.damageLogEntityId = ui.createUiElement()
        ui.addDataComponent(self.damageLogEntityId, {'data': {'damageLogs': []}})
        self._damageLogs = []

    def update(self, damageLog):
        currentLogs = self._damageLogs
        if len(currentLogs) > 0 and currentLogs[0]['victimId'] == damageLog['victimId']:
            damageLog = currentLogs[0]
            damageLog['totalDamage'] += damageLog['lastDamage']
            damageLog['lastDamage'] = damageLog['lastDamage']
        else:
            if len(currentLogs) >= MAX_LOGS_COUNT - 1:
                currentLogs.pop()
            currentLogs.insert(0, damageLog)
        # 
        # If you are reading this and trying to copy paste my code
        # Be careful with how objects in DH component are updated
        # 
        # Changes to objects (list, dict, etc) in DH component will not be reflected to Unbound Datahub when the memory address remains the same.
        #
        # e.g.
        #
        # initdict = {}
        # id(initdict) #>> 0L
        # ui.addDataComponent(entityId, {'data': {}})
        # #>> This will be reflected to Ub Datahub
        #
        # somedict = {'key': 'value'}
        # id(somedict) #>> 1L
        # ui.updateUiElementData(entityId, {'data': somedict})
        # #>> This change proeprly triggers dataComponent.evDataChanged event. Because target object's memory address is differnt. (0L => 1L)
        # 
        # somedict['key'] = 'changedvalue'
        # id(somedict) #>> still 1L
        # ui.updateUiElementData(entityId, {'data': somedict})
        # #>> However, this does not trigger evDataChanged, because the address on memory remains unchanged.
        #
        # You MUST create a new instance of the object in order to trigger the update event.
        #
        ui.updateUiElementData(self.damageLogEntityId, {'data': {'damageLogs': list(currentLogs)}})

    def kill(self):
        ui.deleteUiElement(self.damageLogEntityId)
        self._damageLogs = None


detailedDamageMeter = DetailedDamageMeter()