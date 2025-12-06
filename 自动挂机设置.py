import tkinter as tk
from tkinter import ttk, scrolledtext
from pathlib import Path
import subprocess

class RobotConfigRow:
    def __init__(self, master, index, update_preview_callback):
        self.master = master
        self.index = index
        self.update_preview = update_preview_callback

        self.frame = tk.Frame(master)
        self.frame.grid(row=index, column=0, pady=2, sticky="w")

        self.var标志 = tk.StringVar(value=f"模拟器索引{index}")
        tk.Label(self.frame, text=f"机器人 {index} 标志").grid(row=0, column=0)
        tk.Entry(self.frame, textvariable=self.var标志, width=12).grid(row=0, column=1)

        self.var雷电索引 = tk.StringVar(value="1")
        tk.Label(self.frame, text="雷电索引").grid(row=0, column=2)
        tk.Entry(self.frame, textvariable=self.var雷电索引, width=4).grid(row=0, column=3)

        self.var刷墙 = tk.BooleanVar()
        tk.Checkbutton(self.frame, text="刷墙", variable=self.var刷墙, command=self.update_preview).grid(row=0, column=4)

        self.var刷主世界 = tk.BooleanVar(value=True)
        tk.Checkbutton(self.frame, text="刷主世界", variable=self.var刷主世界, command=self.update_preview).grid(row=0, column=5)

        self.var刷夜世界 = tk.BooleanVar()
        tk.Checkbutton(self.frame, text="刷夜世界", variable=self.var刷夜世界, command=self.update_preview).grid(row=0, column=6)

        self.btn删除 = tk.Button(self.frame, text="删除", command=self.删除行)
        self.btn删除.grid(row=0, column=7)

    def 删除行(self):
        self.frame.destroy()
        app.robot_rows.remove(self)
        self.update_preview()

    def 获取参数(self):
        params = f"标志={self.var标志.get()} 雷电索引={self.var雷电索引.get()}"
        if self.var刷墙.get():
            params += " 刷墙"
        if self.var刷主世界.get():
            params += " 刷主世界"
        if self.var刷夜世界.get():
            params += " 刷夜世界"
        return params

class App:
    def __init__(self, root):
        self.root = root
        root.title("coc_robot 自动挂机设置（小白友好）")

        self.robot_rows = []

        # 多机器人配置区
        tk.Label(root, text="机器人配置").grid(row=0, column=0, sticky="w")
        self.robots_frame = tk.Frame(root)
        self.robots_frame.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # 添加机器人按钮
        tk.Button(root, text="添加机器人", command=self.添加机器人).grid(row=2, column=0, sticky="w", padx=5, pady=5)

        # 虚拟环境选项
        self.var虚拟环境 = tk.BooleanVar()
        tk.Checkbutton(root, text="使用虚拟环境启动", variable=self.var虚拟环境, command=self.更新预览).grid(row=3, column=0, sticky="w", padx=5, pady=2)

        # BAT 预览
        tk.Label(root, text="BAT 文件预览").grid(row=4, column=0, sticky="w")
        self.txt预览 = scrolledtext.ScrolledText(root, width=80, height=15)
        self.txt预览.grid(row=5, column=0, padx=5, pady=5)

        # 一键生成并注册任务
        tk.Label(root, text="计划任务名称").grid(row=6, column=0, sticky="w")
        self.entry任务名称 = tk.Entry(root, width=30)
        self.entry任务名称.grid(row=7, column=0, sticky="w", padx=5, pady=2)
        tk.Label(root, text="执行时间 (HH:MM)").grid(row=8, column=0, sticky="w")
        self.entry时间 = tk.Entry(root, width=10)
        self.entry时间.grid(row=9, column=0, sticky="w", padx=5, pady=2)
        self.entry时间.insert(0, "09:00")
        tk.Button(root, text="一键生成 BAT 并注册任务", bg="lightgreen", command=self.一键创建).grid(row=10, column=0, pady=5)

        # 删除任务
        tk.Label(root, text="删除计划任务名称").grid(row=11, column=0, sticky="w")
        self.entry删除任务 = tk.Entry(root, width=30)
        self.entry删除任务.grid(row=12, column=0, sticky="w", padx=5, pady=2)
        tk.Button(root, text="删除计划任务", bg="lightcoral", command=lambda: self.删除计划任务(self.entry删除任务.get().strip())).grid(row=13, column=0, pady=5)

        # 初始化一个默认机器人
        self.添加机器人()

    def 添加机器人(self):
        row = RobotConfigRow(self.robots_frame, len(self.robot_rows), self.更新预览)
        self.robot_rows.append(row)
        self.更新预览()

    def 更新预览(self):
        bat_preview = "@echo off\ncd /d %~dp0\n"
        if self.var虚拟环境.get():
            bat_preview += "call .venv\\Scripts\\activate.bat\n"
        bat_preview += "python 主入口.py ^\n"
        for i, row in enumerate(self.robot_rows):
            sep = " ^\n" if i < len(self.robot_rows) - 1 else "\n"
            bat_preview += f"    --机器人 {row.获取参数()}{sep}"
        bat_preview += "pause\n"

        self.txt预览.delete("1.0", tk.END)
        self.txt预览.insert(tk.END, bat_preview)

    def 生成_bat(self, 文件名="每日挂机.bat"):
        path = Path(文件名).resolve()
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.txt预览.get("1.0", tk.END))
        return path

    def 注册计划任务(self, bat_path, 任务名称, 每日=True, 时间="09:00"):
        cmd = [
            "schtasks",
            "/Create",
            "/TN", 任务名称,
            "/TR", str(bat_path),
            "/SC", "DAILY" if 每日 else "ONCE",
            "/ST", 时间,
            "/F"
        ]
        try:
            subprocess.run(cmd, check=True)
            tk.messagebox.showinfo("完成", f"计划任务已创建：{任务名称}")
        except subprocess.CalledProcessError as e:
            tk.messagebox.showerror("错误", f"计划任务创建失败：{e}")

    def 删除计划任务(self, 任务名称):
        if not 任务名称:
            tk.messagebox.showwarning("警告", "请输入任务名称")
            return
        cmd = ["schtasks", "/Delete", "/TN", 任务名称, "/F"]
        try:
            subprocess.run(cmd, check=True)
            tk.messagebox.showinfo("完成", f"计划任务已删除：{任务名称}")
        except subprocess.CalledProcessError as e:
            tk.messagebox.showerror("错误", f"计划任务删除失败：{e}")

    def 一键创建(self):
        if not self.robot_rows:
            tk.messagebox.showwarning("警告", "请至少添加一个机器人")
            return
        bat_path = self.生成_bat()
        任务名称 = self.entry任务名称.get().strip()
        时间 = self.entry时间.get().strip()
        if not 任务名称 or not 时间:
            tk.messagebox.showwarning("警告", "请填写任务名称和执行时间")
            return
        self.注册计划任务(bat_path, 任务名称, 每日=True, 时间=时间)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
