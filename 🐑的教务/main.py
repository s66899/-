#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青羽教务系统 - 重构版本
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import csv
import shutil
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
import threading
from tkinter import font as tkfont
import re
import io

# ==================== 数据模型 ====================

def generate_id() -> str:
    import uuid
    return str(uuid.uuid4())[:8]

class Student:
    def __init__(self, name: str, phone: str, birth_date: str, level: str, coach: str):
        self.id = generate_id()
        self.name = name
        self.phone = phone
        self.birth_date = birth_date
        self.level = level
        self.coach = coach
        self.register_date = datetime.now().strftime("%Y-%m-%d")
        self.status = "active"
        self.note = ""
        self.purchased_hours = 0
        self.bonus_hours = 0
        self.remaining_hours = 0

    def calculate_age(self) -> int:
        try:
            birth = datetime.strptime(self.birth_date, "%Y-%m-%d")
            today = datetime.now()
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except:
            return 0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "phone": self.phone,
            "birth_date": self.birth_date, "age": self.calculate_age(),
            "level": self.level, "coach": self.coach,
            "register_date": self.register_date, "status": self.status,
            "note": self.note, "purchased_hours": self.purchased_hours,
            "bonus_hours": self.bonus_hours, "remaining_hours": self.remaining_hours
        }

class Course:
    def __init__(self, name: str, level: str, total_hours: int, price: float):
        self.id = generate_id()
        self.name = name
        self.level = level
        self.total_hours = total_hours
        self.price = price
        self.remaining_hours = total_hours
        self.start_date = ""
        self.end_date = ""
        self.student_ids = []
        self.coach = ""
        self.description = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "level": self.level,
            "total_hours": self.total_hours, "remaining_hours": self.remaining_hours,
            "price": self.price, "start_date": self.start_date, "end_date": self.end_date,
            "student_ids": self.student_ids, "coach": self.coach, "description": self.description
        }

class Schedule:
    def __init__(self, student_id: str, course_id: str, week_day: str, time_slot: str, coach: str = ""):
        self.id = generate_id()
        self.student_id = student_id
        self.course_id = course_id
        self.week_day = week_day
        self.time_slot = time_slot
        self.coach = coach
        self.status = "scheduled"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "student_id": self.student_id, "course_id": self.course_id,
            "week_day": self.week_day, "time_slot": self.time_slot,
            "coach": self.coach, "status": self.status
        }

class Attendance:
    def __init__(self, student_id: str, course_id: str, schedule_id: str, date: str, hours: int = 1):
        self.id = generate_id()
        self.student_id = student_id
        self.course_id = course_id
        self.schedule_id = schedule_id
        self.date = date
        self.status = "present"
        self.hours_used = hours

    def to_dict(self) -> dict:
        return {
            "id": self.id, "student_id": self.student_id, "course_id": self.course_id,
            "schedule_id": self.schedule_id, "date": self.date,
            "status": self.status, "hours_used": self.hours_used
        }

# ==================== 数据管理 ====================

class DataManager:
    def __init__(self, data_file: str = "教务数据.json"):
        self.data_file = data_file
        self.data = self.load_data()

    def load_data(self) -> dict:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_default_data()
        return self.create_default_data()

    def create_default_data(self) -> dict:
        return {
            "students": [], "courses": [], "schedules": [], "attendances": [],
            "settings": {
                "time_slots": {
                    "星期一": ["17:00-18:30", "19:00-20:30"],
                    "星期二": ["17:00-18:30", "19:00-20:30"],
                    "星期三": ["17:00-18:30", "19:00-20:30"],
                    "星期四": ["17:00-18:30", "18:30-20:00"],
                    "星期五": ["17:00-18:30", "19:00-20:30"],
                    "星期六": ["09:00-10:30", "10:30-12:00", "14:00-15:30", "15:30-17:00", "17:00-18:30", "19:00-20:30"],
                    "星期日": ["09:00-10:30", "10:30-12:00", "14:00-15:30", "15:30-17:00", "17:00-18:30", "18:30-20:00"]
                },
                "coaches": ["王教练", "陈教练"],
                "course_levels": ["初级", "中级", "高级", "竞赛级"],
                "max_students_per_slot": 12,
                "max_students_per_coach": 6
            }
        }

    def save_data(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_student(self, student: Student):
        self.data["students"].append(student.to_dict())
        self.save_data()

    def get_students(self, status: str = None) -> List[dict]:
        if status:
            return [s for s in self.data["students"] if s.get("status") == status]
        return self.data["students"]

    def update_student(self, student_id: str, updates: dict):
        for i, s in enumerate(self.data["students"]):
            if s["id"] == student_id:
                self.data["students"][i].update(updates)
                self.save_data()
                return True
        return False

    def delete_students(self, student_ids: List[str]):
        self.data["students"] = [s for s in self.data["students"] if s["id"] not in student_ids]
        self.save_data()

    def find_student_by_name(self, name: str) -> Optional[dict]:
        for s in self.data["students"]:
            if s.get("name") == name:
                return s
        return None

    def find_course_by_name(self, name: str) -> Optional[dict]:
        for c in self.data["courses"]:
            if c.get("name") == name:
                return c
        return None

    def add_course(self, course: Course):
        self.data["courses"].append(course.to_dict())
        self.save_data()

    def get_courses(self) -> List[dict]:
        return self.data["courses"]

    def add_schedule(self, schedule: Schedule):
        self.data["schedules"].append(schedule.to_dict())
        self.save_data()

    def get_schedules(self) -> List[dict]:
        return self.data["schedules"]

    def clear_schedules(self):
        self.data["schedules"] = []
        self.save_data()

    def add_attendance(self, attendance: Attendance):
        self.data["attendances"].append(attendance.to_dict())
        hours = attendance.hours_used
        for s in self.data["students"]:
            if s["id"] == attendance.student_id:
                s["remaining_hours"] = max(0, s.get("remaining_hours", 0) - hours)
                break
        for c in self.data["courses"]:
            if c["id"] == attendance.course_id:
                c["remaining_hours"] = max(0, c.get("remaining_hours", 0) - hours)
                break
        self.save_data()

    def get_attendances(self) -> List[dict]:
        return self.data["attendances"]

    def get_statistics(self) -> dict:
        stats = {
            "total_students": len(self.data["students"]),
            "active_students": len([s for s in self.data["students"] if s.get("status") == "active"]),
            "potential_students": len([s for s in self.data["students"] if s.get("status") == "potential"]),
            "total_courses": len(self.data["courses"]),
            "total_hours": sum(c.get("total_hours", 0) for c in self.data["courses"]),
            "remaining_hours": sum(c.get("remaining_hours", 0) for c in self.data["courses"]),
            "consumption_rate": 0
        }
        if stats["total_hours"] > 0:
            stats["consumption_rate"] = round((stats["total_hours"] - stats["remaining_hours"]) / stats["total_hours"] * 100, 2)
        return stats

# ==================== 业务逻辑 ====================

class StudentService:
    def __init__(self, dm: DataManager):
        self.dm = dm

    def parse_date(self, date_str: str) -> str:
        if not date_str or not date_str.strip():
            return f"{datetime.now().year - 10}-01-01"
        date_str = date_str.strip()
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]:
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except:
                pass
        if date_str.isdigit():
            return f"{datetime.now().year - int(date_str)}-01-01"
        return f"{datetime.now().year - 10}-01-01"

    def import_from_csv(self, filepath: str) -> tuple[int, list]:
        imported, errors = 0, []
        try:
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']
            content = None
            for enc in encodings:
                try:
                    with open(filepath, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except:
                    continue
            if content is None:
                errors.append("无法读取文件编码")
                return 0, errors

            reader = csv.DictReader(io.StringIO(content))
            fieldnames = reader.fieldnames or []
            col_map = {}
            for name in fieldnames:
                nl = name.lower().strip()
                if nl in ['姓名', 'name', '学生姓名']: col_map['name'] = name
                elif nl in ['电话', 'phone', '手机', 'mobile', '联系电话']: col_map['phone'] = name
                elif nl in ['出生日期', 'birthday', 'birth_date', '生日']: col_map['birth_date'] = name
                elif nl in ['年龄', 'age']: col_map['age'] = name
                elif nl in ['等级', 'level']: col_map['level'] = name
                elif nl in ['教练', 'teacher', 'coach']: col_map['coach'] = name
                elif nl in ['状态', 'status']: col_map['status'] = name
                elif nl in ['备注', 'note']: col_map['note'] = name
                elif '购买' in name or '购课' in name: col_map['purchased'] = name
                elif '赠送' in name: col_map['bonus'] = name
                elif '剩余' in name: col_map['remaining'] = name

            for row_num, row in enumerate(reader, start=2):
                try:
                    name = row.get(col_map.get('name', ''), '').strip()
                    if not name:
                        errors.append(f"第{row_num}行: 缺少姓名")
                        continue
                    phone = row.get(col_map.get('phone', ''), '').strip()
                    birth_str = row.get(col_map.get('birth_date', ''), '').strip()
                    age_str = row.get(col_map.get('age', ''), '').strip()
                    birth_date = self.parse_date(birth_str) if birth_str else self.parse_date(age_str) if age_str else f"{datetime.now().year - 10}-01-01"
                    level = row.get(col_map.get('level', ''), '').strip() or '初级'
                    coach = row.get(col_map.get('coach', ''), '').strip() or ''

                    student = Student(name=name, phone=phone, birth_date=birth_date, level=level, coach=coach)

                    # 课时信息
                    purchased = row.get(col_map.get('purchased', ''), '').strip()
                    bonus = row.get(col_map.get('bonus', ''), '').strip()
                    remaining = row.get(col_map.get('remaining', ''), '').strip()

                    # 从"总课时"列解析
                    total_str = row.get('总课时', '').strip()
                    if total_str and '课时' in total_str:
                        total_str = total_str.replace('课时', '').strip()
                        try:
                            total_val = float(total_str)
                            student.purchased_hours = int(total_val)
                            student.remaining_hours = int(total_val)
                        except:
                            pass

                    if purchased:
                        try:
                            student.purchased_hours = int(float(purchased.replace('课时', '').strip()))
                        except:
                            pass
                    if bonus:
                        try:
                            student.bonus_hours = int(float(bonus.replace('课时', '').strip()))
                        except:
                            pass
                    if remaining:
                        try:
                            student.remaining_hours = int(float(remaining.replace('课时', '').strip()))
                        except:
                            pass

                    status = row.get(col_map.get('status', ''), '').strip()
                    if status in ['在读', 'active', '在读']: student.status = 'active'
                    elif status in ['已结', 'inactive']: student.status = 'inactive'

                    note = row.get(col_map.get('note', ''), '').strip()
                    student.note = note

                    self.dm.add_student(student)
                    imported += 1
                except Exception as e:
                    errors.append(f"第{row_num}行: {str(e)}")
        except Exception as e:
            errors.append(f"文件读取错误: {str(e)}")
        return imported, errors

    def export_to_csv(self, filepath: str, students: List[dict]):
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ["姓名", "电话", "出生日期", "年龄", "等级", "教练", "状态", "购买课时", "赠送课时", "剩余课时", "注册日期", "备注"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for s in students:
                    writer.writerow({
                        "姓名": s.get("name", ""), "电话": s.get("phone", ""),
                        "出生日期": s.get("birth_date", ""), "年龄": s.get("age", 0),
                        "等级": s.get("level", ""), "教练": s.get("coach", ""),
                        "状态": s.get("status", ""), "购买课时": s.get("purchased_hours", 0),
                        "赠送课时": s.get("bonus_hours", 0), "剩余课时": s.get("remaining_hours", 0),
                        "注册日期": s.get("register_date", ""), "备注": s.get("note", "")
                    })
            return True, ""
        except Exception as e:
            return False, str(e)

class ScheduleService:
    def __init__(self, dm: DataManager):
        self.dm = dm

    def import_from_csv(self, filepath: str) -> tuple[int, list]:
        imported, errors = 0, []
        try:
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']
            content = None
            for enc in encodings:
                try:
                    with open(filepath, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except:
                    continue
            if content is None:
                errors.append("无法读取文件编码")
                return 0, errors

            lines = content.strip().split('\n')
            lines = [l.strip() for l in lines if l.strip()]
            if not lines:
                errors.append("文件为空")
                return 0, errors

            is_grid = any(kw in lines[0] for kw in ['周一', '周二', '周三', '周四', '周五', '周六', '周日'])
            if is_grid:
                return self._import_grid(lines, errors)
            else:
                return self._import_standard(content, errors)
        except Exception as e:
            errors.append(f"文件读取错误: {str(e)}")
        return imported, errors

    def _import_grid(self, lines: list, errors: list) -> tuple[int, list]:
        imported = 0
        header_line = None
        for line in lines[:5]:
            if any(kw in line for kw in ['周一', '周二', '周三', '周四', '周五', '周六', '周日']):
                header_line = line
                break
        if not header_line:
            errors.append("未找到表头行")
            return 0, errors

        headers = list(csv.reader(io.StringIO(header_line)))[0]
        week_map = {
            '周一': '星期一', '星期一': '星期一', 'mon': '星期一',
            '周二': '星期二', '星期二': '星期二', 'tue': '星期二',
            '周三': '星期三', '星期三': '星期三', 'wed': '星期三',
            '周四': '星期四', '星期四': '星期四', 'thu': '星期四',
            '周五': '星期五', '星期五': '星期五', 'fri': '星期五',
            '周六': '星期六', '星期六': '星期六', 'sat': '星期六',
            '周日': '星期日', '星期日': '星期日', 'sun': '星期日',
        }
        col_info = []
        for h in headers:
            h = h.strip()
            if not h:
                col_info.append(None)
                continue
            week_day = None
            for key, val in week_map.items():
                if key in h:
                    week_day = val
                    break
            time_str = h
            for key in week_map:
                time_str = time_str.replace(key, '')
            time_str = time_str.replace('：', ':').strip()
            tm = re.match(r'(\d{1,2}):(\d{2})[-~](\d{1,2}):(\d{2})', time_str)
            time_slot = None
            if tm:
                time_slot = f"{int(tm.group(1)):02d}:{tm.group(2)}-{int(tm.group(3)):02d}:{tm.group(4)}"
            col_info.append((week_day, time_slot) if week_day and time_slot else None)

        data_start = 0
        for i, line in enumerate(lines):
            if '学员' in line:
                data_start = i
                break
        if data_start == 0:
            for i, line in enumerate(lines):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) > 1 and parts[0] in ['', '学员']:
                    data_start = i
                    break

        for line_idx in range(data_start, len(lines)):
            line = lines[line_idx].strip()
            if not line or all(c in ',，\t ' for c in line):
                continue
            try:
                cells = list(csv.reader(io.StringIO(line)))[0]
            except:
                continue
            if cells[0].strip() in ['教练', '时间', '']:
                continue

            for col_idx in range(1, len(cells)):
                if col_idx >= len(col_info) or col_info[col_idx] is None:
                    continue
                week_day, time_slot = col_info[col_idx]
                cell_content = cells[col_idx].strip()
                if not cell_content:
                    continue
                student_names = re.split(r'[,\n，]', cell_content)
                student_names = [s.strip() for s in student_names if s.strip()]

                for sn in student_names:
                    clean_name = re.sub(r'[~（）()~].*$', '', sn).strip()
                    if not clean_name:
                        continue
                    student = self.dm.find_student_by_name(clean_name)
                    if not student:
                        student = Student(name=clean_name, phone='', birth_date=f"{datetime.now().year - 10}-01-01", level='初级', coach='')
                        self.dm.add_student(student)
                        student = self.dm.find_student_by_name(clean_name)
                    course = self.dm.find_course_by_name("羽毛球课")
                    if not course:
                        course = Course(name="羽毛球课", level="初级", total_hours=50, price=3750)
                        self.dm.add_course(course)
                        course = self.dm.find_course_by_name("羽毛球课")
                    exists = any(s.get("student_id") == student["id"] and s.get("week_day") == week_day and s.get("time_slot") == time_slot for s in self.dm.data["schedules"])
                    if not exists:
                        sched = Schedule(student_id=student["id"], course_id=course["id"] if course else "", week_day=week_day, time_slot=time_slot, coach=student.get("coach", ""))
                        self.dm.add_schedule(sched)
                        imported += 1
        return imported, errors

    def _import_standard(self, content: str, errors: list) -> tuple[int, list]:
        imported = 0
        reader = csv.DictReader(io.StringIO(content))
        week_map = {'周一': '星期一', '星期一': '星期一', '周二': '星期二', '星期二': '星期二', '周三': '星期三', '星期三': '星期三', '周四': '星期四', '星期四': '星期四', '周五': '星期五', '星期五': '星期五', '周六': '星期六', '星期六': '星期六', '周日': '星期日', '星期日': '星期日'}
        for row_num, row in enumerate(reader, start=2):
            try:
                headers = list(row.keys())
                student_name, course_name, week_day, time_slot = '', '', '', ''
                for header in headers:
                    value = row[header].strip()
                    if not value:
                        continue
                    if '姓名' in header:
                        if not student_name: student_name = value
                    if '课程' in header:
                        if not course_name: course_name = value
                    for key, val in week_map.items():
                        if key in value:
                            if not week_day: week_day = val
                            break
                    if not time_slot:
                        tm = re.search(r'(\d{1,2}:\d{2}[-~]\d{1,2}:\d{2})', value)
                        if tm: time_slot = tm.group(1).replace('~', '-')
                if not student_name or not week_day or not time_slot:
                    continue
                tm = re.match(r'(\d{1,2}):(\d{2})[-~](\d{1,2}):(\d{2})', time_slot)
                if tm:
                    time_slot = f"{int(tm.group(1)):02d}:{tm.group(2)}-{int(tm.group(3)):02d}:{tm.group(4)}"
                student = self.dm.find_student_by_name(student_name)
                if not student:
                    student = Student(name=student_name, phone='', birth_date=f"{datetime.now().year - 10}-01-01", level='初级', coach='')
                    self.dm.add_student(student)
                    student = self.dm.find_student_by_name(student_name)
                course = self.dm.find_course_by_name(course_name or "羽毛球课")
                if not course:
                    course = Course(name=course_name or "羽毛球课", level="初级", total_hours=50, price=3750)
                    self.dm.add_course(course)
                    course = self.dm.find_course_by_name(course_name or "羽毛球课")
                exists = any(s.get("student_id") == student["id"] and s.get("week_day") == week_day and s.get("time_slot") == time_slot for s in self.dm.data["schedules"])
                if not exists:
                    sched = Schedule(student_id=student["id"], course_id=course["id"] if course else "", week_day=week_day, time_slot=time_slot, coach=student.get("coach", ""))
                    self.dm.add_schedule(sched)
                    imported += 1
            except Exception as e:
                errors.append(f"第{row_num}行: {str(e)}")
        return imported, errors

    def export_to_csv(self, filepath: str) -> tuple[int, str]:
        try:
            schedules = self.dm.get_schedules()
            student_map = {s["id"]: s["name"] for s in self.dm.data["students"]}
            course_map = {c["id"]: c["name"] for c in self.dm.data["courses"]}
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["学员姓名", "课程名称", "星期", "时间段", "教练"])
                writer.writeheader()
                for s in schedules:
                    writer.writerow({
                        "学员姓名": student_map.get(s.get("student_id", ""), ""),
                        "课程名称": course_map.get(s.get("course_id", ""), ""),
                        "星期": s.get("week_day", ""),
                        "时间段": s.get("time_slot", ""),
                        "教练": s.get("coach", "")
                    })
            return len(schedules), ""
        except Exception as e:
            return 0, str(e)

class AttendanceService:
    def __init__(self, dm: DataManager):
        self.dm = dm

    def take_attendance(self, schedule_id: str, student_ids: List[str], date: str = None, hours: int = 1):
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        schedule = None
        for s in self.dm.data["schedules"]:
            if s["id"] == schedule_id:
                schedule = s
                break
        if not schedule:
            return False, "排课记录不存在"
        for student_id in student_ids:
            att = Attendance(student_id=student_id, course_id=schedule["course_id"], schedule_id=schedule_id, date=date, hours=hours)
            self.dm.add_attendance(att)
        return True, f"成功为{len(student_ids)}名学员消课"

# ==================== 界面 ====================

class BaseFrame(ttk.Frame):
    def __init__(self, parent, dm: DataManager, user_role):
        super().__init__(parent)
        self.dm = dm
        self.user_role = user_role
        self.setup_fonts()
        self.create_widgets()

    def setup_fonts(self):
        self.title_font = tkfont.Font(family="Microsoft YaHei", size=16, weight="bold")
        self.header_font = tkfont.Font(family="Microsoft YaHei", size=12, weight="bold")
        self.normal_font = tkfont.Font(family="Microsoft YaHei", size=10)

    def create_widgets(self):
        pass

    def show_message(self, title: str, message: str, is_error: bool = False):
        if is_error:
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)

# ==================== 学员管理 ====================

class AdminStudentFrame(BaseFrame):
    def create_widgets(self):
        ttk.Label(self, text="学员管理", font=self.title_font).pack(pady=10)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(toolbar, text="添加学员", command=self.add_student).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="删除选中", command=self.delete_students).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导入CSV", command=self.import_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出CSV", command=self.export_csv).pack(side=tk.LEFT, padx=2)

        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search)
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        columns = ("选择", "姓名", "电话", "年龄", "等级", "教练", "购买课时", "赠送课时", "剩余课时", "状态")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        col_widths = [50, 80, 100, 50, 60, 70, 70, 70, 70, 60]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_students()

    def load_students(self, search_text: str = ""):
        for item in self.tree.get_children():
            self.tree.delete(item)
        students = self.dm.get_students()
        if search_text:
            search_text = search_text.lower()
            students = [s for s in students if search_text in s.get("name", "").lower() or search_text in s.get("phone", "").lower()]
        for s in students:
            values = ("", s.get("name", ""), s.get("phone", ""), s.get("age", 0), s.get("level", ""), s.get("coach", ""),
                      s.get("purchased_hours", 0), s.get("bonus_hours", 0), s.get("remaining_hours", 0), s.get("status", ""))
            self.tree.insert("", tk.END, values=values)

    def on_search(self, *args):
        self.load_students(self.search_var.get())

    def add_student(self):
        dialog = AddStudentDialog(self, self.dm)
        self.wait_window(dialog)
        if dialog.result:
            self.load_students()

    def delete_students(self):
        selected = self.tree.selection()
        if not selected:
            self.show_message("提示", "请先选择要删除的学员")
            return
        if messagebox.askyesno("确认", f"确定要删除选中的{len(selected)}名学员吗？"):
            self.show_message("提示", f"已删除{len(selected)}名学员")

    def import_csv(self):
        filepath = filedialog.askopenfilename(title="选择CSV文件", filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")])
        if filepath:
            service = StudentService(self.dm)
            imported, errors = service.import_from_csv(filepath)
            if errors and imported == 0:
                self.show_message("导入错误", f"错误:\n" + "\n".join(errors[:10]), True)
            elif errors:
                self.show_message("导入完成", f"成功导入{imported}条记录\n\n部分错误:\n" + "\n".join(errors[:5]))
            else:
                self.show_message("成功", f"成功导入{imported}条记录")
            self.load_students()

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(title="保存CSV文件", defaultextension=".csv", filetypes=[("CSV文件", "*.csv")])
        if filepath:
            service = StudentService(self.dm)
            success, error = service.export_to_csv(filepath, self.dm.get_students())
            if success:
                self.show_message("成功", f"已导出{len(self.dm.get_students())}条记录")
            else:
                self.show_message("导出错误", f"导出失败: {error}", True)

# ==================== 课程管理 ====================

class AdminCourseFrame(BaseFrame):
    def create_widgets(self):
        ttk.Label(self, text="课程管理", font=self.title_font).pack(pady=10)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(toolbar, text="添加课程", command=self.add_course).pack(side=tk.LEFT, padx=2)
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        columns = ("课程名称", "水平", "总课时", "剩余课时", "价格", "教练", "学员数", "消耗率")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_courses()

    def load_courses(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        courses = self.dm.get_courses()
        for c in courses:
            total = c.get("total_hours", 0)
            remaining = c.get("remaining_hours", 0)
            rate = round((total - remaining) / total * 100, 1) if total > 0 else 0
            self.tree.insert("", tk.END, values=(c.get("name", ""), c.get("level", ""), total, remaining, f"¥{c.get('price', 0)}", c.get("coach", ""), len(c.get("student_ids", [])), f"{rate}%"))

    def add_course(self):
        dialog = AddCourseDialog(self, self.dm)
        self.wait_window(dialog)
        if dialog.result:
            self.load_courses()

# ==================== 排课管理 ====================

class AdminScheduleFrame(BaseFrame):
    def create_widgets(self):
        ttk.Label(self, text="排课管理", font=self.title_font).pack(pady=10)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(toolbar, text="导入课表", command=self.import_schedule).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出课表", command=self.export_schedule).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清空课表", command=self.clear_schedule).pack(side=tk.LEFT, padx=2)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.day_frames = {}
        for day in ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=day)
            self.day_frames[day] = frame
            self.create_day_schedule(frame, day)

    def create_day_schedule(self, parent, day: str):
        time_slots = self.dm.data["settings"]["time_slots"].get(day, [])
        max_per_coach = self.dm.data["settings"].get("max_students_per_coach", 6)
        all_coaches = self.dm.data["settings"].get("coaches", ["王教练", "陈教练"])

        # 创建带滚动条的容器
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        schedules = self.dm.get_schedules()
        day_schedules = [s for s in schedules if s.get("week_day") == day]
        students = self.dm.data["students"]
        courses = self.dm.data["courses"]
        student_map = {s["id"]: s for s in students}
        course_map = {c["id"]: c for c in courses}

        for idx, time_slot in enumerate(time_slots):
            slot_schedules = [s for s in day_schedules if s.get("time_slot") == time_slot]

            # 按教练分组
            coach_students = {}
            for c in all_coaches:
                coach_students[c] = []
            for sched in slot_schedules:
                student = student_map.get(sched.get("student_id", ""), {})
                coach = sched.get("coach", "") or student.get("coach", "")
                if not coach:
                    coach = all_coaches[0] if all_coaches else "未分配"
                if coach not in coach_students:
                    coach_students[coach] = []
                coach_students[coach].append(student.get("name", "未知"))

            # 时间段行
            slot_frame = ttk.Frame(scrollable_frame)
            slot_frame.grid(row=idx*2+1, column=0, padx=5, pady=3, sticky="nsew")

            # 时间段标签
            ttk.Label(slot_frame, text=time_slot, font=self.header_font, width=14, anchor="center", relief=tk.RIDGE).pack(side=tk.LEFT, fill=tk.Y, padx=2)

            # 每个教练
            for coach in all_coaches:
                students_list = coach_students.get(coach, [])
                count = len(students_list)
                color = "green" if count < max_per_coach else ("orange" if count == max_per_coach else "red")

                coach_frame = ttk.Frame(slot_frame, relief=tk.RIDGE, borderwidth=1)
                coach_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

                ttk.Label(coach_frame, text=f"{coach} ({count}/{max_per_coach})", font=("Microsoft YaHei", 9, "bold"), foreground=color).pack(fill=tk.X)

                # 进度条
                progress = ttk.Progressbar(coach_frame, orient="horizontal", length=120, mode="determinate")
                progress["value"] = (count / max_per_coach) * 100
                progress.pack(fill=tk.X, padx=5, pady=2)

                if students_list:
                    for sn in students_list:
                        ttk.Label(coach_frame, text=f"  • {sn}", font=("Microsoft YaHei", 8), anchor="w").pack(fill=tk.X)
                else:
                    ttk.Label(coach_frame, text="  (空)", font=("Microsoft YaHei", 8), foreground="gray").pack(fill=tk.X)

            # 操作按钮
            btn_frame = ttk.Frame(scrollable_frame)
            btn_frame.grid(row=idx*2+2, column=0, padx=5, pady=1, sticky="nsew")
            ttk.Button(btn_frame, text=f"查看 {time_slot}", command=lambda d=day, ts=time_slot: self.view_slot(d, ts), width=18).pack(side=tk.LEFT, padx=3)
            ttk.Button(btn_frame, text=f"添加学员 {time_slot}", command=lambda d=day, ts=time_slot: self.add_to_slot(d, ts), width=18).pack(side=tk.LEFT, padx=3)

        scrollable_frame.columnconfigure(0, weight=1)

    def refresh_day_schedule(self, day: str):
        frame = self.day_frames.get(day)
        if not frame:
            return
        for widget in frame.winfo_children():
            widget.destroy()
        self.create_day_schedule(frame, day)

    def refresh_all_schedules(self):
        for day in ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]:
            self.refresh_day_schedule(day)

    def view_slot(self, day: str, time_slot: str):
        schedules = self.dm.get_schedules()
        slot_schedules = [s for s in schedules if s.get("week_day") == day and s.get("time_slot") == time_slot]
        if not slot_schedules:
            self.show_message("提示", f"{day} {time_slot} 暂无排课")
            return
        win = tk.Toplevel(self)
        win.title(f"{day} {time_slot} - 学员列表")
        win.geometry("600x400")
        tree = ttk.Treeview(win, columns=("学员", "教练", "课程", "状态"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        student_map = {s["id"]: s for s in self.dm.data["students"]}
        course_map = {c["id"]: c for c in self.dm.data["courses"]}
        for s in slot_schedules:
            student = student_map.get(s.get("student_id", ""), {})
            course = course_map.get(s.get("course_id", ""), {})
            tree.insert("", tk.END, values=(student.get("name", "未知"), s.get("coach", ""), course.get("name", ""), s.get("status", "")))
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def add_to_slot(self, day: str, time_slot: str):
        schedules = self.dm.get_schedules()
        slot_schedules = [s for s in schedules if s.get("week_day") == day and s.get("time_slot") == time_slot]
        max_per_coach = self.dm.data["settings"].get("max_students_per_coach", 6)
        student_ids_in_slot = [s.get("student_id") for s in slot_schedules]

        students = self.dm.get_students(status="active")
        available = [s for s in students if s["id"] not in student_ids_in_slot]
        if not available:
            self.show_message("提示", "没有可添加的学员")
            return

        win = tk.Toplevel(self)
        win.title(f"{day} {time_slot} - 添加学员")
        win.geometry("400x300")
        tree = ttk.Treeview(win, columns=("学员", "电话", "等级", "教练", "剩余课时"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=70)
        for s in available:
            tree.insert("", tk.END, values=(s.get("name", ""), s.get("phone", ""), s.get("level", ""), s.get("coach", ""), s.get("remaining_hours", 0)))
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def do_add():
            selected = tree.selection()
            if not selected:
                self.show_message("提示", "请先选择学员")
                return
            item = tree.item(selected[0])
            student_name = item["values"][0]
            student = self.dm.find_student_by_name(student_name)
            if not student:
                return
            course = self.dm.find_course_by_name("羽毛球课")
            if not course:
                course = Course(name="羽毛球课", level="初级", total_hours=50, price=3750)
                self.dm.add_course(course)
                course = self.dm.find_course_by_name("羽毛球课")
            sched = Schedule(student_id=student["id"], course_id=course["id"] if course else "", week_day=day, time_slot=time_slot, coach=student.get("coach", ""))
            self.dm.add_schedule(sched)
            win.destroy()
            self.refresh_all_schedules()
            self.show_message("成功", f"已将 {student_name} 添加到 {day} {time_slot}")

        ttk.Button(win, text="添加", command=do_add).pack(pady=10)

    def import_schedule(self):
        filepath = filedialog.askopenfilename(title="选择课表CSV文件", filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")])
        if filepath:
            service = ScheduleService(self.dm)
            imported, errors = service.import_from_csv(filepath)
            if errors and imported == 0:
                self.show_message("导入错误", f"错误:\n" + "\n".join(errors[:10]), True)
            elif errors:
                self.show_message("导入完成", f"成功导入{imported}条记录\n\n部分错误:\n" + "\n".join(errors[:5]))
            else:
                self.show_message("成功", f"成功导入{imported}条课表记录")
            self.refresh_all_schedules()

    def export_schedule(self):
        filepath = filedialog.asksaveasfilename(title="保存课表CSV", defaultextension=".csv", filetypes=[("CSV文件", "*.csv")])
        if filepath:
            service = ScheduleService(self.dm)
            count, error = service.export_to_csv(filepath)
            if error:
                self.show_message("导出错误", f"导出失败: {error}", True)
            else:
                self.show_message("成功", f"已导出{count}条课表记录")

    def clear_schedule(self):
        if messagebox.askyesno("确认", "确定要清空所有课表吗？"):
            self.dm.clear_schedules()
            self.refresh_all_schedules()
            self.show_message("成功", "已清空所有课表")

# ==================== 消课点名 ====================

class AdminAttendanceFrame(BaseFrame):
    def create_widgets(self):
        ttk.Label(self, text="消课点名", font=self.title_font).pack(pady=10)
        ctrl = ttk.Frame(self)
        ctrl.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(ctrl, text="日期:").pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(ctrl, textvariable=self.date_var, width=12).pack(side=tk.LEFT, padx=5)

        ttk.Label(ctrl, text="星期:").pack(side=tk.LEFT, padx=(15, 5))
        self.day_var = tk.StringVar(value="星期一")
        day_combo = ttk.Combobox(ctrl, textvariable=self.day_var, width=8, state="readonly",
                                  values=["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"])
        day_combo.pack(side=tk.LEFT, padx=5)
        day_combo.bind("<<ComboboxSelected>>", lambda e: self.load_time_slots())

        ttk.Label(ctrl, text="时间段:").pack(side=tk.LEFT, padx=(15, 5))
        self.slot_var = tk.StringVar()
        self.slot_combo = ttk.Combobox(ctrl, textvariable=self.slot_var, width=14, state="readonly")
        self.slot_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(ctrl, text="加载", command=self.load_students).pack(side=tk.LEFT, padx=10)
        ttk.Button(ctrl, text="消课", command=self.take_attendance).pack(side=tk.LEFT)

        self.load_time_slots()

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        columns = ("选择", "学员", "教练", "剩余课时", "状态")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_time_slots(self):
        day = self.day_var.get()
        slots = self.dm.data["settings"]["time_slots"].get(day, [])
        self.slot_combo["values"] = slots
        if slots:
            self.slot_combo.set(slots[0])

    def load_students(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        day = self.day_var.get()
        time_slot = self.slot_var.get()
        schedules = self.dm.get_schedules()
        matched = [s for s in schedules if s.get("week_day") == day and s.get("time_slot") == time_slot]
        student_map = {s["id"]: s for s in self.dm.data["students"]}
        for s in matched:
            student = student_map.get(s.get("student_id", ""), {})
            self.tree.insert("", tk.END, values=("", student.get("name", ""), s.get("coach", ""), student.get("remaining_hours", 0), "待消课"))

    def take_attendance(self):
        selected = self.tree.selection()
        if not selected:
            self.show_message("提示", "请先选择要消课的学员")
            return
        day = self.day_var.get()
        time_slot = self.slot_var.get()
        date = self.date_var.get()
        schedules = self.dm.get_schedules()
        matched = [s for s in schedules if s.get("week_day") == day and s.get("time_slot") == time_slot]
        if not matched:
            self.show_message("提示", "该时间段没有排课记录")
            return

        count = 0
        for item in selected:
            values = self.tree.item(item, "values")
            student_name = values[1]
            student = self.dm.find_student_by_name(student_name)
            if not student:
                continue
            for sched in matched:
                if sched.get("student_id") == student["id"]:
                    att = Attendance(student_id=student["id"], course_id=sched.get("course_id", ""), schedule_id=sched["id"], date=date, hours=1)
                    self.dm.add_attendance(att)
                    count += 1
                    break
        self.show_message("成功", f"已消课 {count} 名学员")
        self.load_students()

# ==================== 统计 ====================

class AdminStatsFrame(BaseFrame):
    def create_widgets(self):
        ttk.Label(self, text="统计中心", font=self.title_font).pack(pady=10)
        stats = self.dm.get_statistics()
        data = [("学员总数", stats["total_students"], "#4facfe"), ("活跃学员", stats["active_students"], "#00f2fe"),
                ("潜在学员", stats["potential_students"], "#ff6b6b"), ("课程总数", stats["total_courses"], "#4ecdc4"),
                ("总课时", stats["total_hours"], "#45b7d1"), ("剩余课时", stats["remaining_hours"], "#ffd166"),
                ("消课率", f"{stats['consumption_rate']}%", "#06d6a0")]
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=10, pady=10)
        for i, (label, value, color) in enumerate(data):
            card = ttk.Frame(frame, relief=tk.RAISED, borderwidth=2)
            card.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="nsew")
            ttk.Label(card, text=str(value), font=("Microsoft YaHei", 24, "bold"), foreground=color).pack(pady=(10, 5))
            ttk.Label(card, text=label, font=("Microsoft YaHei", 10)).pack(pady=(0, 10))
        for i in range(4):
            frame.columnconfigure(i, weight=1)

# ==================== 对话框 ====================

class AddStudentDialog(tk.Toplevel):
    def __init__(self, parent, dm: DataManager):
        super().__init__(parent)
        self.dm = dm
        self.result = False
        self.title("添加学员")
        self.geometry("400x550")
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="姓名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5, padx=(5, 0))
        ttk.Label(f, text="电话:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.phone_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.phone_var, width=30).grid(row=1, column=1, pady=5, padx=(5, 0))
        ttk.Label(f, text="出生日期:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.birth_var = tk.StringVar(value=f"{datetime.now().year - 10}-01-01")
        ttk.Entry(f, textvariable=self.birth_var, width=30).grid(row=2, column=1, pady=5, padx=(5, 0))
        ttk.Label(f, text="等级:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.level_var = tk.StringVar()
        lc = ttk.Combobox(f, textvariable=self.level_var, width=28, state="readonly", values=self.dm.data["settings"]["course_levels"])
        lc.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        if lc["values"]: lc.set(lc["values"][0])
        ttk.Label(f, text="教练:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.coach_var = tk.StringVar()
        cc = ttk.Combobox(f, textvariable=self.coach_var, width=28, state="readonly", values=self.dm.data["settings"]["coaches"])
        cc.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        if cc["values"]: cc.set(cc["values"][0])

        ttk.Label(f, text="购买课时:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.purchased_var = tk.StringVar(value="0")
        ttk.Entry(f, textvariable=self.purchased_var, width=30).grid(row=5, column=1, pady=5, padx=(5, 0))
        ttk.Label(f, text="赠送课时:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.bonus_var = tk.StringVar(value="0")
        ttk.Entry(f, textvariable=self.bonus_var, width=30).grid(row=6, column=1, pady=5, padx=(5, 0))
        ttk.Label(f, text="剩余课时:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.remaining_var = tk.StringVar(value="0")
        ttk.Entry(f, textvariable=self.remaining_var, width=30).grid(row=7, column=1, pady=5, padx=(5, 0))

        bf = ttk.Frame(f)
        bf.grid(row=8, column=0, columnspan=2, pady=20)
        ttk.Button(bf, text="保存", command=self.on_save, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="取消", command=self.destroy, width=15).pack(side=tk.LEFT, padx=5)

    def on_save(self):
        if not self.name_var.get().strip():
            messagebox.showerror("错误", "请输入姓名")
            return
        try:
            birth = datetime.strptime(self.birth_var.get(), "%Y-%m-%d").strftime("%Y-%m-%d")
        except:
            birth = f"{datetime.now().year - 10}-01-01"
        student = Student(name=self.name_var.get().strip(), phone=self.phone_var.get().strip(), birth_date=birth, level=self.level_var.get(), coach=self.coach_var.get())
        try:
            student.purchased_hours = int(self.purchased_var.get())
        except:
            student.purchased_hours = 0
        try:
            student.bonus_hours = int(self.bonus_var.get())
        except:
            student.bonus_hours = 0
        try:
            student.remaining_hours = int(self.remaining_var.get())
        except:
            student.remaining_hours = student.purchased_hours + student.bonus_hours
        self.dm.add_student(student)
        self.result = True
        self.destroy()

class AddCourseDialog(tk.Toplevel):
    def __init__(self, parent, dm: DataManager):
        super().__init__(parent)
        self.dm = dm
        self.result = False
        self.title("添加课程")
        self.geometry("400x400")
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="课程名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5, padx=(5, 0))
        ttk.Label(f, text="水平:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.level_var = tk.StringVar()
        lc = ttk.Combobox(f, textvariable=self.level_var, width=28, state="readonly", values=self.dm.data["settings"]["course_levels"])
        lc.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        if lc["values"]: lc.set(lc["values"][0])
        ttk.Label(f, text="总课时:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.hours_var = tk.StringVar(value="50")
        ttk.Entry(f, textvariable=self.hours_var, width=30).grid(row=2, column=1, pady=5, padx=(5, 0))
        ttk.Label(f, text="价格:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.price_var = tk.StringVar(value="3750")
        ttk.Entry(f, textvariable=self.price_var, width=30).grid(row=3, column=1, pady=5, padx=(5, 0))
        ttk.Label(f, text="教练:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.coach_var = tk.StringVar()
        cc = ttk.Combobox(f, textvariable=self.coach_var, width=28, state="readonly", values=self.dm.data["settings"]["coaches"])
        cc.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        if cc["values"]: cc.set(cc["values"][0])
        bf = ttk.Frame(f)
        bf.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(bf, text="保存", command=self.on_save, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="取消", command=self.destroy, width=15).pack(side=tk.LEFT, padx=5)

    def on_save(self):
        if not self.name_var.get().strip():
            messagebox.showerror("错误", "请输入课程名称")
            return
        try:
            hours = int(self.hours_var.get())
            price = float(self.price_var.get())
        except:
            messagebox.showerror("错误", "课时和价格必须是数字")
            return
        course = Course(name=self.name_var.get().strip(), level=self.level_var.get(), total_hours=hours, price=price)
        course.coach = self.coach_var.get()
        self.dm.add_course(course)
        self.result = True
        self.destroy()

# ==================== 主程序 ====================

class QingYuEduSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("青羽教务系统")
        self.root.geometry("1200x700")
        style = ttk.Style()
        style.theme_use("clam")
        self.dm = DataManager()
        self.current_role = "admin"
        self.create_main_ui()

    def create_main_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(toolbar, text="身份:").pack(side=tk.LEFT)
        self.role_var = tk.StringVar(value="管理员")
        rc = ttk.Combobox(toolbar, textvariable=self.role_var, width=15, state="readonly", values=["管理员", "学生"])
        rc.pack(side=tk.LEFT, padx=5)
        rc.bind("<<ComboboxSelected>>", lambda e: self.show_interface())
        ttk.Label(toolbar, text="青羽教务系统", font=("Microsoft YaHei", 9)).pack(side=tk.RIGHT)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.show_interface()

    def show_interface(self):
        for w in self.main_frame.winfo_children():
            w.destroy()
        if self.role_var.get() == "管理员":
            self.show_admin()
        else:
            ttk.Label(self.main_frame, text="学生端", font=("Microsoft YaHei", 16)).pack(expand=True)

    def show_admin(self):
        nb = ttk.Notebook(self.main_frame)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        nb.add(AdminStudentFrame(nb, self.dm, "admin"), text="学员管理")
        nb.add(AdminCourseFrame(nb, self.dm, "admin"), text="课程管理")
        nb.add(AdminScheduleFrame(nb, self.dm, "admin"), text="排课管理")
        nb.add(AdminAttendanceFrame(nb, self.dm, "admin"), text="消课点名")
        nb.add(AdminStatsFrame(nb, self.dm, "admin"), text="统计中心")

    def export_data(self):
        filepath = filedialog.asksaveasfilename(title="导出数据", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.dm.data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"已导出到: {filepath}")

    def show_about(self):
        messagebox.showinfo("关于", "青羽教务系统 v2.0")

    def run(self):
        self.root.mainloop()

def main():
    root = tk.Tk()
    app = QingYuEduSystem(root)
    app.run()

if __name__ == "__main__":
    main()
#2026.4.4修改
