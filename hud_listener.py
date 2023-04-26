#!/usr/bin/env python3

import socketio
import json
import argparse
import sys
import os
import time
import curses
from queue import *
from deuces import Card, Evaluator
from pn_simdeck import SimDeck
from pn_player import Player

evaluator = Evaluator()
communityCards = []
playerList = []
debugLogging = False
heroName = ""
gameLogFile = ""
firstGC = True
firstRUP = True
lastGC=""
lastRUP=""

#sio = socketio.Client(engineio_logger=True, logger=True)
sio = socketio.Client()
sio.eio.logger.setLevel("CRITICAL")



def curses_print_communityCards(card_ints):
    global debugLogging
    global stdscr
    global height
    global width
    start_w = 4
    start_h = 3
    try:
        for i in range(len(card_ints)):
            c = card_ints[i]
            suit_int = Card.get_suit_int(c)
            rank_int = Card.get_rank_int(c)
            # if we need to color red
            s = Card.PRETTY_SUITS[suit_int]
            r = Card.STR_RANKS[rank_int]
            if(suit_int == 1):            
                # 's' : 1, # spades
                stdscr.addstr(start_h, start_w, " [" +r+ " " +s+ "] ", curses.color_pair(250) | curses.A_BOLD)
            elif(suit_int == 2):
                # 'h' : 2, # hearts
                stdscr.addstr(start_h, start_w, " [" +r+ " " +s+ "] ", curses.color_pair(161) | curses.A_BOLD)
            elif(suit_int == 4):
                # 'd' : 4, # diamonds
                stdscr.addstr(start_h, start_w, " [" +r+ " " +s+ "] ", curses.color_pair(20) | curses.A_BOLD)
            elif(suit_int == 8):
                # 'c' : 8, # clubs
                stdscr.addstr(start_h, start_w, " [" +r+ " " +s+ "] ", curses.color_pair(47) | curses.A_BOLD)
            #Add width of card each time we add a new one
            start_w = start_w + 7
            stdscr.refresh()
    except Exception as e:
        if(debugLogging):
            writeDebugLog("Exception in Print Comm Cards: " + str(e))
        else:
            pass

def curses_clear_communityCards():
    global stdscr
    global height
    global width
    start_w = 2
    start_h = 3
    stdscr.addstr(start_h, start_w, " " * (width-start_w))
    stdscr.refresh()

def curses_print_allHeaders():
    global stdscr
    #stdscr.addstr(0, 18, " *** L E A D E R B O A R D *** ", curses.color_pair(250) | curses.A_BOLD)
    #stdscr.addstr(1, 2,"=" * 95, curses.color_pair(250) | curses.A_BOLD)
    #headers = str("Handle".ljust(15, ' ')) + " Player ID".ljust(15, ' ')+"\t"+"<STATUS>".ljust(10, ' ')+"\t "+"Stacksize".rjust(13,' ')+" (c)\t"+"Wins".rjust(4,' ')+"\t"+"Rebuys".rjust(4,' ')
    #stdscr.addstr(2, 2, headers, curses.color_pair(250) | curses.A_BOLD)
    #stdscr.addstr(3, 2,"-" * 95, curses.color_pair(250) | curses.A_BOLD)
    #stdscr.refresh()
    stdscr.addstr(1, 12, " *** C O M M U N I T Y *  * C A R D S *** ", curses.color_pair(250) | curses.A_BOLD)
    stdscr.addstr(2, 2, "="*85, curses.color_pair(250) | curses.A_BOLD)
    stdscr.refresh()
    stdscr.addstr(7, 16, " *** P L A Y E R - C A R D S *** ", curses.color_pair(250) | curses.A_BOLD)
    stdscr.addstr(8, 2,"=" * 85, curses.color_pair(250) | curses.A_BOLD)
    stdscr.refresh()
    #stdscr.addstr(38, 18, " *** H A N D - S T A T S *** ", curses.color_pair(250) | curses.A_BOLD)
    #stdscr.addstr(39, 2,"=" * 85, curses.color_pair(250) | curses.A_BOLD)
    #stdscr.refresh()

def drawCard(number, exclude):
    deck = SimDeck()
    i = 0
    drawn_cards = []

    while i != number:
        sample_draw = deck.draw()
        if sample_draw in exclude:
            pass
        else:
            drawn_cards.append(sample_draw)
            i += 1

    return drawn_cards

def curses_print_handStats(playerNumber):
    global stdscr
    global height
    global width
    global playerList
    global heroName
    start_w = 17
    start_h = 9
    if(heroName[0] == str(playerList[playerNumber].get_name())):
        stdscr.addstr(start_h + playerNumber, start_w + (5*len(playerList[playerNumber].get_holecards())) + 35, "{Win Percent: %.1f%%}"% (100 * playerList[playerNumber].get_playerWinChance()), curses.color_pair(47) | curses.A_BOLD)
        stdscr.refresh()
    else:
        stdscr.addstr(start_h + playerNumber, start_w + (5*len(playerList[playerNumber].get_holecards())) + 35, "{Win Percent: %.1f%%}"% (100 * playerList[playerNumber].get_playerWinChance()), curses.color_pair(250) | curses.A_BOLD)
        stdscr.refresh()

def curses_clearHandStats():
    global playerList
    global stdscr
    global width
    start_w = 17
    start_h = 9
    i = 0
    for playerNumber in range(len(playerList)):
        stdscr.addstr(start_h + playerNumber, start_w + (5*len(playerList[playerNumber].get_holecards())) + 35, " "*(width - start_w + (5*len(playerList[playerNumber].get_holecards())) + 35), curses.color_pair(250) | curses.A_BOLD)
        stdscr.refresh()  


def run_handSimulation(card_ints, playerNumber):
    global communityCards
    global playerList
    #simulation_count = 10000
    simulation_count = 5000
    win_count = 0
    runs = 0
    numplayers = len(playerList)
    folded_cards = []
    try:
        for sim in range(simulation_count):
            board_fill = 5 - len(communityCards)
            if(numplayers > 2):
                #Make sure we exclude other players cards (we assume all players fold except main enemy)
                folded_enemies = len(playerList)-2
                folded_cards = drawCard(len(card_ints)*folded_enemies, communityCards + card_ints)
            simulate_board = communityCards + drawCard(board_fill, communityCards + card_ints + folded_cards)
            simulate_hand = drawCard(len(card_ints), simulate_board + card_ints + folded_cards)
            if(len(card_ints) == 2):
                my_score = evaluator.evaluate(simulate_board, card_ints)
                enemy_score = evaluator.evaluate(simulate_board, simulate_hand)
                if my_score < enemy_score:
                    win_count += 1
                runs += 1
            elif(len(card_ints) == 4):
                pass
                #Start Omaha Logic
                #First we calc win percent for every possible combination of 2 cards using holdem logic. 
                #my_score = evaluator.evaluate(simulate_board, card_ints)
                #enemy_score = evaluator.evaluate(simulate_board, simulate_hand)
                #if my_score < enemy_score:
                #    win_count += 1
                #runs += 1
        win_chance = win_count/float(runs)
        playerList[playerNumber].set_playerWinChance(win_chance)
        #Now that we have stored the hand stats let's print them
        curses_print_handStats(playerNumber)                
    except Exception as e:
        if(debugLogging):
            writeDebugLog("Exception in hand sim: " + str(e))
        else:
            pass
        


def curses_print_playerCards(card_ints, playerNumber, handEval):
    global stdscr
    global height
    global width
    global playerList
    global heroName
    start_w = 17
    start_h = 9
    if(str(playerList[playerNumber].get_name()) == "" ): #We dont have a players name
        output = str(playerList[playerNumber].playerID).ljust(15, ' ')
    else:
        output = str(playerList[playerNumber].get_name()).ljust(15, ' ')
    if(heroName[0] == str(playerList[playerNumber].get_name())):
        stdscr.addstr(start_h + playerNumber, start_w-15, output, curses.color_pair(47) | curses.A_BOLD)
    else:
        stdscr.addstr(start_h + playerNumber, start_w-15, output, curses.color_pair(250) | curses.A_BOLD)
    stdscr.refresh()
    ##
    for i in card_ints:
        suit_int = Card.get_suit_int(i)
        rank_int = Card.get_rank_int(i)
        # if we need to color red
        s = Card.PRETTY_SUITS[suit_int]
        r = Card.STR_RANKS[rank_int]
        if(suit_int == 1):            
            # 's' : 1, # spades
            stdscr.addstr(start_h + playerNumber, start_w, "[" +r+ " " +s+ "]", curses.color_pair(250) | curses.A_BOLD)
        elif(suit_int == 2):
            # 'h' : 2, # hearts
            stdscr.addstr(start_h + playerNumber, start_w, "[" +r+ " " +s+ "]", curses.color_pair(161) | curses.A_BOLD)
        elif(suit_int == 4):
            # 'd' : 4, # diamonds
            stdscr.addstr(start_h + playerNumber, start_w , "[" +r+ " " +s+ "]", curses.color_pair(20) | curses.A_BOLD)
        elif(suit_int == 8):
            # 'c' : 8, # clubs
            stdscr.addstr(start_h + playerNumber, start_w, "[" +r+ " " +s+ "]", curses.color_pair(47) | curses.A_BOLD)
        #Add width of card each time we add a new one
        start_w = start_w + 5
        stdscr.refresh()
    #Print Users Hand Evaluation
    if(handEval == ""):
        pass
    else:
        if(heroName[0] == str(playerList[playerNumber].get_name())):
            stdscr.addstr(start_h + playerNumber, start_w + (5 * len(card_ints)) + 3, str("("+handEval+")").ljust(35), curses.color_pair(47) | curses.A_BOLD)
        else:
            stdscr.addstr(start_h + playerNumber, start_w + (5 * len(card_ints)) + 3, str("("+handEval+")").ljust(35), curses.color_pair(250) | curses.A_BOLD)
        stdscr.refresh()

def curses_clear_playerCards():
    global stdscr
    global height
    global width
    global playerList
    start_w = 17
    start_h = 9
    for playerNumber in range(len(playerList)):
        stdscr.addstr(start_h+playerNumber, start_w, " " * 80)
        stdscr.refresh()

def curses_print_leaderboard():
    global stdscr
    global height
    global width
    global playerList
    global heroName
    start_w = 2
    start_h = 4
    for player in playerList:
        output = str(player.get_name()).ljust(15, ' ') + str(" ["+ player.playerID +"]").ljust(15, ' ')+"\t"+str("<" + player.get_playerstatus() +">").ljust(10, ' ')+"\t "+str(player.get_stacksize()).rjust(13,' ')+" (c)"+"\t "+str(player.get_playerWins()).rjust(4,' ')+"\t "+str(player.get_playerRebuys()).rjust(4,' ')
        if(heroName[0] == str(player.get_name())):
            stdscr.addstr(start_h, start_w, output, curses.color_pair(47) | curses.A_BOLD)
        else:
            stdscr.addstr(start_h, start_w, output, curses.color_pair(250) | curses.A_BOLD)
        stdscr.refresh()
        start_h = start_h + 1

def curses_print(x,y,msg):
    global stdscr
    stdscr.addstr(x,y,msg)
    stdscr.refresh()

def curses_print_center(msg):
    global stdscr
    global height
    global width
    start_w = int((width // 2) - (len(msg) // 2) - len(msg) % 2)
    start_h = int((height // 2) - 2)
    stdscr.addstr(start_h,0, msg)
    stdscr.refresh()


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g','--game', dest="game", help='pokernow.club game id if - is first char prefix with /', nargs=1, required=True)
    parser.add_argument('-p', '--player', dest="hero", default='', help='Your Player Handle (enables highlighted user in leaderboard)', nargs=1)
    parser.add_argument('-n', '--npt', dest="npt", default='', help='pokernow.club npt cookie value (copy from browser)', nargs=1)
    parser.add_argument('-a', '--apt', dest="apt", default='', help='pokernow.club apt cookie value (copy from browser)', nargs=1)
    parser.add_argument('-l', '--log', dest="log", default='', help='Enable Game Logging', nargs=1)
    parser.add_argument('-d', '--debug', dest="debug", default=False, action='store_true', help='Enable Debug Logging (saves to ./debug.log)')
    args = parser.parse_args()
    if not args.game and (not args.npt or not args.apt):
        print("You must a gameid and a npt/apt cookie value")
        raise SystemExit(-1)
    return args

class rup(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)

class gameComm(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)   

def getPrintPrettyStr(card_ints):
    output = " "
    for i in range(len(card_ints)):
        c = card_ints[i]
        if i != len(card_ints) - 1:
            output += Card.int_to_pretty_str(c) + ","
        else:
            output += Card.int_to_pretty_str(c) + " "
    return output

def isKnownPlayer(strPlayerID):
    global playerList
    for p in playerList:
        if( p.playerID == strPlayerID):
            return True
    return False

def returnPlayerIndex(strPlayerID):
    global playerList
    count = 0
    for p in playerList:
        if( p.playerID == strPlayerID):
            return count
        count = count + 1
    return -1

def muckCards():
    global playerList
    for p in playerList:
        p.clearHoleCards()
    if(playerList is None):
        time.sleep(2)
    else:    
        time.sleep(5) #simulate muck time
    
def printPlayerList():
    global playerList
    global width
    h = 5
    for player in playerList:
        output = str(player.get_name()) + " ["+ player.playerID +"]\t<" + player.get_playerstatus() +">\t "+str(player.get_stacksize())+" c"
        curses_print(h, 2,output, curses.color_pair(1) | curses.A_BOLD)
        h = h + 1

def writeGameLog(inputStr):
    global gameLogFile
    with open(gameLogFile[0], 'a') as logFile:
        logFile.write(inputStr + '\n')    

def writeDebugLog(inputStr):
    with open("debug.log", 'a') as logFile:
        logFile.write(inputStr + '\n')

#SocketIO Code
@sio.event
def connect():
    pass

@sio.on('gC')
def my_gc_event(data):
    global debugLogging
    global firstGC
    global lastGC
    try:
        if(firstGC):
            firstGC=False
            lastGC = data
            parseGCEvent(data)
        else:
            if(lastGC == data):
                #This is a duplice message we do nothing
                pass
            else:
                lastGC = data
                parseGCEvent(data)
        if(len(playerList) == 0):
            sio.emit("action", data={"type":"RUP"},callback=2)
        # if not sio.connected:
        #     sio.emit("action", data={"type":"RUP"},callback=2)
        #sio.emit("action", data={"type":"RUP"},callback=2)
        sio.sleep(1)
    except Exception as e:
        if(debugLogging):
            writeDebugLog("Exception in GC MAin: " + str(e))
        else:
            pass

def updatePlayerList():
    global debugLogging
    #emit event to update player list
    try:
        sio.emit("action", data={"type":"RUP"},callback=2)
    except Exception as e:
        if(debugLogging):
            writeDebugLog("Exception in Update Player list: " + str(e))
        else:
            pass

@sio.on('rup')
def my_rup_event(data):
    global debugLogging
    global firstRUP
    global lastRUP
    try:
        if(firstRUP):
            firstRUP = False
            lastRUP = data
            myrup = rup(json.dumps(data, default=lambda o: o.__dict__, indent=4))
            parseRUPEvent(myrup)
            return 2
        else:
            if(lastRUP == data):
                #This is a duplice message we do nothing
                pass
            else:
                lastRUP = data
                myrup = rup(json.dumps(data, default=lambda o: o.__dict__, indent=4))
                parseRUPEvent(myrup)
        sio.sleep(1)
    except Exception as e:
        if(debugLogging):
            writeDebugLog("In RUP MAIN: " + str(e))
        else:
            pass


@sio.event
def disconnect():
    pass

def start_server(gameID, cookieVal):
    global debugLogging
    try:
        sio.connect('https://www.pokernow.club/socket.io/?gameID='+gameID, transports="websocket", headers={
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'Upgrade',
        'Host': 'www.pokernow.club',
        'Origin': 'https://www.pokernow.club',
        'Pragma': 'no-cache',
        'Sec-WebSocket-Extensions':'client_max_window_bits',
        'Sec-WebSocket-Version': '13',
        'Upgrade': 'websocket',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
        'Cookie': cookieVal
        })
    except Exception as e:
        if(debugLogging):
            writeDebugLog("Start Server: " + str(e))
        else:
            pass
#END SocketIO Code

def parseRUPEvent(evtData):
    global playerList
    global debugLogging
    # if(debugLogging):
    #     writeDebugLog(str(json.dumps(evtData, default=lambda o: o.__dict__, indent=4)))
    for player in evtData.players.keys():
        if(len(playerList) > 0):
            #Check if Player ID Exists
            if( isKnownPlayer(str(evtData.players[player]['id']))):
                #Get Player Item # so we can update them
                itemNum = returnPlayerIndex(str(evtData.players[player]['id']))
                #Update Player
                playerList[itemNum].set_name(str(evtData.players[player]['name']))
                playerList[itemNum].set_stacksize(evtData.players[player]['stack'])
                playerList[itemNum].set_playerstatus(evtData.players[player]['status'])
            else:
                #Add Player
                p = Player(str(evtData.players[player]['id']))
                p.set_name(str(evtData.players[player]['name']))
                p.set_stacksize(evtData.players[player]['stack'])
                p.set_playerstatus(evtData.players[player]['status'])
                # if not (evtData['players'][player]['winCount'] is None):
                #     p.set_playerWins(int(evtData['players'][player]['winCount']))
                # if not (evtData['players'][player]['quitCount'] is None):
                #     p.set_playerRebuys(int(evtData['players'][player]['quitCount']))
                playerList.append(p)
        else:
            #Add Player
            p = Player(str(evtData.players[player]['id']))
            p.set_name(str(evtData.players[player]['name']))
            if not (evtData.players[player]['stack'] is None):
                p.set_stacksize(evtData.players[player]['stack'])
            if not (evtData.players[player]['status'] is None):
                p.set_playerstatus(evtData.players[player]['status'])
            # if not (evtData['players'][player]['winCount'] is None):
            #     p.set_playerWins(int(evtData['players'][player]['winCount']))
            # if not (evtData['players'][player]['quitCount'] is None):
            #     p.set_playerRebuys(int(evtData['players'][player]['quitCount']))
            playerList.append(p)
    #curses_print_leaderboard()
    
def parseGCEvent(evtData):
    global evaluator
    global communityCards
    global playerList
    global debugLogging
    global gameLogFile
    # if(debugLogging):
    #     writeDebugLog(json.dumps(evtData, default=lambda o: o.__dict__, indent=4))
    if( "pC" in evtData.keys()):
        for player in evtData['pC'].keys():
            if( "cards" in evtData['pC'][player]):
                #Check if playing Holdem
                if( len(evtData['pC'][player]['cards']) == 2):
                    c1 = Card.new(evtData['pC'][player]['cards'][0])
                    c2 = Card.new(evtData['pC'][player]['cards'][1])
                    itemNum = returnPlayerIndex(str(player))
                    try:
                        playerList[itemNum].set_holecards( [ c1, c2 ] )
                        if( len(communityCards) > 2 ):
                            curses_print_communityCards(communityCards)
                            curses_print_playerCards(playerList[itemNum].get_holecards(), itemNum, str(evaluator.class_to_string( evaluator.get_rank_class( evaluator.evaluate(communityCards, playerList[itemNum].get_holecards())))))
                            run_handSimulation(playerList[itemNum].get_holecards(), itemNum)
                            if not (gameLogFile == ''):
                                writeGameLog("Community Cards ("+str(len(communityCards))+"): " + getPrintPrettyStr(communityCards))
                                writeGameLog(str(playerList[itemNum].get_name()) + " Cards: " + getPrintPrettyStr(playerList[itemNum].get_holecards()) + "("+ evaluator.class_to_string( evaluator.get_rank_class( evaluator.evaluate(communityCards, playerList[itemNum].get_holecards() ) ) ) +")")    
                        else: #Pre-Flop
                            curses_print_playerCards(playerList[itemNum].get_holecards(), itemNum, "")
                            #Calculate PreFlop Hand Stats
                            run_handSimulation(playerList[itemNum].get_holecards(), itemNum)
                            if not (gameLogFile == ''):
                                writeGameLog(str(playerList[itemNum].get_name()) + " Cards: " + getPrintPrettyStr(playerList[returnPlayerIndex(str(player))].get_holecards()))
                    except:
                        pass
                #We are playing Omahi Hi/Low
                elif(len(evtData['pC'][player]['cards']) == 4):
                    c1 = Card.new(evtData['pC'][player]['cards'][0])
                    c2 = Card.new(evtData['pC'][player]['cards'][1])
                    c3 = Card.new(evtData['pC'][player]['cards'][2])
                    c4 = Card.new(evtData['pC'][player]['cards'][3])
                    itemNum = returnPlayerIndex(str(player))
                    try:
                        playerList[itemNum].set_holecards( [ c1, c2, c3, c4 ] )
                        if( len(communityCards) > 2 ):
                            # print("Community Cards ("+str(len(communityCards))+"): " + getPrintPrettyStr(communityCards))
                            curses_print_communityCards(communityCards)
                            curses_print_playerCards(playerList[itemNum].get_holecards(), itemNum, "")
                            # print(str(playerList[itemNum].get_name()) + " Cards: " + getPrintPrettyStr(playerList[itemNum].get_holecards()) + "("+ evaluator.class_to_string( evaluator.get_rank_class( evaluator.evaluate(communityCards, playerList[itemNum].get_holecards() ) ) ) +")")
                    except:
                        pass
    if("players" in evtData.keys()):
        try:
            if(type(evtData['players']) is dict):
                for player in evtData['players'].keys():
                    if(isKnownPlayer(player)):
                        #Get Player Item # so we can update them
                        itemNum = returnPlayerIndex(player)
                        if("stack" in evtData['players'][player].keys()):
                            playerList[itemNum].set_stacksize(int(evtData['players'][player]['stack']))
                        if("winCount" in evtData['players'][player].keys()):
                            playerList[itemNum].set_playerWins(int(evtData['players'][player]['winCount']))
                        if("quitCount" in evtData['players'][player].keys()):
                            playerList[itemNum].set_playerRebuys(int(evtData['players'][player]['quitCount']))
        except Exception as e:
            if(debugLogging):
                writeDebugLog("Exception in players: " + str(e))
            else:
                pass
        #curses_print_leaderboard()

    if( "oTC" in evtData.keys()):
        try:
            #Clear Board Cards So we can just add them all
            communityCards.clear()
            for cCard in evtData['oTC']['1']:
                communityCards.append(Card.new(cCard))
            if( len(communityCards) > 2):
                curses_print_communityCards(communityCards)
                if not (gameLogFile == ''):
                    writeGameLog("Community Cards: "+ getPrintPrettyStr(communityCards))
        except Exception as e:
            if(debugLogging):
                writeDebugLog("Exception in OTC: " + str(e))
            else:
                pass
    if("gameResult" in evtData.keys()):
        try:
            if(type(evtData['gameResult']) == dict):
                #When we see gameResult the hand is ended
                if not (gameLogFile == ''):
                    writeGameLog("Hand Complete")
                #Clear Board Cards
                communityCards.clear()
                curses_clear_communityCards()
                #Clear Player Cards
                muckCards()
                curses_clear_playerCards()
                curses_clearHandStats()
                #Request for an update to the players list
                updatePlayerList()
                #Print PlayerList
               # curses_print_leaderboard()
        except Exception as e:
            if(debugLogging):
                writeDebugLog("Exception in gameResult: " + str(e))
            else:
                pass
    #if("cHB" in evtData.keys()):
    #    print("cHB: " + str(json.dumps(evtData['cHB'], default=lambda o: o.__dict__, indent=4)))
    #if("tB" in evtData.keys()):
    #    for player in evtData['tB'].keys():
    #        print(player + " tB: " + str(json.dumps(evtData['tB'][player], default=lambda o: o.__dict__, indent=4)))
            #print(str(player) + " Action: " + str(evtData['tB'][player]))#<D> seems to be N/A, check ==check # is amount bet
    #if("gT" in evtData.keys()):
    #    print("gT" + str(json.dumps(evtData['gT'], default=lambda o: o.__dict__, indent=4)))
    #curses_print_leaderboard()

#Create our Cookie String with APT/NPT values
def getCookieVal(aptVal, nptVal):
    cookieStr=""
    if(aptVal != ''):
        cookieStr +='apt='+aptVal[0]+';'
    if(nptVal != ''):
        cookieStr +='npt='+nptVal[0]+';'
    return cookieStr

def main():
    try:
        # if has been added to prefix game remove it 
        # this is done when game begins with - 
        myGameid = args.game[0].replace("/" , "")
        #sio.start_background_task(start_server(args.game[0], getCookieVal(args.apt, args.npt)))
        sio.start_background_task(start_server(myGameid, getCookieVal(args.apt, args.npt)))
        # sio.wait()
        # Initialization
        stdscr.erase()
        statusbarstr = "Press 'Ctrl+C' to exit | pn_listener v0.1"
        #statusbarstr = myGameid
        # Render status bar
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))
        stdscr.refresh()
        curses_print_allHeaders()
        stdscr.refresh()
        while True:
            stdscr.nodelay(1) # Don't block waiting for input.
            c = stdscr.getch() # Get char from input.  If none is available, will return -1.
            time.sleep(1)
            if c == 3:
                stdscr.refresh()
                raise KeyboardInterrupt
            else:
                curses.flushinp() # Clear out buffer.  We only care about Ctrl+C.      
    except KeyboardInterrupt:
        stdscr.erase()
        stdscr.addstr(int(height/2), int(width/2), "I'm Dying How Are You?", curses.color_pair(161) | curses.A_BOLD)
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))
        stdscr.refresh()
        if( sio.connected ):
            sio.disconnect()
        stdscr.refresh()
    finally:
        stdscr.refresh()
        time.sleep(3) # This delay just so we can see final screen output
        curses.endwin()

if __name__ == '__main__':
    args = parseArgs()
    if not (args.log == ''):
        gameLogFile = args.log
    if(args.debug):
        #Enable Debug Logging
        debugLogging = True
    if not (args.hero == ''):
        heroName = args.hero
    #Start Curses
    stdscr = curses.initscr()
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    stdscr.refresh()
    # Start colors in curses
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
    main()