# launcher.py
# Cking 控制面板 - 一键启动 Ollama + 模型 + 网页界面 + 公网隧道

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import requests
import threading
import time
import os
import socket

# Windows 隐藏子进程窗口的标志
CREATE_NO_WINDOW = 0x08000000

OLLAMA_API = "http://localhost:11434"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(PROJECT_DIR, "venv", "Scripts", "python.exe")
CLOUDFLARED = os.path.join(PROJECT_DIR, "cloudflared.exe")
TUNNEL_LOG = os.path.join(PROJECT_DIR, "tunnel.log")


class CkingLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cking 控制面板")
        self.root.geometry("520x700")
        self.root.resizable(False, False)

        self.webui_process = None
        self.tunnel_process = None
        self.tunnel_log_file = None
        self.selected_model = tk.StringVar()
        self.public_url = ""

        self._build_ui()
        self._check_ollama_status()

    def _build_ui(self):
        # ---- Ollama 状态区 ----
        frame_ollama = ttk.LabelFrame(self.root, text="Ollama 服务", padding=10)
        frame_ollama.pack(fill="x", padx=10, pady=5)

        self.lbl_ollama_status = ttk.Label(frame_ollama, text="检测中...")
        self.lbl_ollama_status.pack(side="left")

        row_ollama = ttk.Frame(frame_ollama)
        row_ollama.pack(side="right")
        ttk.Button(row_ollama, text="刷新", command=self._check_ollama_status).pack(side="left", padx=2)
        ttk.Button(row_ollama, text="关闭Ollama", command=self._stop_ollama).pack(side="left", padx=2)

        # ---- 模型选择区 ----
        frame_model = ttk.LabelFrame(self.root, text="模型管理", padding=10)
        frame_model.pack(fill="x", padx=10, pady=5)

        row1 = ttk.Frame(frame_model)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="选择模型：").pack(side="left")
        self.combo_model = ttk.Combobox(row1, textvariable=self.selected_model, state="readonly", width=30)
        self.combo_model.pack(side="left", padx=5)
        ttk.Button(row1, text="刷新列表", command=self._load_models).pack(side="left")

        row2 = ttk.Frame(frame_model)
        row2.pack(fill="x", pady=5)
        self.btn_start_model = ttk.Button(row2, text="启动模型", command=self._start_model)
        self.btn_start_model.pack(side="left")
        self.btn_stop_model = ttk.Button(row2, text="停止模型", command=self._stop_model)
        self.btn_stop_model.pack(side="left", padx=10)

        self.lbl_model_status = ttk.Label(frame_model, text="模型状态：未检测")
        self.lbl_model_status.pack(anchor="w", pady=3)

        # ---- 网页界面区 ----
        frame_webui = ttk.LabelFrame(self.root, text="网页界面", padding=10)
        frame_webui.pack(fill="x", padx=10, pady=5)

        row3 = ttk.Frame(frame_webui)
        row3.pack(fill="x", pady=2)
        self.btn_start_webui = ttk.Button(row3, text="启动网页界面", command=self._start_webui)
        self.btn_start_webui.pack(side="left")
        self.btn_stop_webui = ttk.Button(row3, text="停止网页界面", command=self._stop_webui, state="disabled")
        self.btn_stop_webui.pack(side="left", padx=10)

        self.lbl_webui_status = ttk.Label(frame_webui, text="网页界面：未启动")
        self.lbl_webui_status.pack(anchor="w", pady=3)

        self.lbl_local_url = ttk.Label(frame_webui, text="本地链接：无")
        self.lbl_local_url.pack(anchor="w", pady=2)

        # ---- 公网隧道区 ----
        frame_tunnel = ttk.LabelFrame(self.root, text="公网隧道 (Cloudflare)", padding=10)
        frame_tunnel.pack(fill="x", padx=10, pady=5)

        row4 = ttk.Frame(frame_tunnel)
        row4.pack(fill="x", pady=2)
        self.btn_start_tunnel = ttk.Button(row4, text="开启公网隧道", command=self._start_tunnel, state="disabled")
        self.btn_start_tunnel.pack(side="left")
        self.btn_stop_tunnel = ttk.Button(row4, text="关闭隧道", command=self._stop_tunnel, state="disabled")
        self.btn_stop_tunnel.pack(side="left", padx=10)

        self.lbl_tunnel_status = ttk.Label(frame_tunnel, text="隧道状态：未启动")
        self.lbl_tunnel_status.pack(anchor="w", pady=3)

        self.lbl_public_url = ttk.Label(frame_tunnel, text="公网链接：无", foreground="blue", font=("微软雅黑", 10, "bold"))
        self.lbl_public_url.pack(anchor="w", pady=3)

        self.btn_copy_url = ttk.Button(frame_tunnel, text="复制链接", command=self._copy_url, state="disabled")
        self.btn_copy_url.pack(anchor="w")

        # ---- 日志区 ----
        frame_log = ttk.LabelFrame(self.root, text="运行日志", padding=5)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(frame_log, height=8, state="disabled", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)

        # ---- 底部 ----
        frame_bottom = ttk.Frame(self.root, padding=5)
        frame_bottom.pack(fill="x", padx=10)
        ttk.Button(frame_bottom, text="退出", command=self._on_close).pack(side="right")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ==================== Ollama ====================

    def _check_ollama_status(self):
        def _check():
            try:
                r = requests.get(f"{OLLAMA_API}/api/tags", timeout=3)
                if r.status_code == 200:
                    self.lbl_ollama_status.config(text="Ollama 状态：● 运行中", foreground="green")
                    self._log("Ollama 服务已连接")
                    self._load_models()
                    self._check_running_models()
                    return
            except:
                pass
            self.lbl_ollama_status.config(text="Ollama 状态：○ 未运行", foreground="red")
            self._log("Ollama 未运行")
        threading.Thread(target=_check, daemon=True).start()

    def _stop_ollama(self):
        """关闭 Ollama 服务"""
        def _stop():
            self._log("正在关闭 Ollama 服务...")
            try:
                # 先卸载所有模型释放显存
                requests.post(f"{OLLAMA_API}/api/generate",
                    json={"model": "", "keep_alive": 0}, timeout=5)
            except:
                pass
            try:
                # Windows 上用 taskkill 关闭 ollama
                subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"],
                    capture_output=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                subprocess.run(["taskkill", "/F", "/IM", "ollama_app.exe"],
                    capture_output=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                time.sleep(1)
                self.lbl_ollama_status.config(text="Ollama 状态：○ 已关闭", foreground="gray")
                self.lbl_model_status.config(text="模型状态：未检测", foreground="black")
                self.combo_model["values"] = []
                self._log("Ollama 服务已关闭")
            except Exception as e:
                self._log(f"关闭 Ollama 失败：{e}")
        threading.Thread(target=_stop, daemon=True).start()

    def _load_models(self):
        def _load():
            try:
                r = requests.get(f"{OLLAMA_API}/api/tags", timeout=5)
                if r.status_code == 200:
                    models = [m["name"] for m in r.json().get("models", [])]
                    self.combo_model["values"] = models
                    if models:
                        self.selected_model.set(models[0])
                        self._log(f"发现 {len(models)} 个模型：{', '.join(models)}")
                    else:
                        self._log("没有找到已安装的模型")
            except Exception as e:
                self._log(f"获取模型列表失败：{e}")
        threading.Thread(target=_load, daemon=True).start()

    def _check_running_models(self):
        def _check():
            try:
                r = requests.get(f"{OLLAMA_API}/api/ps", timeout=3)
                if r.status_code == 200:
                    running = r.json().get("models", [])
                    if running:
                        names = [m["name"] for m in running]
                        self.lbl_model_status.config(text=f"模型状态：● 已加载 {', '.join(names)}", foreground="green")
                        self._log(f"运行中的模型：{', '.join(names)}")
                    else:
                        self.lbl_model_status.config(text="模型状态：○ 无模型运行", foreground="gray")
            except:
                self.lbl_model_status.config(text="模型状态：检测失败", foreground="red")
        threading.Thread(target=_check, daemon=True).start()

    def _start_model(self):
        model = self.selected_model.get()
        if not model:
            messagebox.showwarning("提示", "请先选择一个模型")
            return

        def _start():
            self.btn_start_model.config(state="disabled")
            self._log(f"正在加载模型 {model} ...")
            self.lbl_model_status.config(text="模型状态：加载中...", foreground="orange")
            try:
                r = requests.post(f"{OLLAMA_API}/api/generate", json={
                    "model": model, "prompt": "hello", "stream": False,
                    "options": {"num_predict": 1}
                }, timeout=120)
                if r.status_code == 200:
                    self.lbl_model_status.config(text=f"模型状态：● 已加载 {model}", foreground="green")
                    self._log(f"模型 {model} 加载成功")
                else:
                    self.lbl_model_status.config(text="模型状态：加载失败", foreground="red")
                    self._log(f"模型加载失败：{r.status_code}")
            except Exception as e:
                self.lbl_model_status.config(text="模型状态：加载失败", foreground="red")
                self._log(f"模型加载失败：{e}")
            finally:
                self.btn_start_model.config(state="normal")
        threading.Thread(target=_start, daemon=True).start()

    def _stop_model(self):
        """停止模型，释放显存"""
        model = self.selected_model.get()
        if not model:
            messagebox.showwarning("提示", "请先选择一个模型")
            return

        def _stop():
            self._log(f"正在停止模型 {model} ...")
            try:
                r = requests.post(f"{OLLAMA_API}/api/generate", json={
                    "model": model, "keep_alive": 0
                }, timeout=10)
                if r.status_code == 200:
                    self.lbl_model_status.config(text="模型状态：○ 已停止", foreground="gray")
                    self._log(f"模型 {model} 已停止，显存已释放")
            except Exception as e:
                self._log(f"停止模型失败：{e}")
        threading.Thread(target=_stop, daemon=True).start()

    # ==================== 网页界面 ====================

    def _start_webui(self):
        if self.webui_process and self.webui_process.poll() is None:
            self._log("网页界面已在运行")
            return

        self._log("正在启动网页界面...")
        try:
            env = os.environ.copy()
            env["CKING_BROWSER"] = "0"
            self.webui_process = subprocess.Popen(
                [VENV_PYTHON, os.path.join(PROJECT_DIR, "webui.py")],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=PROJECT_DIR, env=env,
                creationflags=CREATE_NO_WINDOW,
            )
            self.btn_start_webui.config(state="disabled")
            self.btn_stop_webui.config(state="normal")
            self._log("网页界面进程已启动，等待加载...")
            self._poll_port(7860, self._on_webui_ready)
        except Exception as e:
            self._log(f"启动失败：{e}")

    def _on_webui_ready(self):
        self.lbl_webui_status.config(text="网页界面：已启动", foreground="green")
        self.lbl_local_url.config(text="本地链接：http://127.0.0.1:7860")
        self.btn_start_tunnel.config(state="normal")
        self._log("网页界面启动成功！本地访问：http://127.0.0.1:7860")

    def _stop_webui(self):
        self._stop_tunnel()
        if self.webui_process and self.webui_process.poll() is None:
            self.webui_process.terminate()
        self.lbl_webui_status.config(text="网页界面：已停止", foreground="gray")
        self.lbl_local_url.config(text="本地链接：无")
        self.btn_start_webui.config(state="normal")
        self.btn_stop_webui.config(state="disabled")
        self.btn_start_tunnel.config(state="disabled")
        self._log("网页界面已停止")

    # ==================== 公网隧道 ====================

    def _start_tunnel(self):
        if self.tunnel_process and self.tunnel_process.poll() is None:
            self._log("隧道已在运行")
            return

        if not os.path.exists(CLOUDFLARED):
            self._log("错误：找不到 cloudflared.exe")
            messagebox.showerror("错误", f"找不到 cloudflared.exe\n路径：{CLOUDFLARED}")
            return

        self._log("正在开启 Cloudflare 隧道...")
        self.lbl_tunnel_status.config(text="隧道状态：连接中...", foreground="orange")

        # 清理旧日志
        try:
            if os.path.exists(TUNNEL_LOG):
                os.remove(TUNNEL_LOG)
        except:
            pass

        # 关闭旧的文件句柄
        if self.tunnel_log_file:
            try:
                self.tunnel_log_file.close()
            except:
                pass

        try:
            # 直接输出到日志文件，不走 PIPE
            self.tunnel_log_file = open(TUNNEL_LOG, "w", encoding="utf-8")
            self.tunnel_process = subprocess.Popen(
                [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:7860"],
                stdout=self.tunnel_log_file,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_DIR,
                creationflags=CREATE_NO_WINDOW,
            )
            self.btn_start_tunnel.config(state="disabled")
            self.btn_stop_tunnel.config(state="normal")
            self._poll_tunnel_url()
        except Exception as e:
            self._log(f"隧道启动失败：{e}")

    def _poll_tunnel_url(self, attempts=0):
        """从日志文件中读取公网链接"""
        if attempts > 30:
            self._log("隧道连接超时，请检查网络")
            self.lbl_tunnel_status.config(text="隧道状态：超时", foreground="red")
            return
        if self.tunnel_process and self.tunnel_process.poll() is not None:
            self._log("隧道进程已退出，可能网络有问题")
            self.lbl_tunnel_status.config(text="隧道状态：已停止", foreground="gray")
            self.btn_start_tunnel.config(state="normal")
            self.btn_stop_tunnel.config(state="disabled")
            return

        try:
            if os.path.exists(TUNNEL_LOG):
                with open(TUNNEL_LOG, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if content:
                    for line in content.split("\n"):
                        if ".trycloudflare.com" in line:
                            for word in line.split():
                                if ".trycloudflare.com" in word:
                                    url = word.strip().rstrip(".")
                                    if not url.startswith("http"):
                                        url = "https://" + url
                                    self.public_url = url
                                    self.lbl_public_url.config(text=f"公网链接：{url}")
                                    self.lbl_tunnel_status.config(text="隧道状态：● 已连接", foreground="green")
                                    self.btn_copy_url.config(state="normal")
                                    self._log(f"公网链接已生成：{url}")
                                    return
        except:
            pass

        self.root.after(1000, self._poll_tunnel_url, attempts + 1)

    def _stop_tunnel(self):
        if self.tunnel_process and self.tunnel_process.poll() is None:
            self.tunnel_process.terminate()
        if self.tunnel_log_file:
            try:
                self.tunnel_log_file.close()
            except:
                pass
            self.tunnel_log_file = None
        self.lbl_tunnel_status.config(text="隧道状态：已停止", foreground="gray")
        self.lbl_public_url.config(text="公网链接：无")
        self.btn_copy_url.config(state="disabled")
        self.btn_start_tunnel.config(state="normal")
        self.btn_stop_tunnel.config(state="disabled")
        self.public_url = ""
        self._log("隧道已关闭")

    def _copy_url(self):
        if self.public_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.public_url)
            self._log(f"已复制：{self.public_url}")

    # ==================== 工具方法 ====================

    def _poll_port(self, port, callback, attempts=0):
        """轮询检测端口是否可用"""
        if attempts > 30:
            self._log(f"端口 {port} 超时")
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(("127.0.0.1", port))
            s.close()
            callback()
            return
        except:
            pass
        self.root.after(1000, self._poll_port, port, callback, attempts + 1)

    def _on_close(self):
        if self.webui_process and self.webui_process.poll() is None:
            self.webui_process.terminate()
        if self.tunnel_process and self.tunnel_process.poll() is None:
            self.tunnel_process.terminate()
        if self.tunnel_log_file:
            try:
                self.tunnel_log_file.close()
            except:
                pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = CkingLauncher()
    app.run()
