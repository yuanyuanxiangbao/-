import os
import shutil
import threading
import json
import time
import sys
import tkinter as tk  # 正确的导入方式
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter.font import Font
from PIL import Image, ImageTk
from jmcomic import JmOption, download_album, JmAlbumDetail

# 固定路径（保持不变）
PDF_SAVE_DIR = r'D:\太虚山\野生文件\本子\PDF'
TEMP_IMAGE_DIR = os.path.join(PDF_SAVE_DIR, 'temp_images')
DOWNLOADED_RECORD = os.path.join(PDF_SAVE_DIR, 'downloaded_records.json')  # 下载记录文件

# 确保目录存在
os.makedirs(PDF_SAVE_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)


class DownloadRecord:
    """下载记录管理"""

    def __init__(self):
        self.records = self._load_records()

    def _load_records(self):
        """加载已下载记录"""
        if os.path.exists(DOWNLOADED_RECORD):
            try:
                with open(DOWNLOADED_RECORD, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载记录失败：{e}")
        return {}

    def save_records(self):
        """保存记录到文件"""
        try:
            with open(DOWNLOADED_RECORD, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记录失败：{e}")

    def is_downloaded(self, album_id):
        """检查是否已下载"""
        return album_id in self.records

    def add_record(self, album_id, album_title):
        """添加下载记录"""
        self.records[album_id] = {
            'title': album_title,
            'download_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.save_records()

    def get_title(self, album_id):
        """获取已下载本子标题"""
        return self.records.get(album_id, {}).get('title', '未知标题')


def get_jm_option():
    """优化JM配置（修复插件参数和目录规则）"""
    option = JmOption.default()

    # 修复目录规则：使用明确的根目录规则
    option.dir_rule.base_dir = TEMP_IMAGE_DIR
    option.dir_rule.rule = 'Bd'  # 直接使用base_dir，避免路径异常
    option.dir_rule.normalize_zh = 'zh-cn'  # 统一为简体中文目录

    # 图片下载配置
    option.download.image.decode = True
    option.download.image.suffix = '.jpg'
    option.download.threading.image = 20  # 调整并发数，平衡速度和稳定性

    # 修复img2pdf插件参数（使用正确的delete_original_file）
    option.plugins.after_album = [{
        'plugin': 'img2pdf',
        'kwargs': {
            'pdf_dir': PDF_SAVE_DIR,
            'filename_rule': 'Aname',
            'delete_original_file': True  # 修复参数名
        }
    }]

    return option


class AnimeStyleDownloader(tk.Tk):
    """二次元风格的下载器UI（彻底修复ttk样式兼容问题）"""

    def __init__(self):
        super().__init__()
        self.title("✨ 禁漫天堂PDF下载器 ✨")
        self.geometry("800x650")
        self.record_manager = DownloadRecord()
        self.option = get_jm_option()
        self.client = self.option.build_jm_client()  # 用于获取本子信息

        # 初始化样式（仅修改默认ttk样式，不自定义布局名）
        self.init_style()
        self.setup_ui()

    def init_style(self):
        """初始化样式（兼容所有Tkinter版本）"""
        # 主题色配置
        self.bg_main = "#f8f0f8"  # 主背景色（浅粉紫）
        self.bg_card = "#ffffff"  # 卡片背景（白）
        self.bg_input = "#fdf7f9"  # 输入框背景（浅粉）
        self.color_text = "#5a2b5a"  # 文字色（深紫）
        self.color_accent = "#d87093"  # 强调色（粉）
        self.color_btn = "#b19cd9"  # 按钮色（淡紫）
        self.color_btn_hover = "#c9a0dc"  # 按钮hover色

        # 主窗口背景
        self.configure(bg=self.bg_main)

        # 自定义字体
        self.font_title = Font(family="微软雅黑", size=18, weight="bold")
        self.font_normal = Font(family="微软雅黑", size=10)
        self.font_btn = Font(family="微软雅黑", size=10, weight="bold")

        # 修改ttk默认样式（关键：不自定义布局名，仅改默认样式）
        self.style = ttk.Style(self)
        # 按钮样式
        self.style.configure("TButton",
                             font=self.font_btn,
                             padding=6,
                             foreground=self.color_text)
        self.style.map("TButton",
                       background=[("active", self.color_btn_hover)],
                       foreground=[("active", self.color_text)])
        # 进度条样式
        self.style.configure("TProgressbar",
                             troughcolor=self.bg_main,
                             background=self.color_accent)
        # LabelFrame样式（仅改字体和内边距）
        self.style.configure("TLabelFrame",
                             font=self.font_normal,
                             foreground=self.color_text,
                             padding=8)

    def setup_ui(self):
        """构建UI（纯tk原生组件+默认ttk组件，确保兼容）"""
        # 背景画布（可选背景图）
        self.setup_background()

        # 主容器
        main_frame = tk.Frame(self, bg=self.bg_main, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题区域
        title_label = tk.Label(main_frame,
                               text="🌸 禁漫天堂PDF下载器 🌸",
                               font=self.font_title,
                               bg=self.bg_main,
                               fg=self.color_text)
        title_label.pack(pady=(0, 15))

        # ===== 输入区域 =====
        input_card = tk.Frame(main_frame, bg=self.bg_card, bd=2, relief=tk.RAISED)
        input_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 输入区域标题
        input_title = tk.Label(input_card,
                               text="📖 本子ID（每行一个）",
                               font=self.font_normal,
                               bg=self.bg_card,
                               fg=self.color_text)
        input_title.pack(anchor=tk.W, padx=10, pady=5)

        # 输入框
        self.id_text = scrolledtext.ScrolledText(input_card,
                                                 font=self.font_normal,
                                                 bg=self.bg_input,
                                                 fg=self.color_text,
                                                 bd=0,
                                                 relief=tk.FLAT,
                                                 height=8,
                                                 wrap=tk.WORD)
        self.id_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        #self.id_text.insert(tk.END, "1198446\n")  # 示例ID

        # ===== 状态区域 =====
        status_card = tk.Frame(main_frame, bg=self.bg_card, bd=2, relief=tk.RAISED)
        status_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 状态区域标题
        status_title = tk.Label(status_card,
                                text="📝 下载状态",
                                font=self.font_normal,
                                bg=self.bg_card,
                                fg=self.color_text)
        status_title.pack(anchor=tk.W, padx=10, pady=5)

        # 状态文本框
        self.status_text = scrolledtext.ScrolledText(status_card,
                                                     font=self.font_normal,
                                                     bg=self.bg_input,
                                                     fg=self.color_text,
                                                     bd=0,
                                                     relief=tk.FLAT,
                                                     height=10,
                                                     wrap=tk.WORD,
                                                     state='disabled')
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # ===== 进度条 =====
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10), ipady=3)

        # ===== 按钮区域 =====
        btn_frame = tk.Frame(main_frame, bg=self.bg_main)
        btn_frame.pack(fill=tk.X, pady=5)

        # 开始下载按钮
        self.start_btn = ttk.Button(btn_frame,
                                    text="🚀 开始下载",
                                    command=self.start_download_thread)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        # 清空状态按钮
        self.clear_btn = ttk.Button(btn_frame,
                                    text="🧹 清空状态",
                                    command=self.clear_status)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # 查看记录按钮
        self.records_btn = ttk.Button(btn_frame,
                                      text="📜 已下载记录",
                                      command=self.show_records)
        self.records_btn.pack(side=tk.RIGHT, padx=5)

    def setup_background(self):
        """设置背景图（缺失时静默失败）"""
        try:
            # 加载二次元背景图（放在最底层）
            bg_img = Image.open("anime_bg.png").convert("RGBA")
            bg_img = bg_img.resize((800, 650), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg_img)

            # 画布放在最底层
            self.canvas_bg = tk.Canvas(self, width=800, height=650, bd=0, highlightthickness=0)
            self.canvas_bg.place(x=0, y=0)
            self.canvas_bg.create_image(0, 0, image=self.bg_photo, anchor=tk.NW)

            # 透明遮罩（避免文字看不清）
            self.canvas_bg.create_rectangle(0, 0, 800, 650,
                                            fill="#ffffff",
                                            stipple="gray50",
                                            outline="")
        except Exception:
            pass

    def log(self, message):
        """线程安全的日志输出"""

        def update():
            self.status_text.config(state='normal')
            self.status_text.insert(tk.END, message + "\n")
            self.status_text.see(tk.END)
            self.status_text.config(state='disabled')

        self.after(0, update)

    def clear_status(self):
        """清空状态文本"""
        self.status_text.config(state='normal')
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state='disabled')

    def get_album_ids(self):
        """获取去重后的本子ID"""
        ids = self.id_text.get(1.0, tk.END).strip().split()
        return list(filter(None, set(ids)))

    def check_duplicate(self, album_id):
        """检查重复下载"""
        if self.record_manager.is_downloaded(album_id):
            title = self.record_manager.get_title(album_id)
            return messagebox.askyesno(
                "重复下载",
                f"本子《{title}》（ID：{album_id}）已下载过，是否继续下载？"
            )
        return True

    def show_records(self):
        """显示下载记录"""
        records = self.record_manager.records
        if not records:
            messagebox.showinfo("记录为空", "暂无下载记录~")
            return

        # 新建窗口
        win = tk.Toplevel(self)
        win.title("📜 已下载记录")
        win.geometry("600x400")
        win.configure(bg=self.bg_main)

        # 记录展示区域
        record_card = tk.Frame(win, bg=self.bg_card, bd=2, relief=tk.RAISED)
        record_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text = scrolledtext.ScrolledText(record_card,
                                         font=self.font_normal,
                                         bg=self.bg_input,
                                         fg=self.color_text,
                                         bd=0,
                                         relief=tk.FLAT)
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 填充记录
        for aid, info in records.items():
            text.insert(tk.END, f"ID：{aid}\n")
            text.insert(tk.END, f"标题：{info['title']}\n")
            text.insert(tk.END, f"下载时间：{info['download_time']}\n")
            text.insert(tk.END, "-" * 50 + "\n")
        text.config(state='disabled')

    def start_download_thread(self):
        """启动下载线程"""
        self.start_btn.config(state='disabled', text="⏳ 下载中...")
        self.progress['value'] = 0
        threading.Thread(target=self.download_albums, daemon=True).start()

    def clean_temp_files(self, max_retry=3):
        """健壮的临时文件清理"""
        for retry in range(max_retry):
            try:
                if os.path.exists(TEMP_IMAGE_DIR):
                    shutil.rmtree(TEMP_IMAGE_DIR, ignore_errors=True)
                os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)
                self.log(f"✅ 临时目录清理完成（重试：{retry + 1}）")
                return
            except Exception as e:
                self.log(f"⚠️ 清理失败（{retry + 1}/{max_retry}）：{str(e)}")
                time.sleep(1)
        self.log(f"❌ 临时目录清理失败：{TEMP_IMAGE_DIR}")

    def download_albums(self):
        """下载主逻辑"""
        album_ids = self.get_album_ids()
        if not album_ids:
            self.log("❌ 请输入至少一个本子ID！")
            self.after(0, lambda: self.start_btn.config(state='normal', text="🚀 开始下载"))
            return

        self.log(f"📋 找到 {len(album_ids)} 个本子ID，开始处理...")
        self.after(0, lambda: self.progress.configure(maximum=len(album_ids)))

        for idx, aid in enumerate(album_ids, 1):
            # 检查重复
            if not self.check_duplicate(aid):
                self.log(f"⏭️ 跳过已下载本子：{aid}")
                self.after(0, lambda v=idx: self.progress.configure(value=v))
                continue

            self.log(f"\n=== 🔍 处理本子ID：{aid}（{idx}/{len(album_ids)}）===")
            self.after(0, lambda v=idx: self.progress.configure(value=v))

            try:
                # 获取本子标题
                album_detail = self.client.get_album_detail(aid)
                title = album_detail.title
                self.log(f"📖 本子标题：{title}")

                # 下载并转换PDF
                download_album(aid, option=self.option)
                self.log(f"✅ 成功：《{title}》已保存为PDF")

                # 记录下载信息
                self.record_manager.add_record(aid, title)
                self.clean_temp_files()

            except Exception as e:
                self.log(f"❌ 处理失败：{aid} - {str(e)}")

        # 最终清理
        self.clean_temp_files()
        self.log("\n🎉 所有任务处理完成！")
        self.after(0, lambda: self.start_btn.config(state='normal', text="🚀 开始下载"))


if __name__ == '__main__':
    # 直接启动（依赖已手动安装）
    app = AnimeStyleDownloader()
    app.mainloop()