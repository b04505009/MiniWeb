#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018  <@DESKTOP-TA60DPH>
#
# Distributed under terms of the MIT license.

"""
Here is the access point into web service
"""
from flask import Flast,request

server = Flask(__name__)

@server.route('/')
def index():
    return "Hello World"


if __name__ == '__main__':
    server.run(debug=True)
