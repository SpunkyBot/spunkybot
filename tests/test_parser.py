#!/usr/bin/env python
# -*- coding: utf-8 -*-

line = "  0:00 InitGame: \g_matchmode\1\g_gametype\7\g_allowvote\536871039\g_gear\KQ\mapname\ut4_dust2_v2\gamename\q3urt43\g_survivor\0\auth\0\g_modversion\4.3.4"


def test_initgame():
    tmp = line.split()
    assert tmp[1] == "InitGame:"


def test_mod43():
    ret_val = 40
    if "g_modversion\4.3" in line:
        ret_val = 43
    assert ret_val == 43


def test_mod42():
    ret_val = 40
    if "g_modversion\4.2" in line:
        ret_val = 42
    assert ret_val == 40


def test_ffa_gametype():
    ret_val = None
    if "g_gametype\0" in line:
        ret_val = "FFA"
    assert ret_val != "FFA"


def test_ctf_gametype():
    ret_val = "FFA"
    if "g_gametype\7" in line:
        ret_val = "CTF"
    assert ret_val == "CTF"


def test_gear_value():
    gear = line.split('g_gear\\')[-1].split('\\')[0] if 'g_gear\\' in line else "%s" % ''
    assert gear == "KQ"
