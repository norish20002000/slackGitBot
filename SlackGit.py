#!/usr/local/pyenv/shims/python
# coding:utf-8

import os
from slackclient import SlackClient
import AppConf
import subprocess

class SlackGit:
    botIdStr = '<@' + AppConf.BOT_ID + '>'
    sc = SlackClient(AppConf.token)
    
    def __init__(self):
        if SlackGit.sc.rtm_connect():
            # print(SlackGit.sc.user)
            # print(SlackGit.sc.server.login_data['self']['id'])
            while True:
                data = SlackGit.sc.rtm_read()

                if(len(data) > 0) :
                    # print(data)
                    message, channel = self.slackOutputStr(data)

                    print(message)
                    print(channel)

                    if message and channel:
                        self.executeCommand(message, channel)

    def slackOutputStr(self, message):
        messageList = message

        if messageList and len(messageList) > 0:
            for msg in messageList:
                if msg and 'text' in msg and SlackGit.botIdStr in msg['text']:
                    return msg['text'].split(SlackGit.botIdStr)[1].strip().lower(), msg['channel']
        
        return None, None

    def executeCommand(self, message, channel):
        print(message[0:12])
        if message == "deploy stg":
            self.execDeploySh(channel, "ステージングサーバー", "execDeployStg.sh", True)
        elif message == "deploy product":
            self.execDeploySh(channel, "本番環境", "execDeployProduct.sh", False)
        elif message == "deploy operation":
            self.execDeploySh(channel, "ope環境", "execDeployOpe.sh", True)
        elif (message[0:10] == "git branch") and (len(message.split(' ')) == 5):
            print(message)
            self.execGitCommand(channel, message, True)
        elif (message[0:7] == "git push") and (len(message.split(' ') == 5)):
            self.execGitCommand(channel, message, True)

    def execDeploySh(self, channel, serverName, shFile, logFlag):
        SlackGit.sc.rtm_send_message(channel, serverName + "にdeploy、始めます。")
        try:
            SlackGit.sc.rtm_send_message(channel, "waiting....................")
            result = subprocess.run(os.path.dirname(os.path.abspath(__file__)) + "/" + shFile
                                    , stdout=subprocess.PIPE
                                    , stderr=subprocess.PIPE
                                    , shell=True
                                    , check=True)
            if logFlag:
                SlackGit.sc.rtm_send_message(channel, result.stdout.decode('euc_jp'))
                SlackGit.sc.rtm_send_message(channel, result.stderr.decode('euc_jp'))
            SlackGit.sc.rtm_send_message(channel, serverName + "にdeploy、終了しました。")
    
            return result
        except subprocess.CalledProcessError as err:
            print("ERROR:", err)
            SlackGit.sc.rtm_send_message(channel, serverName + "にdeploy、失敗しました。\n"\
                                                    "エラーを確認して下さい。\n" \
                                                    + err.stderr.decode('euc_jp'))

    def execGitCommand(self, channel, message, logFlag):
        messageList = message.split(' ')

        # git branch repository ip feature/hogehoge
        if messageList[1] == "branch":
            repositoryStr = messageList[2]
            ipStr = messageList[3]
            branchNameStr = messageList[4]

            SlackGit.sc.rtm_send_message(channel, repositoryStr + "にbranch作成します。")
            try:
                result = subprocess.run(os.path.dirname(os.path.abspath(__file__))\
                                        + "/" + "execGitBranch.sh " + ipStr + " " + branchNameStr
                                        , stdout=subprocess.PIPE
                                        , stderr=subprocess.PIPE
                                        , shell=True
                                        , check=True)

                if logFlag:
                    SlackGit.sc.rtm_send_message(channel, result.stdout.decode('euc_jp'))
                    SlackGit.sc.rtm_send_message(channel, result.stderr.decode('euc_jp'))
                SlackGit.sc.rtm_send_message(channel, repositoryStr + "にブランチ作成しました。")
            except subprocess.CalledProcessError as err:
                print("ERROR:", err)
                SlackGit.sc.rtm_send_message(channel, repositoryStr + "にbranch作成エラー。\n"\
                                                        "エラーを確認して下さい。\n"\
                                                        + err.stderr.decode('euc_jp'))


cmd = SlackGit()
