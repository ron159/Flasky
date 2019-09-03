from flask_mail import Mail, Message
from threading import Thread

def send_async_mail(app, msg, mail):
	with app.app_context():
		mail.send(msg)

def send_mail(to, sub, link, app, mail):
	msg = Message('请查收你的注册邮件', sender=('Sims', 'jamesdd143@mail.com'), recipients=[to])
	msg.body = sub + link
	msg.html = '<h1>' + sub + '</h1><a href=' + link + '>' + link + '</a>'
	thr = Thread(target=send_async_mail, args=[app, msg, mail])
	thr.start()
	return thr