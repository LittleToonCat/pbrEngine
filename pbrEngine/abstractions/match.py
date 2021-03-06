'''
Created on 22.09.2015

@author: Felk
'''

import logging
from copy import deepcopy

from ..util import invertSide, swap, EventHook, sanitizeTeamIngamenames

logger = logging.getLogger("pbrEngine")
dlogger = logging.getLogger("pbrDebug")

class Match(object):
    def __init__(self, timer):
        self._timer = timer
        '''
        Event of a pokemon fainting.
        arg0: <side> "blue" or "red"
        arg2: <slot> team index of the dead pokemon
        '''
        self.on_faint = EventHook(side=str, slot=int)
        self.on_win = EventHook(winner=str)
        self.on_switch = EventHook(side=str, slot_active=int, slot_inactive=int)

        self._check_greenlet = None
        self._lastMove = ("blue", "")

    def new(self, teams, fDoubles):
        self._fDoubles = fDoubles
        sanitizeTeamIngamenames(teams)
        pkmn_blue, pkmn_red = teams

        # Switches during gameplay cause the ingame team order to deviate from the
        # starting team order. The ingame order is what actually determines which button
        # maps to which Pokemon.

        # These fields keep teams in their ingame order.
        self.teams = {"blue": list(pkmn_blue), "red": list(pkmn_red)}
        self.teamsLive = deepcopy(self.teams)
        self.areFainted = {"blue": [False] * len(pkmn_blue), "red": [False] * len(pkmn_red)}

        # This maps a pkmn's ingame order slot to its starting order slot. Both are
        # 0-indexed. Ex:
        # <slot at start of match> = self.slotSOMap[side][<current ingame slot>]
        self.slotSOMap = {"blue": list(range(len(pkmn_blue))),
                          "red": list(range(len(pkmn_red)))}

    def teamsCopy(self):
        return {"blue": list(self.teams["blue"]), "red": list(self.teams["red"])}

    def getFrozenSlotConverter(self):
        slotSOMap = deepcopy(self.slotSOMap)
        def frozenSlotConverter(convertTo, slotOrTeamOrTeams, side=None):
            return self.slotConvert(convertTo, slotOrTeamOrTeams, side, slotSOMap)
        return frozenSlotConverter

    def slotConvert(self, convertTo, slotOrTeamOrTeams, side=None, slotSOMap=None):
        convertTo = convertTo.upper()
        convertTo = ("SO" if convertTo == "STARTING" else
                     "IGO" if convertTo == "INGAME" else convertTo)
        slotSOMap = slotSOMap or self.slotSOMap
        assert convertTo in ("SO", "IGO"), "conversion must be SO or IGO"
        if isinstance(slotOrTeamOrTeams, dict):
            if side:
                raise ValueError("Side may not be specified when value is a dict")
            teams_in = slotOrTeamOrTeams
            teams_out = {"blue": [], "red": []}
            for side in ("blue", "red"):
                if convertTo == "SO":
                    teams_out[side] = [teams_in[side][slotSOMap[side].index(slotSO)]
                                       for slotSO in range(len(teams_in[side]))]
                else:
                    teams_out[side] = [teams_in[side][slotSOMap[side][slotIGO]]
                                       for slotIGO in range(len(teams_in[side]))]
            return teams_out
        elif isinstance(slotOrTeamOrTeams, list):
            team_in = slotOrTeamOrTeams
            assert side, "Side must be specified when value is a list"
            if convertTo == "SO":
                return [team_in[slotSOMap[side].index(slotSO)]
                        for slotSO in range(len(team_in))]
            else:
                return [team_in[slotSOMap[side][slotIGO]]
                        for slotIGO in range(len(team_in))]
        elif isinstance(slotOrTeamOrTeams, int):
            slot = slotOrTeamOrTeams
            assert side, "Side must be specified when value is an int"
            if convertTo == "SO":
                return slotSOMap[side][slot]
            else:
                return slotSOMap[side].index(slot)
        else:
            raise ValueError("value must be of type int, list, or dict")

    def setLastMove(self, side, move):
        self._lastMove = (side, move)

    def switchesAvailable(self, side):
        '''
        Returns the ingame slots of the Pokemon available to switch to for this team.
        Basically fainted pokemon minus the current ones.  Does not include effects of
        arena trap, etc.
        '''
        return [
            not is_fainted and
            not slot == 0 and                  # already in battle
            not (slot == 1 and self._fDoubles) # already in battle
            for slot, is_fainted in enumerate(self.areFainted[side])
        ]

    def fainted(self, side, pkmn_name):
        slot = self.getSlotFromIngamename(side, pkmn_name)
        if slot is None:
            logger.error("Didn't recognize pokemon name: {} ", pkmn_name)
            return
        elif self.areFainted[side][slot]:
            logger.error("{} ({} {}) fainted, but was already marked as fainted"
                         .format(pkmn_name, side, slot))
            return
        self.areFainted[side][slot] = True
        self.on_faint(side=side, slot=slot)
        self.update_winning_checker()

    def update_winning_checker(self):
        '''Initiates a delayed win detection.
        Has to be delayed, because there might be followup-deaths.'''
        if all(self.areFainted["blue"]) or all(self.areFainted["red"]):
            # kill already running wincheckers
            if self._check_greenlet and not self._check_greenlet.ready():
                self._check_greenlet.kill()
            # 11s delay = enough time for swampert (>7s death animation) to die
            self._check_greenlet = self._timer.spawn_later(660, self.checkWinner)

    def getSlotFromIngamename(self, side, pkmn_name):
        # Returns the slot of the pokemon with this name.
        for i, v in enumerate(self.teams[side]):
            if v["ingamename"] == pkmn_name:
                # dlogger.info("{}'s {} successfully recognized."
                #              .format(side, pkmn_name))
                return i
        raise ValueError("Didn't recognize pokemon name: <{}> ({}) {}"
                         .format(pkmn_name, side, self.teams[side]))

    def switched(self, side, slot_active, pkmn_name):
        '''
        A new active Pokemon name was detected, which indicates a switch.
        The name of the active pokemon at `slot_active` was changed to `pkmn_name`.
        The new ingame ordering is equal to the old ingame ordering, with exactly
        one swap applied. Note: In a double KO, trainers select their new slot 0 and sends
        it out, then do the same for their new slot 1.  So it is still one swap at a time.
        '''
        slot_inactive = self.getSlotFromIngamename(side, pkmn_name)
        if slot_inactive == slot_active:
            dlogger.error("Detected switch, but active Pokemon are unchanged.")
            return
        if self.areFainted[side][slot_inactive]:
            raise ValueError("Fainted {} pokemon {} at new ingame slot_active {} swapped"
                             " into battle. slotSOMap: {}"
                             .format(side, pkmn_name, slot_active, self.slotSOMap))
        swap(self.teams[side], slot_inactive, slot_active)
        swap(self.teamsLive[side], slot_inactive, slot_active)
        swap(self.slotSOMap[side], slot_inactive, slot_active)
        swap(self.areFainted[side], slot_inactive, slot_active)
        # Otherwise both pkmn are fainted, and the fainted list is correct as-is
        self.on_switch(side=side, slot_active=slot_active, slot_inactive=slot_inactive)

    def draggedOut(self, side, pkmn_name):
        pass

    def checkWinner(self):
        '''
        TODO this will be an issue if we ever slow down below 1x speed. Why aren't we just spawning the match finished check when the quit menu comes up?
        Shall be called about 11 seconds after a fainted textbox appears.
        Must have this delay if the 2nd pokemon died as well and this was a
        KAPOW-death, therefore no draw.
        '''
        deadBlue = all(self.areFainted["blue"])
        deadRed = all(self.areFainted["red"])
        winner = "draw"
        if deadBlue and deadRed:  # Possible draw, but check for special cases.
            side, move = self._lastMove
            if move.lower() in ("explosion", "selfdestruct", "self-destruct"):
                winner = invertSide(side)
        elif deadBlue:
            winner = "red"
        else:
            winner = "blue"
        self.on_win(winner=winner)
