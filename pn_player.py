
class Player:
    "Player Class for pn_listener"
    playerID = ""
    playerStatus = "unknown"
    playerName = ""
    playerHand = []
    playerWinChance = 0.0
    playerStackSize = 0
    playerWins = 0
    playerRebuys = 0
    playerMuting = []

    def __init__(self, playerID):
        self.playerID = playerID
    
    def set_name(self, pName):
        self.playerName = pName
    
    def get_name(self):
        return self.playerName
    
    def set_stacksize(self, stack):
        self.playerStackSize = stack

    def get_stacksize(self):
        return self.playerStackSize

    def clearHoleCards(self):
        self.playerHand.clear()

    def set_holecards(self, holeCardList):
        self.playerHand = holeCardList

    def get_holecards(self):
        return self.playerHand

    def set_muting(self, muteList):
        self.playerMuting = muteList

    def get_muting(self):
        return self.playerMuting


    def get_playerstatus(self):
        return self.playerStatus

    def set_playerstatus(self, pStatus):
        self.playerStatus = pStatus

    def set_playerWinChance(self, winChance):
        self.playerWinChance = winChance
    
    def get_playerWinChance(self):
        return self.playerWinChance

    def set_playerWins(self, wins):
        self.playerWins = wins
    
    def get_playerWins(self):
        return self.playerWins

    def set_playerRebuys(self, rebuys):
        self.playerRebuys = rebuys
    
    def get_playerRebuys(self):
        return self.playerRebuys