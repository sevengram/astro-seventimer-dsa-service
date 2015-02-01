#! /bin/bash
siege -c 100 -r 30 'http://42.96.137.0/service/wechat POST < constellation.data'
#siege -c 100 -r 30 'http://42.96.137.0/service/wechat POST < location.data'
