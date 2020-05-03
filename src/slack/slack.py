# -*- coding: utf-8 -*-
import slackweb
import slackinfo


def main():
    slack = slackweb.Slack(url=slackinfo.slack_webhook_url)
    slack.notify(text='dockerコンテナで実行してみるよ', channel=slackinfo.slack_channel)


if __name__ == '__main__':
    main()
