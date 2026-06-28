from flask import Flask, render_template, request, redirect, url_for, session, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from openpyxl import Workbook
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.secret_key = "supporthub-enterprise-v2-tested"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///supporthub_enterprise_v2.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs("exports", exist_ok=True)

db = SQLAlchemy(app)

TECH_ROLES = ["Admin", "Operation Supervisor", "Expert Technician", "Technician"]
ASSIGN_ROLES = ["Admin", "Operation Supervisor", "Expert Technician"]


def now():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(60), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), default="")
    phone = db.Column(db.String(50), default="")
    email = db.Column(db.String(120), default="")
    department = db.Column(db.String(120), default="")
    status = db.Column(db.String(50), default="Active")
    last_login = db.Column(db.String(50), default="-")
    created_at = db.Column(db.String(50), default=now)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), default="Customer")
    department = db.Column(db.String(120), default="General")
    branch = db.Column(db.String(120), default="Istanbul HQ")
    category = db.Column(db.String(100), default="General")
    title = db.Column(db.String(150), default="Support Request")
    device_type = db.Column(db.String(100), default="Other")
    priority = db.Column(db.String(50), default="Low")
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Open")
    assigned_group = db.Column(db.String(100), default="Help Desk")
    assigned_to = db.Column(db.String(120), default="Unassigned")
    image_filename = db.Column(db.String(200), default="")
    created_by = db.Column(db.String(100), default="")
    created_at = db.Column(db.String(50), default=now)
    assigned_at = db.Column(db.String(50), default="")
    resolved_at = db.Column(db.String(50), default="")


class TicketLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(255), nullable=False)
    user = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.String(50), default=now)


class TicketComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    user = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.String(50), default=now)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.String(50), default=now)


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_no = db.Column(db.String(50), unique=True, nullable=False)
    device_type = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), default="")
    model = db.Column(db.String(100), default="")
    serial_no = db.Column(db.String(100), default="")
    purchase_date = db.Column(db.String(50), default="")
    warranty_date = db.Column(db.String(50), default="")
    assigned_user = db.Column(db.String(120), default="")
    location = db.Column(db.String(120), default="")
    status = db.Column(db.String(50), default="Active")


class StockItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(100), default="")
    quantity = db.Column(db.Integer, default=0)
    min_quantity = db.Column(db.Integer, default=1)
    location = db.Column(db.String(120), default="")
    status = db.Column(db.String(50), default="Available")


DEFAULT_USERS = {
    "admin": ("1234", "Admin", "Umut Karakaya", "System Administrator", "0549 553 89 01", "umut.karakaya@supporthub.com", "Information Technology"),
    "ops": ("1234", "Operation Supervisor", "Operation Supervisor", "Operation Supervisor", "0555 000 00 04", "ops@supporthub.com", "Operations"),
    "expert": ("1234", "Expert Technician", "Expert Technician", "Expert Technician", "0555 000 00 05", "expert@supporthub.com", "Technical Support"),
    "tech": ("1234", "Technician", "IT Technician", "Support Technician", "0555 000 00 02", "technician@supporthub.com", "Technical Support"),
    "customer": ("1234", "Customer", "Customer User", "Customer", "0555 000 00 03", "customer@supporthub.com", "Customer"),
}


def seed_users():
    for username, data in DEFAULT_USERS.items():
        password, role, full_name, title, phone, email, department = data
        user = User.query.filter_by(username=username).first()

        if user:
            user.role = role
            user.full_name = full_name
            user.title = title
            user.phone = phone
            user.email = email
            user.department = department
            user.status = "Active"
        else:
            db.session.add(User(
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
                full_name=full_name,
                title=title,
                phone=phone,
                email=email,
                department=department,
                status="Active"
            ))

    db.session.commit()


def login_required():
    return "user" in session


def current_user():
    if not login_required():
        return None
    return User.query.filter_by(username=session["user"]).first()


def is_admin():
    return session.get("role") == "Admin"


def is_customer():
    return session.get("role") == "Customer"


def can_manage():
    return session.get("role") in TECH_ROLES


def can_assign():
    return session.get("role") in ASSIGN_ROLES


def visible_ticket_query():
    role = session.get("role")
    username = session.get("user")
    display_name = session.get("display_name")

    if role == "Customer":
        return Ticket.query.filter_by(created_by=username)

    if role == "Technician":
        return Ticket.query.filter((Ticket.assigned_to == display_name) | (Ticket.created_by == username))

    return Ticket.query


def add_log(ticket_id, action):
    db.session.add(TicketLog(ticket_id=ticket_id, action=action, user=session.get("display_name", "System")))
    db.session.commit()


def notify(username, message):
    if username:
        db.session.add(Notification(username=username, message=message))
        db.session.commit()


def notify_role(role, message):
    for user in User.query.filter_by(role=role, status="Active").all():
        db.session.add(Notification(username=user.username, message=message))
    db.session.commit()


@app.context_processor
def inject_counts():
    if not login_required():
        return {}

    query = visible_ticket_query()

    return {
        "notif_tasks": query.filter(Ticket.status != "Resolved").count(),
        "notif_count": Notification.query.filter_by(username=session["user"], is_read=False).count(),
        "current_role": session.get("role"),
    }


@app.route("/", methods=["GET", "POST"])
def login():
    with app.app_context():
        db.create_all()
        seed_users()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username, status="Active").first()

        if user and check_password_hash(user.password_hash, password):
            user.last_login = now()
            db.session.commit()

            session["user"] = user.username
            session["role"] = user.role
            session["display_name"] = user.full_name
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid username or password / Kullanıcı adı veya şifre hatalı")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    query = visible_ticket_query()

    total = query.count()
    open_tickets = query.filter_by(status="Open").count()
    in_progress = query.filter_by(status="In Progress").count()
    resolved = query.filter_by(status="Resolved").count()
    critical = query.filter_by(priority="Critical").count()
    high = query.filter_by(priority="High").count()
    medium = query.filter_by(priority="Medium").count()
    low = query.filter_by(priority="Low").count()
    latest_tickets = query.order_by(Ticket.id.desc()).limit(8).all()

    return render_template(
        "dashboard.html",
        total=total,
        open_tickets=open_tickets,
        in_progress=in_progress,
        resolved=resolved,
        critical=critical,
        high=high,
        medium=medium,
        low=low,
        latest_tickets=latest_tickets
    )


@app.route("/new-ticket", methods=["GET", "POST"])
def new_ticket():
    if not login_required():
        return redirect(url_for("login"))

    technicians = User.query.filter(User.role.in_(TECH_ROLES), User.status == "Active").all()

    if request.method == "POST":
        image_file = request.files.get("image")
        image_filename = ""

        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

        assigned_to = "Unassigned" if is_customer() else request.form.get("assigned_to", "Unassigned")
        assigned_at = now() if assigned_to != "Unassigned" else ""

        ticket = Ticket(
            customer_name=request.form.get("customer_name", session.get("display_name", "Customer")),
            department=request.form.get("department", "General"),
            branch=request.form.get("branch", "Istanbul HQ"),
            category=request.form.get("category", "General"),
            title=request.form.get("title", "Support Request"),
            device_type=request.form.get("device_type", "Other"),
            priority=request.form.get("priority", "Low"),
            description=request.form.get("description", ""),
            assigned_group="Help Desk",
            assigned_to=assigned_to,
            assigned_at=assigned_at,
            image_filename=image_filename,
            created_by=session["user"]
        )

        db.session.add(ticket)
        db.session.commit()

        add_log(ticket.id, "Ticket created")

        if assigned_to == "Unassigned":
            notify_role("Operation Supervisor", f"New unassigned ticket: HD-2026-{ticket.id:06d}")
        else:
            add_log(ticket.id, f"Ticket assigned to {assigned_to}")

        return redirect(url_for("tickets"))

    return render_template("new_ticket.html", technicians=technicians)


@app.route("/tickets")
def tickets():
    if not login_required():
        return redirect(url_for("login"))

    search = request.args.get("search", "")
    query = visible_ticket_query()

    if search:
        query = query.filter(
            (Ticket.customer_name.contains(search)) |
            (Ticket.title.contains(search)) |
            (Ticket.category.contains(search)) |
            (Ticket.device_type.contains(search)) |
            (Ticket.status.contains(search)) |
            (Ticket.assigned_to.contains(search))
        )

    technicians = User.query.filter(User.role.in_(TECH_ROLES), User.status == "Active").all()

    return render_template("tickets.html", tickets=query.order_by(Ticket.id.desc()).all(), search=search, technicians=technicians)


@app.route("/tasks")
def tasks():
    if not login_required():
        return redirect(url_for("login"))

    role = session.get("role")

    if role == "Customer":
        task_list = Ticket.query.filter_by(created_by=session["user"]).order_by(Ticket.id.desc()).all()
    elif role == "Technician":
        task_list = Ticket.query.filter_by(assigned_to=session["display_name"]).order_by(Ticket.id.desc()).all()
    elif can_assign():
        task_list = Ticket.query.filter(Ticket.status != "Resolved").order_by(Ticket.id.desc()).all()
    else:
        task_list = visible_ticket_query().order_by(Ticket.id.desc()).all()

    technicians = User.query.filter(User.role.in_(TECH_ROLES), User.status == "Active").all()

    return render_template("tasks.html", tasks=task_list, technicians=technicians)


@app.route("/assign-ticket/<int:id>", methods=["POST"])
def assign_ticket(id):
    if not login_required() or not can_assign():
        return redirect(url_for("tickets"))

    ticket = Ticket.query.get_or_404(id)
    old_assigned = ticket.assigned_to

    ticket.assigned_to = request.form.get("assigned_to", "Unassigned")
    ticket.assigned_group = "Help Desk"
    ticket.status = "In Progress"
    ticket.assigned_at = now()

    db.session.commit()

    add_log(ticket.id, f"Ticket assigned from {old_assigned} to {ticket.assigned_to}")

    assigned_user = User.query.filter_by(full_name=ticket.assigned_to).first()
    if assigned_user:
        notify(assigned_user.username, f"New task assigned: HD-2026-{ticket.id:06d}")

    return redirect(request.referrer or url_for("tasks"))


@app.route("/ticket-detail/<int:id>", methods=["GET", "POST"])
def ticket_detail(id):
    if not login_required():
        return redirect(url_for("login"))

    ticket = Ticket.query.get_or_404(id)
    allowed = visible_ticket_query().filter_by(id=id).first()

    if not allowed:
        return redirect(url_for("tickets"))

    if request.method == "POST":
        comment = request.form.get("comment", "").strip()

        if comment:
            db.session.add(TicketComment(ticket_id=id, comment=comment, user=session["display_name"]))
            db.session.commit()
            add_log(id, "Comment added")

        return redirect(url_for("ticket_detail", id=id))

    logs = TicketLog.query.filter_by(ticket_id=id).order_by(TicketLog.id.asc()).all()
    comments = TicketComment.query.filter_by(ticket_id=id).order_by(TicketComment.id.desc()).all()

    return render_template("ticket_detail.html", ticket=ticket, logs=logs, comments=comments)


@app.route("/edit-ticket/<int:id>", methods=["GET", "POST"])
def edit_ticket(id):
    if not login_required() or not can_manage():
        return redirect(url_for("tickets"))

    ticket = Ticket.query.get_or_404(id)
    technicians = User.query.filter(User.role.in_(TECH_ROLES), User.status == "Active").all()

    if request.method == "POST":
        old_status = ticket.status
        old_assigned = ticket.assigned_to

        ticket.customer_name = request.form.get("customer_name", ticket.customer_name)
        ticket.department = request.form.get("department", ticket.department)
        ticket.branch = request.form.get("branch", ticket.branch)
        ticket.category = request.form.get("category", ticket.category)
        ticket.title = request.form.get("title", ticket.title)
        ticket.device_type = request.form.get("device_type", ticket.device_type)
        ticket.priority = request.form.get("priority", ticket.priority)
        ticket.status = request.form.get("status", ticket.status)
        ticket.description = request.form.get("description", ticket.description)

        if can_assign():
            ticket.assigned_to = request.form.get("assigned_to", "Unassigned")

            if ticket.assigned_to != old_assigned:
                ticket.assigned_at = now()

        if ticket.status == "Resolved" and old_status != "Resolved":
            ticket.resolved_at = now()

        db.session.commit()

        if old_status != ticket.status:
            add_log(ticket.id, f"Status changed from {old_status} to {ticket.status}")

        if old_assigned != ticket.assigned_to:
            add_log(ticket.id, f"Assigned changed from {old_assigned} to {ticket.assigned_to}")

        add_log(ticket.id, "Ticket updated")

        return redirect(url_for("tickets"))

    return render_template("edit_ticket.html", ticket=ticket, technicians=technicians)


@app.route("/update-status/<int:id>", methods=["POST"])
def update_status(id):
    if not login_required() or not can_manage():
        return redirect(url_for("tickets"))

    ticket = Ticket.query.get_or_404(id)
    old_status = ticket.status
    ticket.status = request.form.get("status", ticket.status)

    if ticket.status == "Resolved" and old_status != "Resolved":
        ticket.resolved_at = now()

    db.session.commit()

    if old_status != ticket.status:
        add_log(ticket.id, f"Status changed from {old_status} to {ticket.status}")

    return redirect(request.referrer or url_for("tickets"))


@app.route("/delete-ticket/<int:id>")
def delete_ticket(id):
    if not login_required() or not can_assign():
        return redirect(url_for("tickets"))

    ticket = Ticket.query.get_or_404(id)

    if ticket.image_filename:
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], ticket.image_filename)

        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass

    TicketLog.query.filter_by(ticket_id=id).delete()
    TicketComment.query.filter_by(ticket_id=id).delete()
    db.session.delete(ticket)
    db.session.commit()

    return redirect(url_for("tickets"))


@app.route("/notifications")
def notifications():
    if not login_required():
        return redirect(url_for("login"))

    notes = Notification.query.filter_by(username=session["user"]).order_by(Notification.id.desc()).all()

    return render_template("notifications.html", notifications=notes)


@app.route("/mark-notifications-read")
def mark_notifications_read():
    if not login_required():
        return redirect(url_for("login"))

    Notification.query.filter_by(username=session["user"]).update({"is_read": True})
    db.session.commit()

    return redirect(url_for("notifications"))


@app.route("/assets", methods=["GET", "POST"])
def assets():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        db.session.add(Asset(
            asset_no=request.form.get("asset_no", ""),
            device_type=request.form.get("device_type", ""),
            brand=request.form.get("brand", ""),
            model=request.form.get("model", ""),
            serial_no=request.form.get("serial_no", ""),
            purchase_date=request.form.get("purchase_date", ""),
            warranty_date=request.form.get("warranty_date", ""),
            assigned_user=request.form.get("assigned_user", ""),
            location=request.form.get("location", ""),
            status=request.form.get("status", "Active")
        ))
        db.session.commit()

        return redirect(url_for("assets"))

    return render_template("assets.html", assets=Asset.query.order_by(Asset.id.desc()).all())


@app.route("/delete-asset/<int:id>")
def delete_asset(id):
    if not login_required() or not can_assign():
        return redirect(url_for("assets"))

    db.session.delete(Asset.query.get_or_404(id))
    db.session.commit()

    return redirect(url_for("assets"))


@app.route("/stock", methods=["GET", "POST"])
def stock():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        db.session.add(StockItem(
            item_name=request.form.get("item_name", ""),
            category=request.form.get("category", ""),
            quantity=int(request.form.get("quantity", 0)),
            min_quantity=int(request.form.get("min_quantity", 1)),
            location=request.form.get("location", ""),
            status=request.form.get("status", "Available")
        ))
        db.session.commit()

        return redirect(url_for("stock"))

    return render_template("stock.html", items=StockItem.query.order_by(StockItem.id.desc()).all())


@app.route("/delete-stock/<int:id>")
def delete_stock(id):
    if not login_required() or not can_assign():
        return redirect(url_for("stock"))

    db.session.delete(StockItem.query.get_or_404(id))
    db.session.commit()

    return redirect(url_for("stock"))


@app.route("/reports")
def reports():
    if not login_required():
        return redirect(url_for("login"))

    return render_template(
        "reports.html",
        total=Ticket.query.count(),
        users=User.query.count(),
        assets=Asset.query.count(),
        stock=StockItem.query.count(),
        open_tickets=Ticket.query.filter_by(status="Open").count(),
        resolved=Ticket.query.filter_by(status="Resolved").count(),
        unassigned=Ticket.query.filter_by(assigned_to="Unassigned").count()
    )


@app.route("/export-excel")
def export_excel():
    if not login_required():
        return redirect(url_for("login"))

    tickets = visible_ticket_query().order_by(Ticket.id.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Tickets"

    ws.append(["Ticket ID", "Customer", "Title", "Category", "Device", "Priority", "Status", "Assigned Group", "Assigned To", "Created By", "Created At", "Resolved At", "Description"])

    for ticket in tickets:
        ws.append([
            f"HD-2026-{ticket.id:06d}",
            ticket.customer_name,
            ticket.title,
            ticket.category,
            ticket.device_type,
            ticket.priority,
            ticket.status,
            ticket.assigned_group,
            ticket.assigned_to,
            ticket.created_by,
            ticket.created_at,
            ticket.resolved_at,
            ticket.description
        ])

    file_path = "exports/supporthub_tickets.xlsx"
    wb.save(file_path)

    return send_file(file_path, as_attachment=True)


@app.route("/export-pdf")
def export_pdf():
    if not login_required():
        return redirect(url_for("login"))

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ModuleNotFoundError:
        return "PDF export requires reportlab. Run: pip install reportlab"

    tickets = visible_ticket_query().order_by(Ticket.id.desc()).all()
    file_path = "exports/supporthub_report.pdf"

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "SupportHub Ticket Report")
    y -= 30

    c.setFont("Helvetica", 9)

    for ticket in tickets:
        line = f"HD-2026-{ticket.id:06d} | {ticket.customer_name} | {ticket.title} | {ticket.status} | {ticket.assigned_to}"
        c.drawString(40, y, line[:115])
        y -= 18

        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)

    c.save()

    return send_file(file_path, as_attachment=True)


@app.route("/users", methods=["GET", "POST"])
def users():
    if not login_required() or not is_admin():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()

        if User.query.filter_by(username=username).first():
            return render_template("users.html", users=User.query.order_by(User.id.desc()).all(), error="This username already exists.")

        db.session.add(User(
            username=username,
            password_hash=generate_password_hash(request.form.get("password", "1234")),
            role=request.form.get("role", "Customer"),
            full_name=request.form.get("full_name", username),
            title=request.form.get("title", ""),
            phone=request.form.get("phone", ""),
            email=request.form.get("email", ""),
            department=request.form.get("department", ""),
            status=request.form.get("status", "Active")
        ))
        db.session.commit()

        return redirect(url_for("users"))

    return render_template("users.html", users=User.query.order_by(User.id.desc()).all())


@app.route("/delete-user/<int:id>")
def delete_user(id):
    if not login_required() or not is_admin():
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(id)

    if user.username != session.get("user"):
        db.session.delete(user)
        db.session.commit()

    return redirect(url_for("users"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not login_required():
        return redirect(url_for("login"))

    user = current_user()

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if check_password_hash(user.password_hash, current_password) and new_password and new_password == confirm_password:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()

            return render_template("profile.html", profile=user, success="Password updated successfully.")

        return render_template("profile.html", profile=user, error="Password could not be updated.")

    return render_template("profile.html", profile=user)


@app.route("/settings")
def settings():
    if not login_required():
        return redirect(url_for("login"))

    return render_template("settings.html")


@app.route("/repair-demo-users")
def repair_demo_users():
    seed_users()
    return "Demo users repaired. Login: admin/1234, ops/1234, expert/1234, tech/1234, customer/1234."


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_users()

    app.run(debug=True)
