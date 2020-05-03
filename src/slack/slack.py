# -*- coding: utf-8 -*-
import slackweb
from . import slackinfo


def Send2SlackBot(sendtext):
    slack = slackweb.Slack(url=slackinfo.slack_webhook_url)
    slack.notify(text=sendtext, channel=slackinfo.slack_channel)


if __name__ == '__main__':
    #TESTCODE
    info = 'hoge'
    Send2SlackBot(info)
