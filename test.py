#coding=utf-8
# python 2.7
import smtplib,time,MySQLdb
from email.mime.text import MIMEText
from email.header import Header

def sendEmail(content):
    mail_host = "smtp.sina.com"
    mail_user = "controlservice@sina.com"
    mail_pass = "a123456"
    sender = 'controlservice@sina.com'
    receivers = ['suishanwen@icloud.com']
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header("controlservice@sina.com")
    message['To'] = Header("my-email")
    message['Subject'] = Header('ControlService')
    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host, 25)
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print(u"邮件发送成功")
    except smtplib.SMTPException as err:
        print(err)
        print(u"Error: 邮件发送失败")

global projectBak1,projectBak2
projectBak1=""
projectBak2=""
while True:
	global projectBak1,projectBak2
	conn = MySQLdb.connect(host='localhost',user='root',passwd='',db='sw',charset='utf8')
	cursor = conn.cursor()  
	cursor.execute("select taskName from Controller where identify='A'")
	results = cursor.fetchall()  
	result=list(results)    
	project1=result[0][0].encode('utf8')
	project2=result[1][0].encode('utf8')
	if projectBak1!=project1 or projectBak2!=project2:
		sendEmail(project1+"-"+project2)
	projectBak1=project1
	projectBak2=project2
	time.sleep(150)