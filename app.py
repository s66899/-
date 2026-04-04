#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青羽教务系统 - Web版本
Flask后端API + 前端页面
"""

from flask import Flask, request, jsonify, render_template
import json
import os
import csv
import io
import uuid
from datetime import datetime
from typing import List, Dict, Optional

app = Flask(__name__)

# ==================== 配置 ====================

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "教务数据.json")

COURSE_PACKAGES = [
    {"id": "1v1", "name": "1v1私教课", "type": "per_hour", "price_per_hour": 220, "description": "1对1教学，220元/节"},
    {"id": "1v2", "name": "1v2小班课", "type": "per_hour", "price_per_hour": 120, "description": "1对2教学，120元/节"},
    {"id": "pkg_50", "name": "50节课包", "type": "package", "hours": 50, "price": 3999, "description": "50节课，3999元"},
    {"id": "pkg_30", "name": "30节课包", "type": "package", "hours": 30, "price": 2699, "description": "30节课，2699元"},
    {"id": "pkg_15", "name": "15节课包", "type": "package", "hours": 15, "price": 1499, "description": "15节课，1499元"},
    {"id": "monthly", "name": "月卡", "type": "package", "hours": 7, "price": 569, "description": "月卡7节课，569元"},
]

# ==================== 数据管理 ====================

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return create_default_data()
    return create_default_data()

def create_default_data() -> dict:
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

def save_data(data: dict):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def gen_id() -> str:
    return str(uuid.uuid4())[:8]

# 全局数据
data = load_data()

# ==================== 页面路由 ====================

@app.route('/')
def index():
    return render_template('index.html')

# ==================== API: 学员 ====================

@app.route('/api/students', methods=['GET'])
def get_students():
    status = request.args.get('status')
    search = request.args.get('search', '').lower()
    students = data["students"]
    if status:
        students = [s for s in students if s.get("status") == status]
    if search:
        students = [s for s in students if
                    search in s.get("name", "").lower() or
                    search in s.get("phone", "").lower() or
                    search in s.get("note", "").lower() or
                    search in s.get("level", "").lower() or
                    search in s.get("coach", "").lower()]
    return jsonify(students)

@app.route('/api/students', methods=['POST'])
def add_student():
    s = request.json
    student = {
        "id": gen_id(),
        "name": s.get("name", ""),
        "phone": s.get("phone", ""),
        "birth_date": s.get("birth_date", ""),
        "level": s.get("level", "初级"),
        "coach": s.get("coach", ""),
        "status": s.get("status", "active"),
        "note": s.get("note", ""),
        "purchased_hours": float(s.get("purchased_hours", 0)),
        "bonus_hours": float(s.get("bonus_hours", 0)),
        "remaining_hours": float(s.get("remaining_hours", 0)),
        "register_date": datetime.now().strftime("%Y-%m-%d")
    }
    data["students"].append(student)
    save_data(data)
    return jsonify(student), 201

@app.route('/api/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    updates = request.json
    for i, s in enumerate(data["students"]):
        if s["id"] == student_id:
            data["students"][i].update(updates)
            save_data(data)
            return jsonify(data["students"][i])
    return jsonify({"error": "学员不存在"}), 404

@app.route('/api/students/batch', methods=['DELETE'])
def delete_students():
    ids = request.json.get("ids", [])
    data["students"] = [s for s in data["students"] if s["id"] not in ids]
    save_data(data)
    return jsonify({"deleted": len(ids)})

@app.route('/api/students/import-csv', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        return jsonify({"error": "无文件"}), 400
    file = request.files['file']
    content = file.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(content))
    fieldnames = reader.fieldnames or []
    col_map = {}
    for name in fieldnames:
        nl = name.replace('*', '').lower().strip()
        if nl in ['姓名', 'name', '学生姓名']: col_map['name'] = name
        elif nl in ['电话', 'phone', '手机', 'mobile', '联系电话']: col_map['phone'] = name
        elif nl in ['出生日期', 'birthday', 'birth_date', '生日']: col_map['birth_date'] = name
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

    use_positional = False
    sample_rows = list(reader)
    if sample_rows and len(fieldnames) >= 11:
        first_vals = list(sample_rows[0].values())
        if len(first_vals) >= 7:
            try:
                float(first_vals[5])
                float(first_vals[6])
                if len(fieldnames) == 12:
                    use_positional = True
            except:
                pass

    imported = 0
    for row in sample_rows:
        if use_positional:
            raw_vals = list(row.values())
            if len(raw_vals) < 10:
                continue
            name = str(raw_vals[0]).strip()
            if not name:
                continue
            phone = str(raw_vals[1]).strip()
            level = str(raw_vals[9]).strip() if len(raw_vals) > 9 else '初级'
            coach = ''
            status = 'active'
            def _sf(v):
                try: return float(str(v).replace('课时','').strip())
                except: return 0.0
            purchased = _sf(raw_vals[5]) if len(raw_vals) > 5 else 0
            bonus = _sf(raw_vals[6]) if len(raw_vals) > 6 else 0
            remaining = _sf(raw_vals[8]) if len(raw_vals) > 8 else 0
        else:
            name = row.get(col_map.get('name', ''), '').strip()
            if not name:
                continue
            phone = row.get(col_map.get('phone', ''), '').strip()
            level = row.get(col_map.get('level', ''), '').strip() or '初级'
            coach = row.get(col_map.get('coach', ''), '').strip() or ''
            status_raw = row.get(col_map.get('status', ''), '').strip()
            status = 'active' if status_raw in ['在读', 'active'] else 'inactive'
            def _ph(v):
                if not v: return 0
                v = v.replace('课时', '').strip()
                try: return float(v)
                except: return 0
            purchased = _ph(row.get(col_map.get('purchased', ''), ''))
            bonus = _ph(row.get(col_map.get('bonus', ''), ''))
            remaining = _ph(row.get(col_map.get('remaining', ''), ''))

        existing = None
        for s in data["students"]:
            if s.get("name") == name:
                existing = s
                break
        if existing:
            existing["purchased_hours"] = existing.get("purchased_hours", 0) + purchased
            existing["bonus_hours"] = existing.get("bonus_hours", 0) + bonus
            existing["remaining_hours"] = existing.get("remaining_hours", 0) + remaining
            if phone: existing["phone"] = phone
            if level: existing["level"] = level
            if coach: existing["coach"] = coach
        else:
            data["students"].append({
                "id": gen_id(), "name": name, "phone": phone,
                "birth_date": f"{datetime.now().year - 10}-01-01",
                "level": level, "coach": coach, "status": status,
                "note": "", "purchased_hours": purchased,
                "bonus_hours": bonus, "remaining_hours": remaining,
                "register_date": datetime.now().strftime("%Y-%m-%d")
            })
        imported += 1
    save_data(data)
    return jsonify({"imported": imported})

# ==================== API: 报课 ====================

@app.route('/api/packages', methods=['GET'])
def get_packages():
    return jsonify(COURSE_PACKAGES)

@app.route('/api/enroll', methods=['POST'])
def enroll():
    req = request.json
    student_id = req.get("student_id")
    package_id = req.get("package_id")
    hours = req.get("hours", 0)

    pkg = None
    for p in COURSE_PACKAGES:
        if p["id"] == package_id:
            pkg = p
            break
    if not pkg:
        return jsonify({"error": "课程包不存在"}), 404

    student = None
    for s in data["students"]:
        if s["id"] == student_id:
            student = s
            break
    if not student:
        return jsonify({"error": "学员不存在"}), 404

    if pkg["type"] == "per_hour":
        if hours <= 0:
            return jsonify({"error": "请输入有效节数"}), 400
        price = hours * pkg["price_per_hour"]
        total_hours = hours
    else:
        total_hours = pkg["hours"]
        price = pkg["price"]

    student["purchased_hours"] = student.get("purchased_hours", 0) + total_hours
    student["remaining_hours"] = student.get("remaining_hours", 0) + total_hours

    if "enrollments" not in data:
        data["enrollments"] = []
    data["enrollments"].append({
        "student_id": student_id,
        "student_name": student["name"],
        "package_id": package_id,
        "package_name": pkg["name"],
        "hours": total_hours,
        "price": price,
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    save_data(data)
    return jsonify({"success": True, "hours": total_hours, "price": price})

@app.route('/api/enrollments', methods=['GET'])
def get_enrollments():
    return jsonify(data.get("enrollments", []))

# ==================== API: 排课 ====================

@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    day = request.args.get('day')
    if day:
        return jsonify([s for s in data["schedules"] if s.get("week_day") == day])
    return jsonify(data["schedules"])

@app.route('/api/schedules', methods=['POST'])
def add_schedule():
    s = request.json
    schedule = {
        "id": gen_id(),
        "student_id": s.get("student_id", ""),
        "week_day": s.get("week_day", ""),
        "time_slot": s.get("time_slot", ""),
        "coach": s.get("coach", ""),
        "course_id": s.get("course_id", "")
    }
    data["schedules"].append(schedule)
    save_data(data)
    return jsonify(schedule), 201

@app.route('/api/schedules/import', methods=['POST'])
def import_schedule():
    if 'file' not in request.files:
        return jsonify({"error": "无文件"}), 400
    file = request.files['file']
    content = file.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(content))
    imported = 0
    for row in reader:
        name = row.get('姓名', '').strip()
        day = row.get('星期', '').strip()
        slot = row.get('时间段', '').strip()
        coach = row.get('教练', '').strip()
        if not name or not day or not slot:
            continue
        student = None
        for s in data["students"]:
            if s.get("name") == name:
                student = s
                break
        if not student:
            student = {
                "id": gen_id(), "name": name, "phone": "",
                "birth_date": f"{datetime.now().year - 10}-01-01",
                "level": "初级", "coach": coach, "status": "active",
                "note": "", "purchased_hours": 0, "bonus_hours": 0,
                "remaining_hours": 0, "register_date": datetime.now().strftime("%Y-%m-%d")
            }
            data["students"].append(student)
        exists = any(
            s.get("student_id") == student["id"] and
            s.get("week_day") == day and
            s.get("time_slot") == slot
            for s in data["schedules"]
        )
        if not exists:
            data["schedules"].append({
                "id": gen_id(), "student_id": student["id"],
                "week_day": day, "time_slot": slot, "coach": coach, "course_id": ""
            })
            imported += 1
    save_data(data)
    return jsonify({"imported": imported})

@app.route('/api/schedules/clear', methods=['POST'])
def clear_schedules():
    data["schedules"] = []
    save_data(data)
    return jsonify({"success": True})

@app.route('/api/schedules/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    data["schedules"] = [s for s in data["schedules"] if s["id"] != schedule_id]
    save_data(data)
    return jsonify({"success": True})

# ==================== API: 消课 ====================

@app.route('/api/attendance', methods=['POST'])
def add_attendance():
    req = request.json
    student_id = req.get("student_id")
    hours_used = float(req.get("hours_used", 1))
    date = req.get("date", datetime.now().strftime("%Y-%m-%d"))

    for s in data["students"]:
        if s["id"] == student_id:
            s["remaining_hours"] = max(0, s.get("remaining_hours", 0) - hours_used)
            break

    attendance = {
        "id": gen_id(), "student_id": student_id,
        "date": date, "hours_used": hours_used, "status": "completed"
    }
    data["attendances"].append(attendance)
    save_data(data)
    return jsonify(attendance), 201

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    return jsonify(data.get("attendances", []))

# ==================== API: 统计 ====================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_hours = 0
    remaining_hours = 0
    for s in data["students"]:
        total_hours += s.get("purchased_hours", 0) + s.get("bonus_hours", 0)
        remaining_hours += s.get("remaining_hours", 0)
    stats = {
        "total_students": len(data["students"]),
        "active_students": len([s for s in data["students"] if s.get("status") == "active"]),
        "potential_students": len([s for s in data["students"] if s.get("status") == "potential"]),
        "total_courses": len(data["courses"]),
        "total_hours": total_hours,
        "remaining_hours": remaining_hours,
        "consumption_rate": round((total_hours - remaining_hours) / total_hours * 100, 2) if total_hours > 0 else 0
    }
    return jsonify(stats)

# ==================== API: 设置 ====================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(data.get("settings", {}))

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    data["settings"].update(request.json)
    save_data(data)
    return jsonify(data["settings"])

# ==================== 启动 ====================

if __name__ == '__main__':
    print("青羽教务系统 Web版")
    print("访问地址: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
