import sys
import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup
import datetime
import json

import prefTable
import areaTable
import cityTable
import epicenterTable

from slack import slack

IntList = ['7', '6+', '6-', '5+', '5-', '4', '3', '2', '1']

IntDict = {
    '7': '震度7',
    '6+': '震度6強',
    '6-': '震度6弱',
    '5+': '震度5強',
    '5-': '震度5弱',
    '4': '震度4',
    '3': '震度3',
    '2': '震度2',
    '1': '震度1'
}


def getxml(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        XmlData = response.read()

    #with open(XmlData) as doc:
    soup = BeautifulSoup(XmlData, "xml")  # 第2引数でパーサを指定
    return soup


def detailInformation(xml, table):
    #print(xml.prettify())
    jsontext = {}
    sendtext = ''
    print(xml.Text.text)
    print("時刻 " + xml.OriginTime.text)
    dt = datetime.datetime.fromisoformat(xml.OriginTime.text)
    jsontext['date'] = dt.strftime("%Y/%m/%d %H:%M:%S")
    print(dt.strftime("%Y/%m/%d %p %I:%M"))
    sendtext += dt.strftime("%Y/%m/%d %p %I:%M") + "ごろ地震がありました。\n"
    print("震源 " + epicenterTable.epicenterTable[xml.Hypocenter.Area.Code.text])
    sendtext += '震源: ' + epicenterTable.epicenterTable[
        xml.Hypocenter.Area.Code.text] + '\n'
    coordinate = xml.find("jmx_eb:Coordinate").text.strip('/')
    coordinate = re.split(r'[+-]', coordinate)
    print("北緯: " + coordinate[1] + " 東経: " + coordinate[2] + " 震源の深さ: " +
          str(int(coordinate[3]) / 1000) + "km")
    sendtext += '震源の深さ: ' + str(int(coordinate[3]) / 1000) + 'km\n'
    jsontext['latitude'] = float(coordinate[1])
    jsontext['longitude'] = float(coordinate[2])
    jsontext['depth'] = float(coordinate[3]) / 1000
    print("マグニチュード " + xml.find("jmx_eb:Magnitude").text)
    sendtext += 'マグニチュード: ' + xml.find("jmx_eb:Magnitude").text + '\n'
    jsontext['Magnitude'] = float(xml.find("jmx_eb:Magnitude").text)
    print("最大震度 " + xml.Intensity.Observation.MaxInt.text)
    jsontext['MaxInt'] = xml.Intensity.Observation.MaxInt.text
    sendtext += '最大震度: ' + xml.Intensity.Observation.MaxInt.text + '\n'
    prefint = {}
    areaint = {}
    cityint = {}
    for comments in xml.Comments.find_all("ForecastComment"):
        print(comments.Text.text + " " + comments.Code.text)

    for intensity in xml.Intensity.find_all("Pref"):
        #        print(intensity.Name.text + " " + intensity.Code.text + " " +
        #              intensity.MaxInt.text)
        prefint[intensity.Code.text] = intensity.MaxInt.text
        for area in intensity.find_all("Area"):
            #            print(" " + area.Name.text + " " + area.Code.text + " " +
            #                  area.MaxInt.text)
            areaint[area.Code.text] = area.MaxInt.text
            for city in area.find_all("City"):
                #                print("  " + city.Name.text + " " + city.Code.text + " " +
                #                      city.Int.text)
                cityint[city.Code.text] = city.Int.text

    jsontext['city'] = cityint

    for Int in IntList:
        if Int in areaint.values():
            print(IntDict[Int])
            key = [k for k, v in areaint.items() if v == Int]
            for area in key:
                print(" " + areaTable.areaTable[area],
                      areaTable.areaFuriganaTable[area])
    print('')

    #震度ごと都道府県ごとに画面表示する
    for Int in IntList:
        if Int not in cityint.values():
            continue

        print(IntDict[Int])
        sendtext += IntDict[Int] + '\n'
        #震度ごとに市町村を検索する
        key = [k for k, v in cityint.items() if v == Int]
        #市町村名に紐づくidを検索する
        city_ids = [[j['id'] for j in table if i == j['CityId']] for i in key]
        #idが複数取得できるため1つのみ残す
        city_id = [x[0] for x in city_ids]
        #市町村が属する都道府県を検索する
        city_prefCodes = [[j['PrefId'] for j in table if i == j['CityId']]
                          for i in key]
        city_prefCode = [x[0] for x in city_prefCodes]
        #市町村コードと都道府県コードを紐づける
        cityPref = {city: pref for city, pref in zip(city_id, city_prefCode)}

        #県名に紐づくidを検索する
        pref_ids = [[j['PrefId'] for j in table if i == j['CityId']]
                    for i in key]
        pref_id = set([x[0] for x in pref_ids])

        #都道府県ごとに表示する
        for pid in pref_id:
            pref = [j['PrefName'] for j in table if pid == j['PrefId']][0]
            print(' ' + pref)
            sendtext += ' ' + pref + '\n'
            city = [k for k, v in cityPref.items() if v == pid]
            city = [[
                '  {}({})'.format(j['CityName'], j['CityFurigana'])
                for j in table if i == j['id']
            ] for i in city]
            city = set([x[0] for x in city])
            for city in city:
                print(city)
                sendtext += city + '\n'

    print(jsontext)
    print(sendtext)
    slack.Send2SlackBot(sendtext)
    return


def majorInformation(xml):
    print(xml.Text.text)
    print("時刻 " + xml.TargetDateTime.text)
    dt = datetime.datetime.fromisoformat(xml.TargetDateTime.text)
    print(dt.strftime("%Y/%m/%d %p %I:%M"))

    for comments in xml.Comments.find_all("ForecastComment"):
        print(comments.Text.text + " " + comments.Code.text)

    for intensity in xml.Headline.Information.find_all("Item"):
        print(intensity.Kind.Name.text)
        for area in intensity.find_all("Area"):
            print(" " + area.Name.text + " " + area.Code.text)
    return


if sys.argv[1] == 'short':
    url = 'http://www.data.jma.go.jp/developer/xml/feed/eqvol.xml'
elif sys.argv[1] == 'long':
    url = 'http://www.data.jma.go.jp/developer/xml/feed/eqvol_l.xml'
else:
    url = 'http://www.data.jma.go.jp/developer/xml/feed/eqvol_l.xml'

#with open(XmlData) as doc:
soup = getxml(url)
#soup = BeautifulSoup(XmlData, "xml")  # 第2引数でパーサを指定

#print(soup.prettify())

with open('table.json', 'r') as table:
    json_table = json.load(table)

for entry in soup.find_all("entry"):
    if entry.title.string == "震源・震度に関する情報":
        print("----------------")
        print(entry.id.text.strip("urn:uuid:"))
        print(entry.updated.text)
        print(entry.title.string)
        #print(entry.content.text)
        detailInfo = getxml(entry.link.get("href"))
        detailInformation(detailInfo, json_table["table"])
        print("----------------")
    if entry.title.string == "震度速報":
        print("----------------")
        print(entry.id.text.strip("urn:uuid:"))
        print(entry.updated.text)
        print(entry.title.string)
        #print(entry.content.text)
        detailInfo = getxml(entry.link.get("href"))
        #        majorInformation(detailInfo)
        print("----------------")
