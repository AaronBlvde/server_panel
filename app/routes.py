from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Role, ContainerConfig
from . import db, login_manager
from .forms import LoginForm, AddUserForm
import docker

client = docker.from_env()
main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----- AUTH -----
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Неверный логин или пароль', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

# ----- DASHBOARD -----
@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# ----- ADD USER (ADMIN ONLY) -----
@main.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash("Только админ может добавлять пользователей", "danger")
        return redirect(url_for('main.dashboard'))

    form = AddUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Пользователь уже существует", "danger")
        else:
            user = User(username=form.username.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            roles = Role(
                user_id=user.id,
                view=form.view.data,
                start_stop=form.start_stop.data,
                rebuild=form.rebuild.data
            )
            db.session.add(roles)
            db.session.commit()
            flash("Пользователь создан", "success")
            return redirect(url_for('main.dashboard'))
    return render_template('add_user.html', form=form)

# ----- UTILS -----
def get_user_roles():
    if current_user.roles:
        return current_user.roles
    return Role(view=False, start_stop=False, rebuild=False)

# ----- CONTAINERS -----
@main.route('/containers')
@login_required
def containers():
    roles = get_user_roles()
    if not roles.view:
        flash("Нет прав для просмотра контейнеров", "danger")
        return redirect(url_for('main.dashboard'))

    containers_list = []
    for c in client.containers.list(all=True):
        # Сбор информации о портах
        ports = []
        for mappings in (c.attrs.get('NetworkSettings', {}).get('Ports') or {}).values():
            if mappings:
                ports.append(mappings[0]['HostPort'])

        # Сбор информации о хостовых путях (Source)
        host_paths = [m.get("Source") for m in c.attrs.get('Mounts', [])]

        containers_list.append({
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "ports": ports,
            "host_paths": host_paths
        })

    return render_template('containers.html', containers=containers_list, roles=roles)

@main.route('/containers/<container_id>/logs')
@login_required
def container_logs(container_id):
    roles = get_user_roles()
    if not roles.view:
        flash("Нет прав для просмотра логов", "danger")
        return redirect(url_for('main.containers'))
    container = client.containers.get(container_id)
    return render_template('container_logs.html', container=container)

@main.route('/containers/<container_id>/logs_json')
@login_required
def container_logs_json(container_id):
    roles = get_user_roles()
    if not roles.view:
        return jsonify({"error": "Нет прав"}), 403
    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=50).decode()
        return jsonify({"logs": logs})
    except docker.errors.NotFound:
        return jsonify({"error": "Контейнер не найден"}), 404

@main.route('/containers/<container_id>/start')
@login_required
def container_start(container_id):
    roles = get_user_roles()
    if not roles.start_stop:
        flash("Нет прав для запуска/остановки", "danger")
        return redirect(url_for('main.containers'))
    container = client.containers.get(container_id)
    try:
        container.start()
        flash(f"Контейнер {container.name} запущен", "success")
    except Exception as e:
        flash(f"Ошибка при запуске: {e}", "danger")
    return redirect(url_for('main.containers'))

@main.route('/containers/<container_id>/stop')
@login_required
def container_stop(container_id):
    roles = get_user_roles()
    if not roles.start_stop:
        flash("Нет прав для запуска/остановки", "danger")
        return redirect(url_for('main.containers'))
    container = client.containers.get(container_id)
    try:
        container.stop()
        flash(f"Контейнер {container.name} остановлен", "success")
    except Exception as e:
        flash(f"Ошибка при остановке: {e}", "danger")
    return redirect(url_for('main.containers'))

# ----- REBUILD CONTAINER WITH PATH MEMORY -----
@main.route('/containers/rebuild/<container_name>', methods=['GET', 'POST'])
@login_required
def rebuild_container(container_name):
    roles = get_user_roles()
    if not roles.rebuild:
        flash("Нет прав для пересборки", "danger")
        return redirect(url_for('main.containers'))

    config = ContainerConfig.query.filter_by(container_name=container_name).first()
    last_path = config.last_build_path if config else ""

    if request.method == 'POST':
        folder_path = request.form['folder_path']

        if not config:
            config = ContainerConfig(container_name=container_name, last_build_path=folder_path)
            db.session.add(config)
        else:
            config.last_build_path = folder_path
        db.session.commit()

        try:
            client.images.build(path=folder_path, tag=container_name)
            flash(f"Контейнер {container_name} пересобран", "success")
        except Exception as e:
            flash(f"Ошибка при пересборке: {e}", "danger")

        return redirect(url_for('main.containers'))

    return render_template('rebuild_container.html', container_name=container_name, last_path=last_path)
