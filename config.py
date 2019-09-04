import os 

#表单秘钥
CSRF_ENABLED = True
SECRET_KEY = 'this-is-a-test-secret-key'


#邮箱配置信息
MAIL_SERVER = 'smtp.mail.com'	#邮件服务器
MAIL_PORT = 587	#端口
MAIL_USE_SSL = False
MAIL_USE_TLS = True	
MAIL_DEBUG = True	
MAIL_USERNAME = '  '	#邮箱账号
MAIL_PASSWORD = r'  '	#邮箱密码

#数据库配置
basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')	#数据库URI		
SQLALCHEMY_COMMIT_ON_TEARDOWN = True	#更改自动提交
SQLALCHEMY_TRACK_MODIFICATIONS = True
