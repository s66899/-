#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青羽教务系统 - 备份主程序（重构版）
功能与main.py相同，用于紧急恢复
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

class QingYuEduBackup:
    """青羽教务系统备份版本"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("青羽教务系统 - 备份版")
        self.root.geometry("800x500")
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面"""
        # 标题
        title_label = ttk.Label(self.root, text="青羽教务系统 - 备份恢复", 
                               font=("Microsoft YaHei", 20, "bold"))
        title_label.pack(pady=30)
        
        # 说明
        info_text = """这是青羽教务系统的备份版本。
        
如果您的主程序无法运行，可以使用此备份版本。
此版本包含基本的数据查看和导出功能。

主要功能:
1. 查看现有数据
2. 导出数据备份
3. 恢复数据文件
4. 系统状态检查

注意: 备份版本功能有限，建议尽快修复主程序。"""
        
        info_label = ttk.Label(self.root, text=info_text, font=("Microsoft YaHei", 10),
                              justify=tk.LEFT)
        info_label.pack(pady=20, padx=50)
        
        # 按钮框架
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=30)
        
        # 功能按钮
        buttons = [
            ("检查数据文件", self.check_data_file),
            ("导出数据备份", self.export_backup),
            ("查看系统信息", self.show_system_info),
            ("打开主程序", self.open_main_program)
        ]
        
        for text, command in buttons:
            btn = ttk.Button(button_frame, text=text, command=command, width=20)
            btn.pack(pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(self.root, textvariable=self.status_var, 
                                relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def check_data_file(self):
        """检查数据文件"""
        data_file = "教务数据.json"
        if os.path.exists(data_file):
            size = os.path.getsize(data_file)
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stats = f"""数据文件状态:
位置: {os.path.abspath(data_file)}
大小: {size} 字节
学员数: {len(data.get('students', []))}
课程数: {len(data.get('courses', []))}
排课数: {len(data.get('schedules', []))}
考勤数: {len(data.get('attendances', []))}
最后修改: {datetime.fromtimestamp(os.path.getmtime(data_file)).strftime('%Y-%m-%d %H:%M:%S')}"""
            
            messagebox.showinfo("数据文件检查", stats)
            self.status_var.set("数据文件检查完成")
        else:
            messagebox.showwarning("警告", f"数据文件不存在: {data_file}")
            self.status_var.set("数据文件不存在")
    
    def export_backup(self):
        """导出备份"""
        import shutil
        import time
        
        data_file = "教务数据.json"
        if not os.path.exists(data_file):
            messagebox.showerror("错误", "数据文件不存在，无法备份")
            return
        
        # 创建备份目录
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # 生成备份文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"教务数据_备份_{timestamp}.json")
        
        try:
            shutil.copy2(data_file, backup_file)
            messagebox.showinfo("成功", f"数据已备份到:\n{backup_file}")
            self.status_var.set(f"备份完成: {backup_file}")
        except Exception as e:
            messagebox.showerror("错误", f"备份失败: {str(e)}")
            self.status_var.set("备份失败")
    
    def show_system_info(self):
        """显示系统信息"""
        import platform
        import sys
        
        info = f"""系统信息:
Python版本: {sys.version}
操作系统: {platform.system()} {platform.release()}
架构: {platform.machine()}
当前目录: {os.getcwd()}

青羽教务系统:
主程序: main.py (重构版)
数据文件: 教务数据.json
备份目录: backups/
重构时间: 2024年1月"""
        
        messagebox.showinfo("系统信息", info)
        self.status_var.set("系统信息已显示")
    
    def open_main_program(self):
        """打开主程序"""
        main_file = "main.py"
        if os.path.exists(main_file):
            try:
                import subprocess
                if platform.system() == "Windows":
                    subprocess.Popen(["python", main_file])
                else:
                    subprocess.Popen(["python3", main_file])
                self.status_var.set("已启动主程序")
                messagebox.showinfo("提示", "主程序已启动，请稍候...")
            except Exception as e:
                messagebox.showerror("错误", f"启动失败: {str(e)}")
                self.status_var.set("启动失败")
        else:
            messagebox.showerror("错误", f"主程序不存在: {main_file}")
            self.status_var.set("主程序不存在")

def main():
    """主函数"""
    root = tk.Tk()
    app = QingYuEduBackup(root)
    
    # 居中显示
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()