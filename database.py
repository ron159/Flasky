from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, ValidationError, RadioField
from wtforms.validators import Email, DataRequired, Length, EqualTo
from flask import session
db = SQLAlchemy()
#用户模型
class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	stu_id = db.Column(db.String(64), index=True)
	name = db.Column(db.String(64))
	major = db.Column(db.String(64))
	address = db.Column(db.String(64))
	#联系方式
	email = db.Column(db.String(64), index=True, unique=True)
	phone = db.Column(db.String(64), index=True, unique=True)
	#密码
	password = db.Column(db.String(64), default='123456')
	#身份
	role = db.Column(db.String(64), default='学生')
	#验证邮箱码
	active_code = db.Column(db.String(6))
	#激活状态
	active_state = db.Column(db.Boolean, default=False)
	#所管理的学生
	students = db.relationship('Student', backref='user', lazy='dynamic')
	#冻结状态
	frozen = db.Column(db.Boolean, default=False)

#学生模型
class Student(db.Model):
	__tablename__ = 'students'
	id = db.Column(db.Integer, primary_key=True)
	stu_id = db.Column(db.String(64), index=True)
	name = db.Column(db.String(64))
	#班级
	major = db.Column(db.String(64))
	#寝室
	address = db.Column(db.String(64))
	#联系方式
	email = db.Column(db.String(64))
	phone = db.Column(db.String(64))
	#教师id
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

#管理员表单模型
class AdminForm(FlaskForm):
	#邮箱验证
	def account_check(self, field):
		if field.data != 'admin@admin.com':
			raise ValidationError('账号或者密码错误')
	#密码验证
	def password_check(self, field):
		if field.data != 'admin':
			raise ValidationError('账号或者密码错误')

	email = StringField("管理员邮箱", validators=[DataRequired(message='邮箱不能为空'), 
		Email(message=u'非法邮箱地址'), account_check])
	password = PasswordField("管理员密码", validators=[DataRequired(message='密码不能为空'), password_check])
	login = SubmitField("登录")

#管理员增加用户表单模型
class AdminAddForm(FlaskForm):
	#检测邮箱唯一性
	def email_unique(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('邮箱存在')
	def phone_unique(self, field):
		if User.query.filter_by(phone=field.data).first():
			raise 	ValidationError('手机号已存在')

	stu_id = StringField('学号或工号', validators=[DataRequired()])
	name = StringField('姓名', validators=[DataRequired()])
	major = StringField('专业班级', validators=[DataRequired()])
	address = StringField('寝室', validators=[DataRequired()])
	email = StringField('邮箱', validators=[DataRequired(), email_unique])
	phone = StringField('用户手机', default='', validators=[Length(11,11,message='长度不符合'), phone_unique])
	password = StringField('用户密码', validators=[DataRequired()], default='123456')
	role = RadioField('身份', choices=[('学生', '学生'), ('教师', '教师')], default='学生')
	add = SubmitField("增加用户")
			
#用户登录表单模型
class LoginForm(FlaskForm):
	#验证用户是否存在
	def email_exist(self, field):
		if not User.query.filter_by(email=field.data).first():
			raise ValidationError('账号不存在')
	
	email = StringField("邮箱", validators=[DataRequired(message='邮箱为空'), 
		Email(message=u'非法邮箱地址'), email_exist])
	password = PasswordField("密码", validators=[DataRequired(message='密码为空')])
	login = SubmitField("登录")

#用户注册表单模型
class SignupForm(FlaskForm):
	def email_unique(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('邮箱已存在')
	def phone_unique(self, field):
		if User.query.filter_by(phone=field.data).first():
			raise 	ValidationError('手机号已存在')
	#检测密码中是否有空格
	def password_noblank(self, field):
		for s in field.data:
			if s == ' ':
				raise ValidationError('密码中不可包含空格')

	name = StringField('姓名', validators=[DataRequired(message='必填')])
	stu_id = StringField('学号或工号', validators=[DataRequired(message='必填')])
	major = StringField('专业班级', validators=[DataRequired(message='必填')])
	email = StringField("邮箱", validators=[DataRequired(message='必填'), 
		Email(message='非法邮箱地址'), email_unique])
	phone = StringField("手机号", validators=[DataRequired(message='必填'), 
		Length(11, 11, message='长度不符合'), phone_unique])
	address = StringField("寝室或住址", validators=[DataRequired(message='必填')])
	password = PasswordField("密码", validators=[DataRequired(message='必填'),
		Length(6, message='密码过短'), password_noblank])		
	confirm = PasswordField("确认密码", validators=[DataRequired(message='已确认'),
		EqualTo('password', "两次密码不一样!")])
	role = RadioField('身份', choices=[('学生', '学生'), ('教师', '教师')], default='学生')
	signup = SubmitField("注册")

#找回密码表单模型
class ForgetForm(FlaskForm):
	def email_exist(self, field):
		if not User.query.filter_by(email=field.data).first():
			raise ValidationError('没有这个邮箱')
	def password_noblank(self, field):
		for s in field.data:
			if s == ' ':
				raise ValidationError('密码中不可包含空格')

	email = StringField("注册时邮箱：", validators=[DataRequired(message='邮箱不能为空'), 
		Email(message='非法邮箱地址'), email_exist])
	password = PasswordField("请填写新密码：", validators=[DataRequired(message='密码不能为空'),
		Length(6, message='密码过短'), password_noblank])		
	confirm = PasswordField("确认密码：", validators=[DataRequired(message='密码不能为空'),
		EqualTo('password', "两次密码不一致")])
	getback = SubmitField("确认")	

class AddForm(FlaskForm):
	#检测学号是否存在
	def student_exist(self, field):
		user = User.query.filter_by(id=session.get('user_id')).first()
		for student in user.students:
			if student.stu_id == field.data:
				raise ValidationError("该学号学生已存在")

	stu_id = StringField("学生学号", validators=[DataRequired(message="不可为空"), Length(6, 15, "长度不符合"), student_exist])
	name = StringField("学生姓名", validators=[DataRequired(message="不可为空"), Length(-1, 10, "长度不符合")])
	major = StringField("专业班级", validators=[DataRequired(message="不可为空"), Length(-1, 15, "长度不符合")])
	address = StringField("所在寝室", validators=[DataRequired(message="不可为空"), Length(-1, 15, "长度不符合")])
	phone = StringField("联系电话", validators=[DataRequired(message="不可为空")])
	email = StringField("邮箱", validators=[DataRequired(message="不可为空")])
	add = SubmitField("添加")
	
#教师搜索学生表单模型
class SearchForm(FlaskForm):
	keyword = StringField("输入查询关键字", validators=[DataRequired(message="输入不能为空")])
	search = SubmitField("查找")
