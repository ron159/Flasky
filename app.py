# encoding='utf-8'

import random
from flask import Flask, render_template, redirect, url_for, flash, abort, session, request, jsonify, send_from_directory
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from mail import send_mail
from database import db, Student, User, AddForm, AdminForm, AdminAddForm, LoginForm, SignupForm, ForgetForm, SearchForm

# 创建应用实例
app = Flask(__name__)

# 应用配置读取
app.config.from_object('config')

# 首先在此处实例化所有模块
# 需要注意的是，配置文件的读取必须在实例化以前，否则无法正确读取配置
bootstrap = Bootstrap(app)
#db = SQLAlchemy(app)
db.init_app(app)
db.app = app
mail = Mail(app)
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

# 初始化数据库
db.create_all()

# 登录路由控制
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # 验证是否被冻结
        if user.frozen:
            flash("你的账户已被冻结")
            return redirect(url_for('login'))
        # 验证是否激活邮箱
        if user.active_state == False:
            flash("请查收邮件以完成注册")
            return redirect(url_for('login'))
        # 验证密码是否正确
        elif user.password != form.password.data:
            flash("密码不正确")
            return redirect(url_for('login'))
        # 记住登录状态
        session['user_id'] = user.id
        # 根据身份重定向
        if user.role == '教师':
            return redirect('/u/' + str(user.id))
        if user.role == '学生':
            return redirect('/s/' + str(user.id))
    return render_template('form.html', form=form)

# 退出路由控制
@app.route('/logout')
def logout():
    # 管理员退出
    if session.get('admin'):
        session['admin'] = None
    # 普通用户退出
    elif session.get('user_id') is None:
        flash("未登录")
        return redirect(url_for('login'))
    flash("退出成功")
    session['user_id'] = None
    return redirect(url_for('login'))

# 注册路由控制
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        # 生成随机码
        n = []
        for i in range(10):
            n.append(str(random.randint(0, 9)))
        active_code = ''.join(n)
        new_user = User(name=form.name.data, stu_id=form.stu_id_data, major=form.major.data, email=form.email.data, phone=form.phone.data,
							address=form.address.data, password=form.password.data, role=form.role.data, active_code=active_code)
        db.session.add(new_user)

        # 发送验证邮件
        user = User.query.filter_by(email=form.email.data).first()
        sub = "请点击链接继续完成注册："
        link = '127.0.0.1/signup/' + str(user.id) + '/' + active_code
        send_mail(new_user.email, sub, link, app, mail)

        flash("请查收邮件以继续完成注册")
        return redirect(url_for('login'))
    return render_template('form.html', form=form)

# 验证邮箱路由控制
@app.route('/signup/<int:id>/<active_code>')
def check(id, active_code):
    user = User.query.filter_by(id=id).first()
    # 验证随机码是否匹配
    if user is not None and user.active_code == active_code:
        user.active_state = True
        db.session.add(user)
        return render_template('success.html', action="注册")
    abort(400)

# 找回密码路由控制
@app.route('/forget', methods=['GET', 'POST'])
def forget():
    form = ForgetForm()
    if form.validate_on_submit():
        # 发送找回密码邮件
        user = User.query.filter_by(email=form.email.data).first()
        sub = "请点击链接继续完成密码更改："
        link = '127.0.0.1/f/' + \
            str(user.id) + '/' + user.active_code + '/' + form.password.data
        flash("请查收邮件以完成密码更改")
        send_mail(user.email, sub, link, app, mail)
        return redirect(url_for('login'))
    return render_template("form.html", form=form)

# 找回密码邮箱验证路由控制
@app.route('/f/<int:id>/<active_code>/<password>')
def new_password(id, active_code, password):
    user = User.query.filter_by(id=id).first()
    if user is not None and user.active_code == active_code:
        # 更改密码并存入数据库
        user.password = password
        db.session.add(user)
        return render_template('success.html', action="密码已成功更改")
    abort(400)

# 教师主页路由控制
@app.route('/u/<int:id>')
def user(id):
    # 验证是否已登录
    if session.get('user_id') is None or id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    user = User.query.filter_by(id=id).first()
    # 验证身份
    if user.role != '教师':
        abort(400)
    return render_template('user.html', user=user)

# 学生主页路由控制
@app.route('/s/<int:id>')
def student(id):
    if session.get('user_id') is None or id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    user = User.query.filter_by(id=id).first()
    teachers = User.query.filter_by(role='教师').all()
    if user.role != '学生':
        abort(400)
    return render_template('student.html', user=user, teachers=teachers)

# 学生加入路由设置
@app.route('/s/<int:user_id>/<int:teacher_id>/join')
def join(user_id, teacher_id):
    user = User.query.filter_by(id=user_id).first()
    teacher = User.query.filter_by(id=teacher_id).first()
    teachers = User.query.filter_by(role='教师').all()
    new_student = Student(stu_id=user.id, name=user.name, major=user.major, address=user.address,
                          email=user.email, phone=user.phone, user_id=teacher_id)
    if Student.query.filter_by(stu_id=user.id, user_id=teacher_id).all():
        flash('加入失败，你已经是该老师的学生')
    else:
        db.session.add(new_student)
        flash('加入成功')
    return render_template('student.html', user=user, teachers=teachers)


# 账户信息路由控制
@app.route('/u/<int:id>/account')
def account(id):
    if session.get('user_id') is None or id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    user = User.query.filter_by(id=id).first()
    num = user.students.count()
    return render_template('account.html', user=user, num=num)

# 学生选择教师路由控制
@app.route('/s/<int:user_id>/<int:teacher_id>')
def detail(user_id, teacher_id):
    if session.get('user_id') is None or user_id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    user = User.query.filter_by(id=user_id).first()
    if user.role != '学生':
        abort(400)
    teacher = User.query.filter_by(id=teacher_id).first()
    # 为了更改id和role重新构建用户传递给跳转页面
    x_user = {}
    x_user['id'] = user_id
    x_user['role'] = '学生'
    x_user['name'] = teacher.name
    x_user['students'] = teacher.students
    return render_template('detail.html', user=x_user)

# 教师新增学生路由控制
@app.route('/u/<int:id>/add', methods=['GET', 'POST'])
def add(id):
    if session.get('user_id') is None or id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    user = User.query.filter_by(id=id).first()
    if user.role != '教师':
        abort(400)
    form = AddForm()
    if form.validate_on_submit():
        # 构建新学生并保存
        new_student = Student(stu_id=form.stu_id.data, name=form.name.data,
                              major=form.major.data, address=form.address.data, phone=form.phone.data, email=form.email.data, user_id=id)
        db.session.add(new_student)
        flash("添加成功")
        return redirect('/u/' + str(id) + '/add')
    return render_template('form.html', form=form, user=user)

# 教师搜索学生路由控制
@app.route('/u/<int:id>/search', methods=['GET', 'POST'])
def search(id):
    if session.get('user_id') is None or id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    form = SearchForm()
    user = User.query.filter_by(id=id).first()
    if user.role != '教师':
        abort(400)

    hide = set()  # 不需显示的学生集合
    if form.validate_on_submit():
        for student in user.students:
            word = str(student.stu_id) + ' ' + student.name + ' ' + student.major + ' ' + \
                student.address + ' ' + student.phone + ' ' + student.email
            # 没有关键字则添加进hide集合
            if form.keyword.data not in word:
                hide.add(student)
    return render_template('form.html', form=form, search=True, user=user, hide=hide)

# 教师删除学生路由控制
@app.route('/u/<int:id>/delete', methods=['POST'])
def delete(id):
    if session.get('user_id') is None or id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    user = User.query.filter_by(id=id).first()
    if user.role != '教师':
        abort(400)

    student = Student.query.filter_by(
        stu_id=request.form.get('stu_id'), user_id=id).first()
    if student:
        db.session.delete(student)
    return jsonify({'result': 'success'})

# 教师更改学生路由控制
@app.route('/u/<int:id>/change', methods=['POST'])
def change(id):
    if session.get('user_id') is None or id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    user = User.query.filter_by(id=id).first()
    if user.role != '教师':
        abort(400)
    # 更改学生信息
    student = Student.query.filter_by(id=request.form.get('id')).first()
    student.stu_id = request.form.get('stu_id')
    student.name = request.form.get('name')
    student.major = request.form.get('major')
    student.address = request.form.get('address')
    student.phone = request.form.get('phone')
    student.email = request.form.get('email')
    db.session.add(student)
    return jsonify({'result': 'success'})

# 管理员登录路由控制
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    form = AdminForm()
    if form.validate_on_submit():
        session['admin'] = True
        return redirect('/admin/control')
    return render_template('form.html', form=form)

# 管理员控制台路由控制
@app.route('/admin/control', methods=['GET', 'POST'])
def control():
    if not session.get('admin'):
        abort(400)
    users = User.query.all()
    return render_template('control.html', users=users)

# 管理员新增用户路由控制
@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():
    if not session.get('admin'):
        abort(400)
    form = AdminAddForm()
    if form.validate_on_submit():
        # 简化增加用户,自动生成随机码
        n = []
        for i in range(6):
            n.append(str(random.randint(0, 9)))
        active_code = ''.join(n)
        # 自动构建通过验证的用户
        user = User(stu_id=form.stu_id.data, name=form.name.data, major=form.major.data, address=form.address.data, email=form.email.data, phone=form.phone.data,
                    password=form.password.data, role=form.role.data, active_code=active_code, active_state=True)
        db.session.add(user)
        flash('增加成功')
        return redirect(url_for('admin_add'))
    return render_template('adminadd.html', form=form)

# 管理员更改用户路由控制
@app.route('/admin/control/change', methods=['POST'])
def admin_change():
    # 更改学生信息
    user = User.query.filter_by(id=request.form.get('id')).first()
    user.stu_id = request.form.get('stu_id')
    user.name = request.form.get('name')
    user.major = request.form.get('major')
    user.address = request.form.get('address')
    user.email = request.form.get('email')
    user.phone = request.form.get('phone')
    db.session.add(user)
    return jsonify({'result': 'success'})

# 管理员删除用户路由控制
@app.route('/admin/delete', methods=['POST'])
def admin_delete():
    if session.get('admin'):
        user = User.query.filter_by(id=request.form.get('id')).first()
        if user:
            db.session.delete(user)
        return 'ok'
    abort(400)

# 管理员冻结用户路由控制
@app.route('/admin/frozen', methods=['POST'])
def admin_frozen():
    if session.get('admin'):
        user = User.query.filter_by(id=request.form.get('id')).first()
        if user:
            user.frozen = True
            db.session.add(user)
        return 'ok'
    abort(400)

# 管理员解冻用户路由控制
@app.route('/admin/normal', methods=['POST'])
def admin_normal():
    if session.get('admin'):
        user = User.query.filter_by(id=request.form.get('id')).first()
        user.frozen = False
        db.session.add(user)
        return 'ok'
    abort(400)

# 关于页面路由控制
@app.route('/about')
def about():
    return render_template('/about.html')

# 错误页面路由控制
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', code='404'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', code='500'), 500


@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', code='400'), 500


if __name__ == '__main__':
    manager.run()
