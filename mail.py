from flask_mail import Mail, Message
from threading import Thread

#异步发送邮件
def send_async_mail(app, msg, mail):
	with app.app_context():
		mail.send(msg)

def send_mail(to, sub, link, app, mail):
	msg = Message('Flaskr邮件来啦', sender=('Flaskr', 'jamesdd143@mail.com'), recipients=[to])
	msg.body = sub + link
	msg.html = '<h1>' + sub + '</h1><a href=' + link + '>' + link + '</a>'
	thr = Thread(target=send_async_mail, args=[app, msg, mail])
	thr.start()
	return thr