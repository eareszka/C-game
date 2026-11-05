"""Xuelin's lantern posts' other frames (town_design.py anim_design): the
cells of each post at frames 1 and 2, a column a cell, laid on the sheet
beside the town (overworld_style.XUELIN_AT['town_anim']) and swapped in on
the world's ambient beat (src/tilemap.cpp art_cells_at, XUELIN_ANIM).
Exported by town_design.py; this gives gen_entrance_art.py its layers."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import town_design


def design():
    return town_design.anim_design()
