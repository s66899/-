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

def _safe_float(val) -> float:
    try:
        v = str(val).replace('课时', '').strip()
        return float(v)
    except:
        return 0.0

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
    def __init__(self, data_file: Optional[str] = None):
        if data_file is None:
            data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "教务数据.json")
        self.data_file = data_file
        self.auto_save = True
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
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存失败: {e}")

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
        total_hours = 0
        remaining_hours = 0
        for s in self.data["students"]:
            total_hours += s.get("purchased_hours", 0) + s.get("bonus_hours", 0)
            remaining_hours += s.get("remaining_hours", 0)
        stats = {
            "total_students": len(self.data["students"]),
            "active_students": len([s for s in self.data["students"] if s.get("status") == "active"]),
            "potential_students": len([s for s in self.data["students"] if s.get("status") == "potential"]),
            "total_courses": len(self.data["courses"]),
            "total_hours": total_hours,
            "remaining_hours": remaining_hours,
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
            # Try GBK first (Excel default on Windows), then UTF-8 variants
            encodings = ['gbk', 'gb18030', 'utf-8-sig', 'utf-8', 'gb2312']
            content = None
            for enc in encodings:
                try:
                    with open(filepath, 'r', encoding=enc) as f:
                        content = f.read()
                    # Verify content has Chinese characters
                    if any('\u4e00' <= c <= '\u9fff' for c in content):
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
                nl = name.replace('*', '').lower().strip()
                if nl in ['姓名', 'name', '学生姓名']: col_map['name'] = name
                elif nl in ['电话', 'phone', '手机', 'mobile', '联系电话', '主要联系人:电话']: col_map['phone'] = name
                elif nl in ['出生日期', 'birthday', 'birth_date', '生日']: col_map['birth_date'] = name
                elif nl in ['年龄', 'age']: col_map['age'] = name
                elif nl in ['等级', 'level']: col_map['level'] = name
                elif nl in ['教练', 'teacher', 'coach']: col_map['coach'] = name
                elif nl in ['状态', 'status']: col_map['status'] = name
                elif nl in ['备注', 'note']: col_map['note'] = name
                elif '购买' in nl or '购课' in nl:
                    if 'purchased' not in col_map: col_map['purchased'] = name
                elif '赠送' in nl:
                    if 'bonus' not in col_map: col_map['bonus'] = name
                elif '剩余' in nl:
                    if 'remaining' not in col_map: col_map['remaining'] = name

            # Detect template format: sample first row to check if data aligns with headers
            use_positional = False
            sample_rows = list(reader)
            
            if sample_rows and len(fieldnames) >= 11:
                # Template format has headers shifted - data at positions doesn't match header names
                # Check if "购买课时" column (index 6 in template) has numeric data
                first_vals = list(sample_rows[0].values())
                # In template: position 5 = purchased (numeric), position 6 = bonus (numeric)
                # But headers map: "购买课时" -> position 6 (which is actually bonus in data)
                # If position 5 is numeric and position 6 is also numeric, it's the template format
                if len(first_vals) >= 7:
                    try:
                        float(first_vals[5])  # Position 5 should be numeric (purchased)
                        float(first_vals[6])  # Position 6 should be numeric (bonus)
                        # If both numeric and we have 12 columns, it's our template format
                        if len(fieldnames) == 12:
                            use_positional = True
                    except:
                        pass
                elif len(fieldnames) == 12:
                    # 12 columns with no mapped purchased = likely template format
                    use_positional = True

            # Collect students and merge duplicates from CSV
            student_data = {}  # name -> data
            order = []

            for row_num, row in enumerate(sample_rows, start=2):
                try:
                    if use_positional:
                        # Template format: parse by column position
                        # 0-姓名, 1-电话, 2-出生日期, 3-课程类型, 4-状态, 5-购买课时, 6-赠送课时, 7-(空), 8-剩余课时, 9-等级, 10-性别, 11-备注
                        raw_vals = list(row.values())
                        if len(raw_vals) < 10:
                            continue
                        name = str(raw_vals[0]).strip()
                        if not name:
                            continue
                        phone = str(raw_vals[1]).strip()
                        birth_str = str(raw_vals[2]).strip() if len(raw_vals) > 2 else ''
                        status_raw = str(raw_vals[4]).strip() if len(raw_vals) > 4 else ''
                        purchased = _safe_float(raw_vals[5]) if len(raw_vals) > 5 else 0
                        bonus = _safe_float(raw_vals[6]) if len(raw_vals) > 6 else 0
                        remaining = _safe_float(raw_vals[8]) if len(raw_vals) > 8 else 0
                        level = str(raw_vals[9]).strip() if len(raw_vals) > 9 else '初级'
                        note = str(raw_vals[10]).strip() if len(raw_vals) > 10 else ''
                        birth_date = self.parse_date(birth_str) if birth_str else f"{datetime.now().year - 10}-01-01"
                        coach = ''
                        if status_raw in ['在读', 'active']:
                            status = 'active'
                        elif status_raw in ['已结', 'inactive', '停课']:
                            status = 'inactive'
                        else:
                            status = 'active'
                    else:
                        # Standard format: use column name mapping
                        name = row.get(col_map.get('name', ''), '').strip()
                        if not name:
                            continue
                        phone = row.get(col_map.get('phone', ''), '').strip()
                        if ':' in phone:
                            phone = phone.split(':', 1)[1].strip()
                        birth_str = row.get(col_map.get('birth_date', ''), '').strip()
                        age_str = row.get(col_map.get('age', ''), '').strip()
                        birth_date = self.parse_date(birth_str) if birth_str else self.parse_date(age_str) if age_str else f"{datetime.now().year - 10}-01-01"
                        level = row.get(col_map.get('level', ''), '').strip() or '初级'
                        coach = row.get(col_map.get('coach', ''), '').strip() or ''
                        note = row.get(col_map.get('note', ''), '').strip()

                        def parse_hours(val):
                            if not val: return 0
                            val = val.replace('课时', '').strip()
                            try: return float(val)
                            except: return 0

                        purchased = parse_hours(row.get(col_map.get('purchased', ''), ''))
                        bonus = parse_hours(row.get(col_map.get('bonus', ''), ''))
                        remaining = parse_hours(row.get(col_map.get('remaining', ''), ''))

                        status = row.get(col_map.get('status', ''), '').strip()
                        if status in ['在读', 'active']: status = 'active'
                        elif status in ['已结', 'inactive']: status = 'inactive'
                        else: status = 'active'

                    if name in student_data:
                        # Merge: sum hours for duplicate names in CSV
                        student_data[name]['purchased_hours'] += purchased
                        student_data[name]['bonus_hours'] += bonus
                        student_data[name]['remaining_hours'] += remaining
                    else:
                        student_data[name] = {
                            'name': name, 'phone': phone, 'birth_date': birth_date,
                            'level': level, 'coach': coach, 'note': note, 'status': status,
                            'purchased_hours': purchased, 'bonus_hours': bonus, 'remaining_hours': remaining
                        }
                        order.append(name)
                except Exception as e:
                    errors.append(f"第{row_num}行: {str(e)}")

            # Add or update students in database
            for name in order:
                sd = student_data[name]
                existing = self.dm.find_student_by_name(sd['name'])
                if existing:
                    # Update existing student
                    updates = {
                        'phone': sd['phone'] or existing.get('phone', ''),
                        'birth_date': sd['birth_date'] or existing.get('birth_date', ''),
                        'level': sd['level'] or existing.get('level', ''),
                        'coach': sd['coach'] or existing.get('coach', ''),
                        'status': sd['status'] or existing.get('status', ''),
                        'note': sd['note'] or existing.get('note', ''),
                        'purchased_hours': int(sd['purchased_hours']) + existing.get('purchased_hours', 0),
                        'bonus_hours': int(sd['bonus_hours']) + existing.get('bonus_hours', 0),
                        'remaining_hours': int(sd['remaining_hours']) + existing.get('remaining_hours', 0),
                    }
                    self.dm.update_student(existing['id'], updates)
                else:
                    # Add new student
                    student = Student(name=sd['name'], phone=sd['phone'], birth_date=sd['birth_date'], level=sd['level'], coach=sd['coach'])
                    student.purchased_hours = int(sd['purchased_hours'])
                    student.bonus_hours = int(sd['bonus_hours'])
                    student.remaining_hours = int(sd['remaining_hours'])
                    student.status = sd['status']
                    student.note = sd['note']
                    self.dm.add_student(student)
                imported += 1
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

                # Extract coach from cell content (e.g., "学生A，学生B（王教练）")
                coach_match = re.search(r'[（(]([^）)]*教练)[）)]', cell_content)
                cell_coach = coach_match.group(1) if coach_match else ""

                for sn in student_names:
                    clean_name = re.sub(r'[~（）()~].*$', '', sn).strip()
                    if not clean_name:
                        continue
                    student = self.dm.find_student_by_name(clean_name)
                    if not student:
                        student = Student(name=clean_name, phone='', birth_date=f"{datetime.now().year - 10}-01-01", level='初级', coach=cell_coach)
                        self.dm.add_student(student)
                        student = self.dm.find_student_by_name(clean_name)
                    course = self.dm.find_course_by_name("羽毛球课")
                    if not course:
                        course = Course(name="羽毛球课", level="初级", total_hours=50, price=3750)
                        self.dm.add_course(course)
                        course = self.dm.find_course_by_name("羽毛球课")
                    exists = any(s.get("student_id") == student["id"] and s.get("week_day") == week_day and s.get("time_slot") == time_slot for s in self.dm.data["schedules"])
                    if not exists:
                        sched = Schedule(student_id=student["id"], course_id=course["id"] if course else "", week_day=week_day, time_slot=time_slot, coach=cell_coach)
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
                student_name, course_name, week_day, time_slot, coach = '', '', '', '', ''
                for header in headers:
                    value = row[header].strip()
                    if not value:
                        continue
                    if '姓名' in header:
                        if not student_name: student_name = value
                    if '课程' in header:
                        if not course_name: course_name = value
                    if '教练' in header:
                        if not coach: coach = value
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
                    student = Student(name=student_name, phone='', birth_date=f"{datetime.now().year - 10}-01-01", level='初级', coach=coach)
                    self.dm.add_student(student)
                    student = self.dm.find_student_by_name(student_name)
                course = self.dm.find_course_by_name(course_name or "羽毛球课")
                if not course:
                    course = Course(name=course_name or "羽毛球课", level="初级", total_hours=50, price=3750)
                    self.dm.add_course(course)
                    course = self.dm.find_course_by_name(course_name or "羽毛球课")
                exists = any(s.get("student_id") == student["id"] and s.get("week_day") == week_day and s.get("time_slot") == time_slot for s in self.dm.data["schedules"])
                if not exists:
                    sched = Schedule(student_id=student["id"], course_id=course["id"] if course else "", week_day=week_day, time_slot=time_slot, coach=coach)
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
            ids_to_delete = []
            for item in selected:
                values = self.tree.item(item, "values")
                name = values[1] if values else ""
                student = self.dm.find_student_by_name(name)
                if student:
                    ids_to_delete.append(student["id"])
            if ids_to_delete:
                self.dm.delete_students(ids_to_delete)
            self.show_message("提示", f"已删除{len(ids_to_delete)}名学员")
            self.load_students()

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

# ==================== 课程包定义 ====================

COURSE_PACKAGES = [
    {"id": "1v1", "name": "1v1私教课", "type": "per_hour", "price_per_hour": 220, "description": "1对1教学，220元/节"},
    {"id": "1v2", "name": "1v2小班课", "type": "per_hour", "price_per_hour": 120, "description": "1对2教学，120元/节"},
    {"id": "pkg_50", "name": "50节课包", "type": "package", "hours": 50, "price": 3999, "description": "50节课，3999元"},
    {"id": "pkg_30", "name": "30节课包", "type": "package", "hours": 30, "price": 2699, "description": "30节课，2699元"},
    {"id": "pkg_15", "name": "15节课包", "type": "package", "hours": 15, "price": 1499, "description": "15节课，1499元"},
    {"id": "monthly", "name": "月卡", "type": "package", "hours": 7, "price": 569, "description": "月卡7节课，569元"},
]

# ==================== 课程管理 ====================

class AdminCourseFrame(BaseFrame):
    def create_widgets(self):
        ttk.Label(self, text="报课管理", font=self.title_font).pack(pady=10)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(toolbar, text="学员报课", command=self.enroll_student).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="查看报课记录", command=self.view_enrollments).pack(side=tk.LEFT, padx=2)

        ttk.Label(self, text="课程包列表", font=self.header_font).pack(pady=(10, 5))

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        columns = ("课程包名称", "类型", "课时/节", "单价", "总价", "描述")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        col_widths = [120, 80, 80, 80, 80, 200]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_packages()

    def load_packages(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for pkg in COURSE_PACKAGES:
            if pkg["type"] == "per_hour":
                hours = "自选"
                unit = f"¥{pkg['price_per_hour']}/节"
                total = "按节数计算"
            else:
                hours = str(pkg["hours"])
                unit = f"¥{round(pkg['price']/pkg['hours'], 1)}/节"
                total = f"¥{pkg['price']}"
            self.tree.insert("", tk.END, values=(
                pkg["name"],
                "按节计费" if pkg["type"] == "per_hour" else "课包",
                hours, unit, total, pkg["description"]
            ))

    def enroll_student(self):
        dialog = EnrollDialog(self, self.dm)
        self.wait_window(dialog)
        if dialog.result:
            self.load_packages()

    def view_enrollments(self):
        win = tk.Toplevel(self)
        win.title("报课记录")
        win.geometry("800x500")
        tree = ttk.Treeview(win, columns=("学员", "课程包", "购买课时", "总价", "日期"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=140)
        enrollments = self.dm.data.get("enrollments", [])
        for e in enrollments:
            tree.insert("", tk.END, values=(
                e.get("student_name", ""),
                e.get("package_name", ""),
                e.get("hours", 0),
                f"¥{e.get('price', 0)}",
                e.get("date", "")
            ))
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=10)

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

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

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

    def highlight_students(self, search_text: str):
        pass

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
        win.geometry("700x450")
        tree = ttk.Treeview(win, columns=("学员", "教练", "课程", "剩余课时", "状态"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        student_map = {s["id"]: s for s in self.dm.data["students"]}
        course_map = {c["id"]: c for c in self.dm.data["courses"]}
        for s in slot_schedules:
            student = student_map.get(s.get("student_id", ""), {})
            course = course_map.get(s.get("course_id", ""), {})
            coach = s.get("coach", "") or student.get("coach", "") or "未分配"
            tree.insert("", tk.END, values=(student.get("name", "未知"), coach, course.get("name", ""), student.get("remaining_hours", 0), s.get("status", "")))
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
        self.stats_frame = ttk.Frame(self)
        self.stats_frame.pack(fill=tk.X, padx=10, pady=10)
        self.refresh_stats()

    def refresh_stats(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        stats = self.dm.get_statistics()
        data = [("学员总数", stats["total_students"], "#4facfe"), ("活跃学员", stats["active_students"], "#00f2fe"),
                ("潜在学员", stats["potential_students"], "#ff6b6b"), ("课程总数", stats["total_courses"], "#4ecdc4"),
                ("总课时", stats["total_hours"], "#45b7d1"), ("剩余课时", stats["remaining_hours"], "#ffd166"),
                ("消课率", f"{stats['consumption_rate']}%", "#06d6a0")]
        for i, (label, value, color) in enumerate(data):
            card = ttk.Frame(self.stats_frame, relief=tk.RAISED, borderwidth=2)
            card.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="nsew")
            ttk.Label(card, text=str(value), font=("Microsoft YaHei", 24, "bold"), foreground=color).pack(pady=(10, 5))
            ttk.Label(card, text=label, font=("Microsoft YaHei", 10)).pack(pady=(0, 10))
        for i in range(4):
            self.stats_frame.columnconfigure(i, weight=1)

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

class EnrollDialog(tk.Toplevel):
    def __init__(self, parent, dm: DataManager):
        super().__init__(parent)
        self.dm = dm
        self.result = False
        self.title("学员报课")
        self.geometry("500x550")
        self.resizable(False, False)
        self.selected_pkg = None
        self.hours_var = tk.StringVar(value="10")
        self.create_widgets()

    def create_widgets(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="选择学员:", font=("Microsoft YaHei", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.student_var = tk.StringVar()
        students = self.dm.get_students(status="active")
        self.student_combo = ttk.Combobox(f, textvariable=self.student_var, width=28, state="readonly",
                                          values=[s["name"] for s in students])
        self.student_combo.grid(row=0, column=1, pady=5, padx=(5, 0))

        ttk.Label(f, text="选择课程包:", font=("Microsoft YaHei", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=(15, 5))

        self.pkg_var = tk.StringVar()
        pkg_values = []
        for pkg in COURSE_PACKAGES:
            if pkg["type"] == "per_hour":
                label = f"{pkg['name']} - ¥{pkg['price_per_hour']}/节"
            else:
                label = f"{pkg['name']} - ¥{pkg['price']}({pkg['hours']}节)"
            pkg_values.append(label)
        self.pkg_combo = ttk.Combobox(f, textvariable=self.pkg_var, width=35, state="readonly", values=pkg_values)
        self.pkg_combo.grid(row=1, column=0, columnspan=2, pady=5, padx=(0, 0))
        self.pkg_combo.bind("<<ComboboxSelected>>", self.on_pkg_selected)

        self.info_frame = ttk.Frame(f)
        self.info_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="nsew")

        self.hours_frame = ttk.Frame(f)
        self.hours_frame.grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Label(self.hours_frame, text="购买节数:").pack(side=tk.LEFT, padx=5)
        self.hours_entry = ttk.Entry(self.hours_frame, textvariable=self.hours_var, width=8)
        self.hours_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(self.hours_frame, text="节").pack(side=tk.LEFT)
        self.hours_frame.pack_forget()

        self.price_label = ttk.Label(f, text="", font=("Microsoft YaHei", 12, "bold"), foreground="#4facfe")
        self.price_label.grid(row=4, column=0, columnspan=2, pady=15)

        bf = ttk.Frame(f)
        bf.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(bf, text="确认报课", command=self.on_enroll, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="取消", command=self.destroy, width=15).pack(side=tk.LEFT, padx=5)

    def on_pkg_selected(self, event=None):
        idx = self.pkg_combo.current()
        if idx < 0:
            return
        self.selected_pkg = COURSE_PACKAGES[idx]
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        pkg = self.selected_pkg
        if pkg["type"] == "per_hour":
            self.hours_frame.pack(fill=tk.X, padx=20)
            self.hours_entry.focus()
            total = int(self.hours_var.get()) * pkg["price_per_hour"]
            self.price_label.config(text=f"总价: ¥{total}")
        else:
            self.hours_frame.pack_forget()
            self.price_label.config(text=f"{pkg['description']}")

    def on_enroll(self):
        student_name = self.student_var.get().strip()
        if not student_name:
            messagebox.showerror("错误", "请选择学员")
            return
        if not self.selected_pkg:
            messagebox.showerror("错误", "请选择课程包")
            return

        student = self.dm.find_student_by_name(student_name)
        if not student:
            messagebox.showerror("错误", "学员不存在")
            return

        pkg = self.selected_pkg
        if pkg["type"] == "per_hour":
            try:
                hours = int(self.hours_var.get())
                if hours <= 0:
                    raise ValueError
            except:
                messagebox.showerror("错误", "请输入有效节数")
                return
            price = hours * pkg["price_per_hour"]
            total_hours = hours
        else:
            hours = pkg["hours"]
            price = pkg["price"]
            total_hours = hours

        student["purchased_hours"] = student.get("purchased_hours", 0) + total_hours
        student["remaining_hours"] = student.get("remaining_hours", 0) + total_hours
        self.dm.save_data()

        if "enrollments" not in self.dm.data:
            self.dm.data["enrollments"] = []
        self.dm.data["enrollments"].append({
            "student_id": student["id"],
            "student_name": student_name,
            "package_id": pkg["id"],
            "package_name": pkg["name"],
            "hours": total_hours,
            "price": price,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        self.dm.save_data()
        messagebox.showinfo("成功", f"{student_name} 报课成功\n课程包: {pkg['name']}\n课时: {total_hours}节\n总价: ¥{price}")
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

# ==================== 全局搜索对话框 ====================

class GlobalSearchDialog:
    def __init__(self, parent, dm: DataManager):
        self.parent = parent
        self.dm = dm
        self.win = None

    def show(self):
        self.win = tk.Toplevel(self.parent)
        self.win.title("全局搜索学员")
        self.win.geometry("900x600")
        self.win.transient(self.parent)

        ttk.Label(self.win, text="输入学员姓名、电话、备注进行搜索", font=("Microsoft YaHei", 10)).pack(pady=10)

        search_frame = ttk.Frame(self.win)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.do_search)
        ttk.Entry(search_frame, textvariable=self.search_var, width=40, font=("Microsoft YaHei", 11)).pack(side=tk.LEFT, padx=5)
        self.search_var_entry = search_frame.winfo_children()[0]
        self.search_var_entry.focus()

        columns = ("姓名", "电话", "年龄", "等级", "教练", "购买课时", "赠送课时", "剩余课时", "状态", "备注", "注册日期")
        list_frame = ttk.Frame(self.win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=18)
        col_widths = [80, 100, 50, 60, 70, 70, 70, 70, 60, 120, 90]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.view_student_detail)
        self.tree.bind("<Return>", self.view_student_detail)

        ttk.Button(self.win, text="关闭", command=self.win.destroy).pack(pady=10)

        self.do_search()

    def do_search(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)
        text = self.search_var.get().strip().lower()
        students = self.dm.get_students()
        if text:
            students = [s for s in students if
                        text in s.get("name", "").lower() or
                        text in s.get("phone", "").lower() or
                        text in s.get("note", "").lower() or
                        text in s.get("level", "").lower() or
                        text in s.get("coach", "").lower()]
        for s in students:
            self.tree.insert("", tk.END, values=(
                s.get("name", ""), s.get("phone", ""), s.get("age", 0),
                s.get("level", ""), s.get("coach", ""),
                s.get("purchased_hours", 0), s.get("bonus_hours", 0),
                s.get("remaining_hours", 0), s.get("status", ""),
                s.get("note", ""), s.get("register_date", "")
            ))

    def view_student_detail(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        name = item["values"][0]
        student = self.dm.find_student_by_name(name)
        if not student:
            return
        win = tk.Toplevel(self.win)
        win.title(f"学员详情 - {name}")
        win.geometry("500x450")
        f = ttk.Frame(win, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        fields = [
            ("姓名", student.get("name", "")),
            ("电话", student.get("phone", "")),
            ("出生日期", student.get("birth_date", "")),
            ("年龄", student.get("age", 0)),
            ("等级", student.get("level", "")),
            ("教练", student.get("coach", "")),
            ("状态", "在读" if student.get("status") == "active" else "已结"),
            ("购买课时", student.get("purchased_hours", 0)),
            ("赠送课时", student.get("bonus_hours", 0)),
            ("剩余课时", student.get("remaining_hours", 0)),
            ("注册日期", student.get("register_date", "")),
            ("备注", student.get("note", "")),
        ]
        for i, (label, value) in enumerate(fields):
            ttk.Label(f, text=label, font=("Microsoft YaHei", 10, "bold")).grid(row=i, column=0, sticky=tk.W, pady=3, padx=5)
            ttk.Label(f, text=str(value), font=("Microsoft YaHei", 10)).grid(row=i, column=1, sticky=tk.W, pady=3, padx=5)

        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=10)


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
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.dm.save_data()
        self.root.destroy()

    def open_global_search(self):
        dialog = GlobalSearchDialog(self, self.dm)
        dialog.show()

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

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(toolbar, text="🔍 全局搜索学员", command=self.open_global_search).pack(side=tk.LEFT, padx=5)

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
        self.student_frame = AdminStudentFrame(nb, self.dm, "admin")
        self.course_frame = AdminCourseFrame(nb, self.dm, "admin")
        self.schedule_frame = AdminScheduleFrame(nb, self.dm, "admin")
        self.attendance_frame = AdminAttendanceFrame(nb, self.dm, "admin")
        self.stats_frame = AdminStatsFrame(nb, self.dm, "admin")
        nb.add(self.student_frame, text="学员管理")
        nb.add(self.course_frame, text="报课管理")
        nb.add(self.schedule_frame, text="排课管理")
        nb.add(self.attendance_frame, text="消课点名")
        nb.add(self.stats_frame, text="统计中心")
        nb.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        nb = event.widget
        tab_text = nb.tab(nb.select(), "text")
        if tab_text == "统计中心":
            self.stats_frame.refresh_stats()

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
