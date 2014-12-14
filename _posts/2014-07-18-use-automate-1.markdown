---
layout: default
category: use
subcategory: Automate
description: open scheduler <em>sudo crontab -e</em> and add the following line changing <em>/PATH_TO_NEWVIDEOS/</em> to location of uncataloged files
title: Catalog scheduler
code: [STRSTAR STRSTAR STRSTAR find /PATH_TO_NEWVIDEOS/ -name '*.mkv' -o -name '*.iso' -exec ./ripsnort.py -v -r CURLYOPENCURLYCLOSE \;]
---
