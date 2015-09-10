'''
Created on 09.09.2015

@author: Felk
'''

from util import enum

##########################################
# buttons. concatenate to 16 bit integer with binary or

WiimoteButton = enum(
    LEFT  = 0x0001,
    RIGHT = 0x0002,
    DOWN  = 0x0004,
    UP    = 0x0008,
    PLUS  = 0x0010,

    TWO   = 0x0100,
    ONE   = 0x0200,
    B     = 0x0400,
    A     = 0x0800,
    MINUS = 0x1000,
    HOME  = 0x8000,
)

##########################################
# uncategorized stuff

# none :)

##########################################
# cursor positions to click on stuff

CursorOffsets = enum(
    BOX      = 0x0b,
    PKMN     = 0x0a,
    BP_SLOTS = 0x15,
    STAGE    = 0x01,
)

CursorPosMenu = enum(
    BP       = 0x01,
    BATTLE   = 0x02,
    PROFILE  = 0x03, #unused
    SAVE     = 0x04, #unused
    STORAGE  = 0x05, #unused
    WFC      = 0x06, #unused
    SHOP     = 0x07, #unused
    BUTTON_1 = 0x01, # for generic guis
    BUTTON_2 = 0x02, # for generic guis
    BUTTON_3 = 0x03, # for generic guis
    BACK     = 0x63, # for whatever reason
    STAGE_DOWN = 0x08,
)

CursorPosBP = enum(
    BP_1   = 0x14,
    BP_2   = 0x15,
    REMOVE = 0x09,
    CUSTOM = 0x0d,
    RENTAL = 0x0e,
    FRIEND = 0x0f,
)

##########################################
# all necessary gui states.
# hook events to there states!

GuiStateBP = enum(
    CONFIRM        = 0x00,
    BP_SELECTION   = 0x0C,
    SLOT_SELECTION = 0x06,
    BOX_SELECTION  = 0x1C,
    PKMN_SELECTION = 0x27,
    PKMN_GRABBED   = 0x09,
)

GuiStateMenu = enum(
    #NONE            = 0x00,
    MAIN_MENU       = 0x2d,
    BATTLE_PASS     = 0x39,
    BATTLE_TYPE     = 0x40,
    BATTLE_PLAYERS  = 0x85,
    BATTLE_REMOTES  = 0x8a,
    BATTLE_RULES    = 0x90, # unfortunately stage selection AND rules
                            # use GuiStateRules for better distinction
)

GuiStateRules = enum(
    STAGE_SELECTION = 0x20,
    OVERVIEW        = 0x26,
    BATTLE_STYLE    = 0x2b, # single or double battle
    BP_SELECTION    = 0xb8, # use GuiStateBpSelection for better distinction
    BP_CONFIRM      = 0x3a,
    MATCH           = 0x3d, # also pre-match? useless
)

GuiStateBpSelection = enum(
    BP_SELECTION_CUSTOM = 0x15, # use this
    BP_SELECTION_RENTAL = 0x14, # unused
    BP_CONFIRM          = 0x17,
)

GuiStateOrderSelection = enum(
    #NONE    = 0x14,
    SELECT  = 0x03,
    CONFIRM = 0x0e,
)

GuiStateMatch = enum(
    IDLE    = 0x8,
    MOVES   = 0x3,
    GIVE_IN = 0xb,
    PKMN    = 0x5,     
)

StatePopupBox = enum(
    AWAIT_INPUT = 0x67, # wtf
    # IDLE      = 0x01, and 0x02?
)

##########################################
# can stay unused by using inputs instead.
GuiTarget = enum(
    GIVE_IN       = 0xff,
    SELECT_MOVE   = 0xfc,
    SWITCH_PKMN   = 0xfd,
    INSTA_GIVE_IN = 0xfe,
)
MoveInput = enum(
    NONE  = 0xff,
    UP    = 0,
    RIGHT = 1, 
    LEFT  = 2,
    DOWN  = 3,
)
