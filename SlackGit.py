#!/usr/local/pyenv/shims/python
# coding:utf-8

import os
from slackclient import SlackClient
import AppConf
import subprocess
import io,sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

                    # print(message)
                    # print(channel)

                    if message and channel:
                        self.executeCommand(message, channel)

    def slackOutputStr(self, message):
        messageList = message

        if messageList and len(messageList) > 0:
            for msg in messageList:
                if msg and 'text' in msg and SlackGit.botIdStr in msg['text']:
                    return msg['text'].split(SlackGit.botIdStr)[1].strip(), msg['channel']
        
        return None, None

    def executeCommand(self, message, channel):
        if message == "deploy stg":
            self.execDeploySh(channel, "ステージングサーバー", "execDeployStg.sh", True)
        elif message == "deploy product":
            self.execDeploySh(channel, "本番環境", "execDeployProduct.sh", False)
        elif message == "deploy operation":
            self.execDeploySh(channel, "ope環境", "execDeployOpe.sh", True)
        elif (message[0:10] == "git branch") and (len(message.split(' ')) == 5):
            self.execGitCommand(channel, message, True)
        elif (self.isGitPushCommand(message)):
            self.execGitCommand(channel, message, True)
        elif (message[:8] == "git pull") and (len(message.split(' ')) == 4):
            self.execGitCommand(channel, message, True)

    # check git push command
    def isGitPushCommand(self, message):
        # slack特殊文字置換
        message = self.replaceMessage(message)

        # Double quotation start:“ end:”
        messageWithoutComment = message[:message.find('\"')-1]

        # push ダブルクォーテーション commnet抜きコマンド配列==4
        if message[0:8] == "git push"\
           and message.count('\"') == 2\
           and len(messageWithoutComment.split(' ')) == 4:
            return True
        else:
            return False

    # slack特殊文字置換
    def replaceMessage(self, message):
        # Double quotation start:“ end:”
        message = message.replace('“', "\"")
        message = message.replace('”', "\"")

        return message

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
        # slack特殊文字置換
        message = self.replaceMessage(message)

        messageList = message.split(' ')

        # git branch repository ip feature/hogehoge
        if messageList[1] == "branch":
            repositoryStr = messageList[2]
            ipStr = messageList[3]
            branchNameStr = messageList[4]
            shCommand = "execGitBranch.sh " + repositoryStr + " " + ipStr + " " + branchNameStr
            commentStr = "にブランチ作成"

            self.execSh(channel, shCommand, ipStr, commentStr, logFlag )

        # git push repository ip commitComment
        elif messageList[1] == "push":
            repositoryStr = messageList[2]
            ipStr = messageList[3]

            commitComment = ""
            for str in messageList[4:]:
                commitComment += str + " "
            commitComment = commitComment.strip()

            shCommand = "execGitPush.sh " + repositoryStr + " " + ipStr + " " + commitComment
            commentStr = "のfeatureブランチをpush"

            self.execSh(channel, shCommand, ipStr, commentStr, logFlag)

        elif messageList[1] == "pull":
            repositoryStr = messageList[2]
            ipStr = messageList[3]
            shCommand = "execGitPull.sh " + repositoryStr + " " + ipStr
            commentStr = "のdevelopブランチを最新化"

            self.execSh(channel, shCommand, ipStr, commentStr, logFlag)

    def execSh(self, channel, shCommand, ipStr, commentStr, logFlag):
        SlackGit.sc.rtm_send_message(channel, ipStr + commentStr + "します。")
        try:
            result = subprocess.run(os.path.dirname(os.path.abspath(__file__))\
                                    + "/" + shCommand
                                    , stdout=subprocess.PIPE
                                    , stderr=subprocess.PIPE
                                    , shell=True
                                    , check=True)

            if logFlag:
                SlackGit.sc.rtm_send_message(channel, result.stdout.decode("utf8"))
                SlackGit.sc.rtm_send_message(channel, result.stderr.decode("utf8"))
            SlackGit.sc.rtm_send_message(channel, ipStr + commentStr + "しました。")
        except subprocess.CalledProcessError as err:
            print("ERROR:", err)
            SlackGit.sc.rtm_send_message(channel, ipStr + commentStr + "エラー。\n"\
                                                    "エラーを確認して下さい。\n"\
                                                    + err.stderr.decode("utf8"))


cmd = SlackGit()
