#!/usr/bin/env python
# -*- coding: utf-8 -*-


import ripsnort


def test_formatName():
    expectedText1 = 'Bones - Season 7 Disc 1'

    assert expectedText1 == ripsnort.formatDiscName('BONES_SEASON_7_DISC_1')
    assert expectedText1 == ripsnort.formatDiscName('bones_s7_d1')
    assert expectedText1 == ripsnort.formatDiscName('bones_season7_d1')
    assert expectedText1 == ripsnort.formatDiscName('bones_season_7_d1')
    assert expectedText1 == ripsnort.formatDiscName('bones_season_7_d_1')
    
    expectedText2 = 'Die Hard'
 
    assert expectedText2 == ripsnort.formatDiscName('Die Hard Limited Edition')
    assert expectedText2 == ripsnort.formatDiscName('Die Hard limited_Edition')
    assert expectedText2 == ripsnort.formatDiscName('Die Hard Special Edition')
    assert expectedText2 == ripsnort.formatDiscName('Die Hard special_edition')
    assert expectedText2 == ripsnort.formatDiscName('Die Hard Extended Edition')
    assert expectedText2 == ripsnort.formatDiscName('DIE_HARD_EXTENDED_EDITION')
    expectedText3 = 'Bones - Season 8 Disc 1'

    assert expectedText3 == ripsnort.formatDiscName('BONES_SEASON_8_F1_DISC_1')
    assert expectedText3 == ripsnort.formatDiscName('BONES_SEASON_8_F1_D_1')
    assert expectedText3 == ripsnort.formatDiscName('BONES_SEASON_8_F1_D1')

    expectedText4 = '24 - Season 2 Disc 2'

    assert expectedText4 == ripsnort.formatDiscName('24_SEASON2_DISC2')
    assert expectedText4 == ripsnort.formatDiscName('24_SEASON2_DISC_2')
    assert expectedText4 == ripsnort.formatDiscName('24SEASON2DISC2')
    assert expectedText4 == ripsnort.formatDiscName('24_SEASON_2_DISC_2')
    assert expectedText4 == ripsnort.formatDiscName('24_SEASON_2_DISK_2')

    expectedText5 = 'Die Hard 2'
 
    assert expectedText5 == ripsnort.formatDiscName('Die Hard 2')
    assert expectedText5 == ripsnort.formatDiscName('Die Hard  2')
    assert expectedText5 == ripsnort.formatDiscName('Die Hard2')

    expectedText6 = 'Little Mermaid 2'
 
    assert expectedText6 == ripsnort.formatDiscName('LITTLE_MERMAID2')
    
    return True


if __name__ == "__main__":
    assert test_formatName() == True


