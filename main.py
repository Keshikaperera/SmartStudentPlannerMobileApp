"""
Smart Student Planner - Secure Enterprise Mobile Architecture
Module: LDC6004M - Mobile Application Development
Implements: Real-world Password Validation, Multi-User Registry, and Calendar Views.
"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.properties import ListProperty, StringProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
import json
import os
import re
import calendar
from datetime import datetime

# Enforce professional mobile emulation dimensions
Window.size = (420, 780)

class LoginScreen(Screen):
    def do_login(self):
        username = self.ids.username_input.text.strip()
        password = self.ids.password_input.text.strip()
        app = App.get_running_app()
        
        if not username or not password:
            self.ids.message_label.text = "Fields cannot be blank!"
            return
            
        # Validate against our database dictionary mapping parameters
        if username in app.db_storage.get("users", {}):
            if app.db_storage["users"][username] == password:
                app.logged_in_user = username
                self.ids.message_label.text = ""
                self.manager.current = "home"
            else:
                self.ids.message_label.text = "Invalid password!"
        else:
            self.ids.message_label.text = "Username not found! Please register."

    def go_to_register(self):
        self.manager.current = "register"


class RegisterScreen(Screen):
    def do_register(self):
        username = self.ids.reg_username.text.strip()
        password = self.ids.reg_password.text.strip()
        confirm = self.ids.reg_confirm.text.strip()
        app = App.get_running_app()

        # 1. Check for blank form submissions
        if not username or not password or not confirm:
            self.ids.reg_message.text = "Error: All fields are required!"
            return
            
        # 2. Check if passphrases match
        if password != confirm:
            self.ids.reg_message.text = "Error: Passwords do not match!"
            return
            
        # 3. Check for username collisions
        if username in app.db_storage.get("users", {}):
            self.ids.reg_message.text = "Error: Username already exists!"
            return

        # 4. Industry Standard Password Authentication Validation Metrics
        if len(password) < 8:
            self.ids.reg_message.text = "Error: Must be at least 8 characters long!"
            return
        if not re.search(r"[A-Z]", password):
            self.ids.reg_message.text = "Error: Must contain an uppercase letter (A-Z)!"
            return
        if not re.search(r"[a-z]", password):
            self.ids.reg_message.text = "Error: Must contain a lowercase letter (a-z)!"
            return
        if not re.search(r"\d", password):
            self.ids.reg_message.text = "Error: Must include at least one number (0-9)!"
            return
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_+-=~`\\/\[\]]", password):
            self.ids.reg_message.text = "Error: Must include a special character (!@#$ etc.)!"
            return

        # Commit secure credentials to local JSON database storage
        app.db_storage["users"][username] = password
        app.save_data_to_storage()
        
        # Clear fields and log in automatically
        self.ids.reg_username.text = ""
        self.ids.reg_password.text = ""
        self.ids.reg_confirm.text = ""
        app.logged_in_user = username
        self.ids.reg_message.text = ""
        self.manager.current = "home"

    def go_back(self):
        self.manager.current = "login"


class HomeScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        self.ids.welcome_label.text = f"Welcome, {app.logged_in_user}!"
        self.load_dashboard_metrics()
        self.check_deadline_reminders()

    def load_dashboard_metrics(self):
        app = App.get_running_app()
        all_tasks = app.db_storage.get("tasks", [])
        user_tasks = [t for t in all_tasks if t.get('user') == app.logged_in_user]
        
        pending = len([t for t in user_tasks if not t.get('completed', False)])
        completed = len([t for t in user_tasks if t.get('completed', False)])
        self.ids.metrics_label.text = f"Pending Tasks: {pending}  |  Completed: {completed}"

    def check_deadline_reminders(self):
        app = App.get_running_app()
        all_tasks = app.db_storage.get("tasks", [])
        user_tasks = [t for t in all_tasks if t.get('user') == app.logged_in_user and not t.get('completed', False)]
        
        urgent_reminders = []
        today = datetime.now().date()
        
        for task in user_tasks:
            try:
                due_date = datetime.strptime(task['due_date'], "%Y-%m-%d").date()
                days_left = (due_date - today).days
                
                if 0 <= days_left <= 2:
                    urgent_reminders.append(f"'{task['title']}' due in {days_left} days!")
                elif days_left < 0:
                    urgent_reminders.append(f"⚠️ '{task['title']}' is OVERDUE!")
            except ValueError:
                continue

        if urgent_reminders:
            self.ids.reminder_box.opacity = 1
            self.ids.reminder_text.text = "\n".join(urgent_reminders[:2])
        else:
            self.ids.reminder_box.opacity = 0
            self.ids.reminder_text.text = ""

    def logout(self):
        app = App.get_running_app()
        app.logged_in_user = ""
        self.manager.current = "login"


class TaskManagerScreen(Screen):
    current_task_id = StringProperty("")
    current_year = datetime.now().year
    current_month = datetime.now().month

    def on_pre_enter(self):
        self.refresh_task_list()
        self.generate_calendar_grid()

    def generate_calendar_grid(self):
        app = App.get_running_app()
        grid = self.ids.calendar_grid
        grid.clear_widgets()
        
        all_tasks = app.db_storage.get("tasks", [])
        active_dates = [t['due_date'] for t in all_tasks if t.get('user') == app.logged_in_user]

        self.ids.calendar_header.text = f"{calendar.month_name[self.month]} {self.year}"
        
        for day in ["M", "T", "W", "T", "F", "S", "S"]:
            grid.add_widget(Label(text=day, font_size=12, bold=True, color=(0.6, 0.6, 0.7, 1), size_hint_y=None, height=25))

        month_matrix = calendar.monthcalendar(self.year, self.month)
        for week in month_matrix:
            for day in week:
                if day == 0:
                    grid.add_widget(Label())
                else:
                    date_str = f"{self.year}-{self.month:02d}-{day:02d}"
                    is_marked = date_str in active_dates
                    
                    btn_bg = (0.25, 0.45, 0.85, 1) if is_marked else (0.18, 0.20, 0.30, 1)
                    txt_color = (1, 1, 1, 1) if is_marked else (0.8, 0.8, 0.8, 1)
                    
                    day_btn = Button(
                        text=str(day),
                        font_size=13,
                        background_normal="",
                        background_color=btn_bg,
                        color=txt_color
                    )
                    day_btn.bind(on_release=lambda x, d=date_str: self.filter_tasks_by_date(d))
                    grid.add_widget(day_btn)

    def filter_tasks_by_date(self, selected_date):
        self.ids.search_bar.text = selected_date
        self.refresh_task_list(selected_date)

    def change_month(self, direction):
        self.month += direction
        if self.month > 12:
            self.month = 1
            self.year += 1
        elif self.month < 1:
            self.month = 12
            self.year -= 1
        self.generate_calendar_grid()

    @property
    def year(self): return self.current_year
    @year.setter
    def year(self, value): self.current_year = value

    @property
    def month(self): return self.current_month
    @month.setter
    def month(self, value): self.current_month = value

    def refresh_task_list(self, filter_text=""):
        app = App.get_running_app()
        container = self.ids.tasks_container
        container.clear_widgets()
        
        search_keyword = filter_text.lower().strip()
        all_tasks = app.db_storage.get("tasks", [])
        user_tasks = [t for t in all_tasks if t.get('user') == app.logged_in_user]
        
        for task in user_tasks:
            if search_keyword and (search_keyword not in task['title'].lower() and search_keyword not in task['module'].lower() and search_keyword not in task['due_date']):
                continue
                
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=75, spacing=8, padding=[4,4,4,4])
            status_symbol = "[X]" if task.get('completed', False) else "[ ]"
            info_text = f"{status_symbol} {task['title']} ({task['module']})\nDue: {task['due_date']} | Pri: {task['priority']}"
            
            lbl = Label(text=info_text, halign='left', valign='middle', size_hint_x=0.55, color=(1,1,1,1))
            lbl.bind(size=lbl.setter('text_size'))
            row.add_widget(lbl)
            
            btn_status = Button(text="Toggle", size_hint_x=0.15, background_color=(0.2, 0.6, 0.8, 1))
            btn_status.bind(on_release=lambda x, t_id=task['id']: self.toggle_task_status(t_id))
            row.add_widget(btn_status)
            
            btn_edit = Button(text="Edit", size_hint_x=0.15, background_color=(0.9, 0.6, 0.2, 1))
            btn_edit.bind(on_release=lambda x, t_id=task['id']: self.populate_edit_fields(t_id))
            row.add_widget(btn_edit)
            
            btn_del = Button(text="Del", size_hint_x=0.15, background_color=(0.8, 0.2, 0.2, 1))
            btn_del.bind(on_release=lambda x, t_id=task['id']: self.delete_task(t_id))
            row.add_widget(btn_del)
            
            container.add_widget(row)

    def add_task(self):
        title = self.ids.task_title.text.strip()
        module = self.ids.task_module.text.strip()
        due_date = self.ids.task_due.text.strip()
        priority = self.ids.task_priority.text.strip()
        notes = self.ids.task_notes.text.strip()

        if not title or not module or not due_date:
            self.ids.error_feedback.text = "Error: Missing required fields!"
            return
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            self.ids.error_feedback.text = "Error: Use YYYY-MM-DD template format!"
            return

        app = App.get_running_app()

        if self.current_task_id:
            for t in app.db_storage["tasks"]:
                if t['id'] == self.current_task_id:
                    t.update({"title": title, "module": module, "due_date": due_date, "priority": priority, "notes": notes})
            self.current_task_id = ""
            self.ids.btn_submit_task.text = "Add Task Record"
        else:
            new_task = {
                "id": str(len(app.db_storage["tasks"]) + 1),
                "user": app.logged_in_user,
                "title": title,
                "module": module,
                "due_date": due_date,
                "priority": priority if priority in ["High", "Medium", "Low"] else "Medium",
                "notes": notes,
                "completed": False
            }
            app.db_storage["tasks"].append(new_task)

        app.save_data_to_storage()
        self.clear_form_inputs()
        self.refresh_task_list()
        self.generate_calendar_grid()
        self.ids.error_feedback.text = "Success: System storage updated safely."

    def populate_edit_fields(self, task_id):
        app = App.get_running_app()
        task = next((t for t in app.db_storage["tasks"] if t['id'] == str(task_id)), None)
        if task:
            self.current_task_id = str(task_id)
            self.ids.task_title.text = task['title']
            self.ids.task_module.text = task['module']
            self.ids.task_due.text = task['due_date']
            self.ids.task_priority.text = task['priority']
            self.ids.task_notes.text = task['notes']
            self.ids.btn_submit_task.text = "Update Task Changes"

    def delete_task(self, task_id):
        app = App.get_running_app()
        app.db_storage["tasks"] = [t for t in app.db_storage["tasks"] if t['id'] != str(task_id)]
        app.save_data_to_storage()
        self.refresh_task_list()
        self.generate_calendar_grid()

    def toggle_task_status(self, task_id):
        app = App.get_running_app()
        for t in app.db_storage["tasks"]:
            if t['id'] == str(task_id):
                t['completed'] = not t['completed']
        app.save_data_to_storage()
        self.refresh_task_list()

    def clear_form_inputs(self):
        self.ids.task_title.text = ""
        self.ids.task_module.text = ""
        self.ids.task_due.text = ""
        self.ids.task_priority.text = "Medium"
        self.ids.task_notes.text = ""
        self.current_task_id = ""
        self.ids.btn_submit_task.text = "Add Task Record"

    def go_back(self):
        self.manager.current = "home"


class SmartPlannerApp(App):
    db_storage = DictProperty({"users": {"Samanthi": "1234"}, "tasks": []})
    logged_in_user = ""

    def build(self):
        self.storage_file = "student_planner_data.json"
        self.load_data_from_storage()

        Builder.load_file("ui/login.kv")
        Builder.load_file("ui/register.kv")
        Builder.load_file("ui/home.kv")
        Builder.load_file("ui/profile.kv")

        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(TaskManagerScreen(name="profile"))
        return sm

    def load_data_from_storage(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    if "users" in data and "tasks" in data:
                        self.db_storage = data
            except Exception:
                pass

    def save_data_to_storage(self):
        try:
            with open(self.storage_file, "w") as f:
                json.dump(dict(self.db_storage), f, indent=4)
        except Exception as e:
            print(f"File Output Error: {e}")

if __name__ == "__main__":
    SmartPlannerApp().run()