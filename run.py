import os
import paramiko
import requests
import json
from datetime import datetime, timezone, timedelta

def ssh_multiple_connections(hosts_info, command):
    results = []
    for host_info in hosts_info:
        hostname = host_info['hostname']
        username = host_info['username']
        password = host_info['password']
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=hostname, port=22, username=username, password=password)
            stdin, stdout, stderr = ssh.exec_command(command)
            user = stdout.read().decode().strip()
            results.append({
                'status': 'success',
                'username': user,
                'hostname': hostname
            })
            ssh.close()
        except Exception as e:
            results.append({
                'status': 'fail',
                'username': username,
                'hostname': hostname,
                'error': str(e)
            })
    return results

ssh_info_str = os.getenv('SSH_INFO', '[]')
hosts_info = json.loads(ssh_info_str)

command = 'whoami'
connection_results = ssh_multiple_connections(hosts_info, command)

content = ""
for result in connection_results:
    if result['status'] == 'success':
        content += "✅ SSH登录成功\n"
        content += f"用户名：{result['username']}\n服务器：{result['hostname']}\n"
    else:
        content += "❌ SSH登录失败\n"
        content += f"用户名：{result['username']}\n服务器：{result['hostname']}，错误：{result['error']}\n"

beijing_timezone = timezone(timedelta(hours=8))
time = datetime.now(beijing_timezone).strftime('%Y-%m-%d %H:%M:%S')

try:
    loginip = requests.get('https://api.ipify.org?format=json', timeout=5).json()['ip']
except:
    loginip = "未知"

content += f"登录时间：{time}\n登录IP：{loginip}"

push = os.getenv('PUSH')

def mail_push(url):
    data = {
        "body": content,
        "email": os.getenv('MAIL')
    }

    try:
        response = requests.post(url, json=data)
        response_data = response.json()
        if response_data.get('code') == 200:
            print("推送成功")
        else:
            print(f"推送失败，错误代码：{response_data.get('code')}")
    except Exception as e:
        print("连接邮箱服务器失败：", e)

def telegram_push(message):
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    payload = {
        'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
        'text': message,
        'parse_mode': 'HTML'
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"发送消息到Telegram失败: {response.text}")

if push == "mail":
    mail_push('https://zzzwb.pp.ua/test')
elif push == "telegram":
    telegram_push(content)
else:
    print("推送失败，推送参数设置错误")
