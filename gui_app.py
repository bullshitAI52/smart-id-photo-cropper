#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能证件照批量处理工具 - 完整修复版
功能：单张/批量处理、自定义尺寸、智能裁剪、居中选项、DPI设置
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
from datetime import datetime

class SmartBatchCropApp:
    """智能批量裁剪应用"""

    def __init__(self, root):
        self.root = root
        self.root.title("智能证件照批量处理工具")
        self.root.geometry("1280x768")

        # 变量初始化
        self.original_image = None
        self.pil_image = None
        self.display_image = None
        self.crop_rect = None

        # 目标尺寸
        self.target_width = tk.IntVar(value=295)
        self.target_height = tk.IntVar(value=413)
        self.target_dpi = tk.IntVar(value=300)

        # 居中选项
        self.horizontal_center = tk.BooleanVar(value=True)
        self.vertical_center = tk.BooleanVar(value=False)

        # 批量处理相关
        self.batch_files = []
        self.batch_processing = False
        self.batch_thread = None
        self.batch_settings = {}

        # 缩放相关
        self.scale_factor = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0

        # 交互状态
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.crop_start_x = 0
        self.crop_start_y = 0

        # 创建界面
        self.create_widgets()

        # 绑定事件
        self.setup_bindings()

        # 更新裁剪框
        self.update_crop_rect()

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # 单张处理按钮
        ttk.Button(toolbar, text="打开单张图片", command=self.open_single_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="保存单张", command=self.save_crop).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="重置位置", command=self.reset_position).pack(side=tk.LEFT, padx=5)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # 批量处理按钮
        ttk.Button(toolbar, text="批量处理", command=self.open_batch_window).pack(side=tk.LEFT, padx=5)

        # 开始批量处理按钮
        self.start_batch_btn = ttk.Button(toolbar, text="开始批量处理", 
                                         command=self.start_batch_from_main,
                                         state=tk.DISABLED)
        self.start_batch_btn.pack(side=tk.LEFT, padx=5)

        # 参数设置区域
        params_frame = ttk.LabelFrame(main_frame, text="裁剪参数", padding="10")
        params_frame.pack(fill=tk.X, pady=(0, 10))

        # 目标尺寸
        size_frame = ttk.Frame(params_frame)
        size_frame.pack(fill=tk.X, pady=5)

        ttk.Label(size_frame, text="目标宽度:").pack(side=tk.LEFT, padx=(0, 5))
        width_spin = ttk.Spinbox(
            size_frame,
            from_=100,
            to=2000,
            increment=1,
            textvariable=self.target_width,
            width=8,
            command=self.update_crop_rect
        )
        width_spin.pack(side=tk.LEFT, padx=(0, 15))
        width_spin.bind('<Return>', lambda e: self.update_crop_rect())

        ttk.Label(size_frame, text="目标高度:").pack(side=tk.LEFT, padx=(0, 5))
        height_spin = ttk.Spinbox(
            size_frame,
            from_=100,
            to=2000,
            increment=1,
            textvariable=self.target_height,
            width=8,
            command=self.update_crop_rect
        )
        height_spin.pack(side=tk.LEFT, padx=(0, 15))
        height_spin.bind('<Return>', lambda e: self.update_crop_rect())

        # DPI设置
        ttk.Label(size_frame, text="DPI:").pack(side=tk.LEFT, padx=(0, 5))
        dpi_spin = ttk.Spinbox(
            size_frame,
            from_=72,
            to=1200,
            increment=50,
            textvariable=self.target_dpi,
            width=6,
            command=self.update_crop_rect
        )
        dpi_spin.pack(side=tk.LEFT, padx=(0, 15))
        dpi_spin.bind('<Return>', lambda e: self.update_crop_rect())

        # 居中选项
        center_frame = ttk.Frame(params_frame)
        center_frame.pack(fill=tk.X, pady=5)

        self.horizontal_check = ttk.Checkbutton(
            center_frame,
            text="水平居中",
            variable=self.horizontal_center,
            command=self.update_crop_rect
        )
        self.horizontal_check.pack(side=tk.LEFT, padx=(0, 20))

        self.vertical_check = ttk.Checkbutton(
            center_frame,
            text="垂直居中",
            variable=self.vertical_center,
            command=self.update_crop_rect
        )
        self.vertical_check.pack(side=tk.LEFT)

        # 标准尺寸快捷按钮
        std_frame = ttk.Frame(params_frame)
        std_frame.pack(fill=tk.X, pady=5)

        ttk.Label(std_frame, text="标准尺寸:").pack(side=tk.LEFT, padx=(0, 10))

        standard_sizes = [
            ("1寸", (295, 413)),
            ("2寸", (413, 579)),
            ("身份证", (358, 441)),
            ("小2寸", (413, 531)),
            ("护照", (390, 567)),
        ]

        for name, size in standard_sizes:
            btn = ttk.Button(
                std_frame,
                text=name,
                command=lambda s=size: self.set_standard_size(s)
            )
            btn.pack(side=tk.LEFT, padx=2)

        # 主显示区域
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True)

        # 画布用于显示图片和裁剪框
        self.canvas = tk.Canvas(
            display_frame,
            bg="#f0f0f0",
            highlightthickness=1,
            highlightbackground="#cccccc"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 底部状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        # 单张处理状态
        self.status_var = tk.StringVar(value="就绪 - 请打开图片")
        ttk.Label(status_frame, textvariable=self.status_var, width=50).pack(side=tk.LEFT)

        # 批量处理进度
        self.batch_progress_var = tk.DoubleVar(value=0)
        self.batch_progress_bar = ttk.Progressbar(
            status_frame, 
            variable=self.batch_progress_var, 
            maximum=100, 
            mode='determinate',
            length=200
        )
        self.batch_progress_bar.pack(side=tk.LEFT, padx=10)

        # 批量处理状态
        self.batch_status_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.batch_status_var, 
                 width=30, foreground="#0066cc").pack(side=tk.LEFT)

        # 停止批量处理按钮
        self.stop_batch_btn = ttk.Button(
            status_frame,
            text="停止",
            command=self.stop_batch_processing,
            state=tk.DISABLED
        )
        self.stop_batch_btn.pack(side=tk.RIGHT, padx=5)

        # 计算信息显示
        self.calc_var = tk.StringVar(value="")
        calc_label = ttk.Label(
            main_frame,
            textvariable=self.calc_var,
            foreground="#666",
            font=("TkDefaultFont", 9)
        )
        calc_label.pack(fill=tk.X, pady=(5, 0))

    def setup_bindings(self):
        """设置事件绑定"""
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_crop)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # 绑定尺寸变化事件
        self.target_width.trace("w", lambda *args: self.update_crop_rect())
        self.target_height.trace("w", lambda *args: self.update_crop_rect())

    def open_batch_window(self):
        """打开批量处理设置窗口"""
        batch_window = tk.Toplevel(self.root)
        batch_window.title("批量处理设置")

        # 获取主窗口尺寸并设置为85%
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        batch_width = int(main_width * 0.85)
        batch_height = int(main_height * 0.85)

        # 确保最小尺寸
        batch_width = max(batch_width, 800)
        batch_height = max(batch_height, 600)

        # 计算居中位置
        x = self.root.winfo_x() + (main_width - batch_width) // 2
        y = self.root.winfo_y() + (main_height - batch_height) // 2

        batch_window.geometry(f"{batch_width}x{batch_height}+{x}+{y}")
        batch_window.transient(self.root)
        batch_window.grab_set()

        # 主框架
        main_frame = ttk.Frame(batch_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(title_frame, text="批量证件照处理设置", 
                 font=("TkDefaultFont", 14, "bold")).pack()

        # 创建滚动区域
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        content_frame = ttk.Frame(canvas)

        content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # 设置固定宽度
        content_width = 750
        canvas.create_window((0, 0), window=content_frame, anchor="nw", width=content_width)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ====== 文件夹设置 ======
        folder_frame = ttk.LabelFrame(content_frame, text="文件夹设置", padding="15")
        folder_frame.pack(fill=tk.X, pady=(0, 20))

        # 输入文件夹
        ttk.Label(folder_frame, text="输入文件夹:", font=("TkDefaultFont", 10)).grid(
            row=0, column=0, padx=(0, 10), pady=10, sticky=tk.W)

        self.input_dir_var = tk.StringVar()
        input_entry = ttk.Entry(folder_frame, textvariable=self.input_dir_var)
        input_entry.grid(row=0, column=1, padx=(0, 10), pady=10, sticky=tk.EW)

        ttk.Button(folder_frame, text="浏览", 
                  command=lambda: self.browse_folder(self.input_dir_var),
                  width=8).grid(row=0, column=2, pady=10)

        # 输出文件夹
        ttk.Label(folder_frame, text="输出文件夹:", font=("TkDefaultFont", 10)).grid(
            row=1, column=0, padx=(0, 10), pady=(0, 10), sticky=tk.W)

        self.output_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "batch_output"))
        output_entry = ttk.Entry(folder_frame, textvariable=self.output_dir_var)
        output_entry.grid(row=1, column=1, padx=(0, 10), pady=(0, 10), sticky=tk.EW)

        ttk.Button(folder_frame, text="浏览", 
                  command=lambda: self.browse_folder(self.output_dir_var),
                  width=8).grid(row=1, column=2, pady=(0, 10))

        folder_frame.columnconfigure(1, weight=1)

        # ====== 输出格式 ======
        format_frame = ttk.LabelFrame(content_frame, text="输出格式", padding="15")
        format_frame.pack(fill=tk.X, pady=(0, 20))

        self.format_var = tk.StringVar(value="JPEG")
        format_options = [
            ("JPEG格式 (推荐)", "JPEG"),
            ("PNG格式", "PNG"),
            ("保持原格式", "保持原格式")
        ]

        for i, (text, value) in enumerate(format_options):
            ttk.Radiobutton(format_frame, text=text, variable=self.format_var, 
                          value=value).pack(anchor=tk.W, pady=5)

        # ====== 文件命名 ======
        naming_frame = ttk.LabelFrame(content_frame, text="文件命名", padding="15")
        naming_frame.pack(fill=tk.X, pady=(0, 20))

        naming_frame.columnconfigure(1, weight=1)

        # 前缀设置
        ttk.Label(naming_frame, text="文件名前缀:", font=("TkDefaultFont", 10)).grid(
            row=0, column=0, padx=(0, 15), pady=10, sticky=tk.W)

        self.name_prefix_var = tk.StringVar(value="processed_")
        ttk.Entry(naming_frame, textvariable=self.name_prefix_var).grid(
            row=0, column=1, pady=10, sticky=tk.W)

        # 命名选项
        options_row = ttk.Frame(naming_frame)
        options_row.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)

        self.keep_original_name = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_row, text="保留原文件名", 
                       variable=self.keep_original_name).pack(side=tk.LEFT, padx=(0, 20))

        self.add_timestamp = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_row, text="添加时间戳", 
                       variable=self.add_timestamp).pack(side=tk.LEFT, padx=(0, 20))

        self.add_counter = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_row, text="添加序号", 
                       variable=self.add_counter).pack(side=tk.LEFT)

        # ====== 处理选项 ======
        options_frame = ttk.LabelFrame(content_frame, text="处理选项", padding="15")
        options_frame.pack(fill=tk.X, pady=(0, 20))

        self.skip_errors = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="跳过错误文件，继续处理其他", 
                       variable=self.skip_errors).pack(anchor=tk.W, pady=5)

        self.auto_open_output = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="处理完成后自动打开输出文件夹", 
                       variable=self.auto_open_output).pack(anchor=tk.W, pady=5)

        # 预览按钮
        preview_frame = ttk.Frame(content_frame)
        preview_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Button(preview_frame, text="预览文件列表", 
                  command=lambda: self.preview_batch_files(batch_window)).pack()

        # ====== 底部按钮区域 ======
        button_container = ttk.Frame(main_frame)
        button_container.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(10, 0))

        ttk.Separator(button_container, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 15))

        button_frame = ttk.Frame(button_container)
        button_frame.pack(expand=True)

        ttk.Button(button_frame, text="保存设置", 
                  command=lambda: self.save_batch_settings(batch_window),
                  width=12).grid(row=0, column=0, padx=10, pady=5)

        ttk.Button(button_frame, text="确认并开始处理", 
                  command=lambda: self.confirm_and_start_batch(batch_window),
                  width=15).grid(row=0, column=1, padx=10, pady=5)

        ttk.Button(button_frame, text="取消", 
                  command=batch_window.destroy,
                  width=10).grid(row=0, column=2, padx=10, pady=5)

        # 提示信息
        ttk.Label(button_container, text="提示：点击'保存设置'仅保存配置，点击'确认并开始处理'将立即开始批量处理",
                 font=("TkDefaultFont", 9), foreground="#666").pack(pady=(10, 0))

        # 设置最小窗口大小
        batch_window.minsize(800, 600)

        # 更新显示
        batch_window.update()
        canvas.config(scrollregion=canvas.bbox("all"))

    def browse_folder(self, var):
        """浏览文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            var.set(folder)

    def save_batch_settings(self, window):
        """保存批量处理设置"""
        # 验证输入
        input_dir = self.input_dir_var.get()
        output_dir = self.output_dir_var.get()

        if not input_dir or not os.path.isdir(input_dir):
            messagebox.showwarning("提示", "请先选择有效的输入文件夹")
            return

        if not output_dir:
            messagebox.showwarning("提示", "请设置输出文件夹")
            return

        # 保存设置
        self.batch_settings = {
            'input_dir': input_dir,
            'output_dir': output_dir,
            'format': self.format_var.get(),
            'name_prefix': self.name_prefix_var.get(),
            'keep_original_name': self.keep_original_name.get(),
            'add_timestamp': self.add_timestamp.get(),
            'add_counter': self.add_counter.get(),
            'skip_errors': self.skip_errors.get(),
            'auto_open_output': self.auto_open_output.get()
        }

        # 启用主界面的批量处理按钮
        self.start_batch_btn.config(state=tk.NORMAL)

        messagebox.showinfo("保存成功", "批量处理设置已保存！\n\n现在可以关闭此窗口，然后在主界面点击'开始批量处理'按钮开始处理。")

    def confirm_and_start_batch(self, window):
        """确认并开始批量处理"""
        # 验证输入
        input_dir = self.input_dir_var.get()
        output_dir = self.output_dir_var.get()

        if not input_dir or not os.path.isdir(input_dir):
            messagebox.showwarning("提示", "请先选择有效的输入文件夹")
            return

        if not output_dir:
            messagebox.showwarning("提示", "请设置输出文件夹")
            return

        # 保存设置
        self.save_batch_settings(window)

        # 关闭窗口并开始处理
        window.destroy()
        self.start_batch_from_settings()

    def start_batch_from_main(self):
        """从主界面开始批量处理"""
        if not self.batch_settings:
            messagebox.showwarning("提示", "请先配置批量处理设置")
            self.open_batch_window()
            return

        self.start_batch_from_settings()

    def preview_batch_files(self, window):
        """预览批量处理文件列表"""
        input_dir = self.input_dir_var.get()

        if not input_dir or not os.path.isdir(input_dir):
            messagebox.showwarning("提示", "请先选择输入文件夹")
            return

        # 收集图片文件
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp')
        files = []
        for file in os.listdir(input_dir):
            if file.lower().endswith(supported_formats):
                files.append(file)

        if not files:
            messagebox.showwarning("提示", "输入文件夹中没有找到支持的图片文件")
            return

        # 创建预览窗口
        preview_window = tk.Toplevel(window)
        preview_window.title("文件预览")
        preview_window.geometry("400x300")

        ttk.Label(preview_window, text=f"找到 {len(files)} 个图片文件:", 
                 font=("TkDefaultFont", 10, "bold")).pack(pady=10)

        # 文件列表
        list_frame = ttk.Frame(preview_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)

        for file in files:
            listbox.insert(tk.END, file)

        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(preview_window, text="关闭", 
                  command=preview_window.destroy).pack(pady=10)

    def start_batch_from_settings(self):
        """从保存的设置开始批量处理"""
        # 检查输出文件夹
        output_dir = self.batch_settings['output_dir']
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建输出文件夹:\n{str(e)}")
                return
        else:
            # 检查输出文件夹是否为空
            if os.listdir(output_dir):
                response = messagebox.askyesno("提示", 
                    "输出文件夹不为空，继续处理可能会覆盖同名文件。\n是否继续？")
                if not response:
                    return

        # 收集图片文件
        input_dir = self.batch_settings['input_dir']
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp')
        files = []
        for file in os.listdir(input_dir):
            if file.lower().endswith(supported_formats):
                files.append(os.path.join(input_dir, file))

        if not files:
            messagebox.showerror("错误", "输入文件夹中没有找到支持的图片文件")
            return

        self.batch_files = files

        # 开始批量处理
        self.start_batch_thread(output_dir)

    def start_batch_thread(self, output_dir):
        """启动批量处理线程"""
        if self.batch_processing:
            messagebox.showwarning("提示", "批量处理正在进行中")
            return

        # 重置进度
        self.batch_progress_var.set(0)
        self.batch_status_var.set("准备中...")
        self.stop_batch_btn.config(state=tk.NORMAL)

        # 在新线程中开始批量处理
        self.batch_thread = threading.Thread(
            target=self.process_batch_thread, 
            args=(output_dir,),
            daemon=True
        )
        self.batch_processing = True
        self.batch_thread.start()

        # 启动进度监控
        self.root.after(100, self.update_batch_progress)

    def update_batch_progress(self):
        """更新批量处理进度"""
        if self.batch_processing:
            self.root.after(100, self.update_batch_progress)
        else:
            self.stop_batch_btn.config(state=tk.DISABLED)

    def process_batch_thread(self, output_dir):
        """批量处理线程"""
        try:
            total_files = len(self.batch_files)
            success_count = 0
            error_files = []

            for i, input_path in enumerate(self.batch_files):
                if not self.batch_processing:
                    break

                try:
                    # 更新进度
                    progress = (i + 1) / total_files * 100
                    self.batch_status_var.set(f"处理中: {i+1}/{total_files}")

                    # 处理单个文件
                    output_path = self.get_batch_output_path(input_path, output_dir, i+1)
                    success = self.process_single_file(input_path, output_path)

                    if success:
                        success_count += 1
                    else:
                        error_files.append(os.path.basename(input_path))

                except Exception as e:
                    error_files.append(f"{os.path.basename(input_path)}: {str(e)}")
                    if not self.batch_settings.get('skip_errors', True):
                        break

            # 处理完成
            self.batch_processing = False
            result = {
                'total': total_files,
                'success': success_count,
                'errors': error_files,
                'output_dir': output_dir
            }

            self.root.after(0, self.show_batch_result, result)

        except Exception as e:
            self.batch_processing = False
            self.root.after(0, lambda: messagebox.showerror("批量处理错误", f"处理过程中出错:\n{str(e)}"))

    def get_batch_output_path(self, input_path, output_dir, counter):
        """获取批量处理的输出路径"""
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)

        # 确定扩展名
        if self.batch_settings.get('format') == "JPEG":
            ext = ".jpg"
        elif self.batch_settings.get('format') == "PNG":
            ext = ".png"

        # 构建新文件名
        new_name = self.batch_settings.get('name_prefix', 'processed_')

        if self.batch_settings.get('keep_original_name', True):
            new_name += name

        if self.batch_settings.get('add_timestamp', False):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name += f"_{timestamp}"

        if self.batch_settings.get('add_counter', True):
            new_name += f"_{counter:03d}"

        new_name += ext

        return os.path.join(output_dir, new_name)

    def process_single_file(self, input_path, output_path):
        """处理单个文件"""
        try:
            # 打开图片
            pil_image = Image.open(input_path)

            # 计算裁剪框
            crop_rect = self.calculate_crop_rect(
                pil_image,
                self.target_width.get(),
                self.target_height.get(),
                self.horizontal_center.get(),
                self.vertical_center.get()
            )

            # 裁剪并调整尺寸
            cropped = pil_image.crop(crop_rect)
            target_size = (self.target_width.get(), self.target_height.get())

            if cropped.size != target_size:
                cropped = cropped.resize(target_size, Image.Resampling.LANCZOS)

            # 设置DPI并保存
            dpi = self.target_dpi.get()
            cropped.info['dpi'] = (dpi, dpi)

            if output_path.lower().endswith('.png'):
                cropped.save(output_path, 'PNG', dpi=(dpi, dpi))
            else:
                cropped.save(output_path, 'JPEG', quality=95, dpi=(dpi, dpi))

            return True

        except Exception as e:
            print(f"处理文件 {input_path} 出错: {e}")
            return False

    def calculate_crop_rect(self, pil_image, target_width, target_height, horizontal_center, vertical_center):
        """计算裁剪框"""
        img_width, img_height = pil_image.size

        # 计算目标比例和原图比例
        target_ratio = target_width / target_height
        img_ratio = img_width / img_height

        # 计算裁剪框尺寸
        if abs(img_ratio - target_ratio) < 0.01:
            # 比例相同，可以直接缩放
            scale_w = target_width / img_width
            scale_h = target_height / img_height
            scale = min(scale_w, scale_h)
            crop_width = int(target_width / scale)
            crop_height = int(target_height / scale)
        elif img_ratio > target_ratio:
            # 原图更宽，裁剪宽度
            crop_height = img_height
            crop_width = int(crop_height * target_ratio)
            if crop_width > img_width:
                crop_width = img_width
                crop_height = int(crop_width / target_ratio)
        else:
            # 原图更高，裁剪高度
            crop_width = img_width
            crop_height = int(crop_width / target_ratio)
            if crop_height > img_height:
                crop_height = img_height
                crop_width = int(crop_height * target_ratio)

        # 应用居中选项
        if horizontal_center:
            x1 = max(0, (img_width - crop_width) // 2)
        else:
            x1 = 0

        if vertical_center:
            y1 = max(0, (img_height - crop_height) // 2)
        else:
            y1 = 0

        x2 = x1 + crop_width
        y2 = y1 + crop_height

        # 确保裁剪框在图片范围内
        if x2 > img_width:
            x1 = img_width - crop_width
            x2 = img_width

        if y2 > img_height:
            y1 = img_height - crop_height
            y2 = img_height

        return (int(x1), int(y1), int(x2), int(y2))

    def show_batch_result(self, result):
        """显示批量处理结果"""
        self.batch_progress_var.set(100)
        self.batch_status_var.set(f"完成: {result['success']}/{result['total']} 成功")

        message = f"批量处理完成！\n\n"
        message += f"总文件数: {result['total']}\n"
        message += f"成功处理: {result['success']}\n"
        message += f"失败: {len(result['errors'])}\n"

        if result['errors']:
            message += f"\n失败文件:\n"
            for error in result['errors'][:5]:
                message += f"  • {error}\n"
            if len(result['errors']) > 5:
                message += f"  ...还有 {len(result['errors']) - 5} 个\n"

        message += f"\n输出文件夹: {result['output_dir']}"

        # 询问是否打开输出文件夹
        if result['success'] > 0 and self.batch_settings.get('auto_open_output', True):
            response = messagebox.askyesno("批量处理完成", f"{message}\n\n是否打开输出文件夹？")
            if response:
                try:
                    import subprocess
                    import sys
                    if sys.platform == "win32":
                        os.startfile(result['output_dir'])
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", result['output_dir']])
                    else:
                        subprocess.Popen(["xdg-open", result['output_dir']])
                except Exception as e:
                    print(f"打开文件夹失败: {e}")
        else:
            messagebox.showinfo("批量处理完成", message)

    def stop_batch_processing(self):
        """停止批量处理"""
        if self.batch_processing:
            self.batch_processing = False
            self.batch_status_var.set("正在停止...")

    # ====== 单张处理功能 ======

    def set_standard_size(self, size):
        """设置标准尺寸"""
        self.target_width.set(size[0])
        self.target_height.set(size[1])
        self.update_crop_rect()

    def open_single_image(self):
        """打开单张图片"""
        filetypes = [
            ("图片文件", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("所有文件", "*.*")
        ]

        filename = filedialog.askopenfilename(
            title="选择图片",
            filetypes=filetypes
        )

        if not filename:
            return

        try:
            self.pil_image = Image.open(filename)
            self.calculate_smart_crop()
            self.update_display()
            self.status_var.set(f"已打开: {os.path.basename(filename)}")
            self.update_calculation_info()

        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片:\n{str(e)}")

    def calculate_smart_crop(self):
        """智能计算裁剪策略"""
        if self.pil_image is None:
            return

        img_width, img_height = self.pil_image.size

        # 使用静态方法计算裁剪框
        self.crop_rect = self.calculate_crop_rect(
            self.pil_image,
            self.target_width.get(),
            self.target_height.get(),
            self.horizontal_center.get(),
            self.vertical_center.get()
        )

    def update_crop_rect(self):
        """更新裁剪框"""
        if self.pil_image is not None:
            self.calculate_smart_crop()
            self.update_display()
            self.update_calculation_info()

    def update_calculation_info(self):
        """更新计算信息"""
        if self.pil_image is None or self.crop_rect is None:
            return

        img_width, img_height = self.pil_image.size
        x1, y1, x2, y2 = self.crop_rect
        crop_width = x2 - x1
        crop_height = y2 - y1

        scale_x = self.target_width.get() / crop_width
        scale_y = self.target_height.get() / crop_height

        info = f"原图: {img_width}×{img_height} | "
        info += f"裁剪区域: {crop_width}×{crop_height} | "
        info += f"缩放比例: {scale_x:.2f}×{scale_y:.2f}"

        if abs(scale_x - scale_y) > 0.01:
            info += " | 注意: 宽高缩放比例不同，图片将被拉伸"

        self.calc_var.set(info)

    def update_display(self):
        """更新显示"""
        if self.pil_image is None:
            return

        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        img_width, img_height = self.pil_image.size

        # 计算缩放比例
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale_factor = min(scale_x, scale_y, 1.0)

        self.display_width = int(img_width * self.scale_factor)
        self.display_height = int(img_height * self.scale_factor)

        # 计算显示位置
        self.display_offset_x = (canvas_width - self.display_width) // 2
        self.display_offset_y = (canvas_height - self.display_height) // 2

        # 缩放图片用于显示
        display_img = self.pil_image.resize(
            (self.display_width, self.display_height),
            Image.Resampling.LANCZOS
        )

        self.display_image = ImageTk.PhotoImage(display_img)

        # 在画布上显示图片
        self.canvas.create_image(
            self.display_offset_x, self.display_offset_y,
            anchor=tk.NW,
            image=self.display_image
        )

        # 绘制裁剪框
        if self.crop_rect is not None:
            self.draw_crop_rect()

    def draw_crop_rect(self):
        """绘制裁剪框和遮罩"""
        if self.crop_rect is None:
            return

        x1, y1, x2, y2 = self.crop_rect

        # 转换为显示坐标
        display_x1 = self.display_offset_x + int(x1 * self.scale_factor)
        display_y1 = self.display_offset_y + int(y1 * self.scale_factor)
        display_x2 = self.display_offset_x + int(x2 * self.scale_factor)
        display_y2 = self.display_offset_y + int(y2 * self.scale_factor)

        # 绘制裁剪框
        self.canvas.create_rectangle(
            display_x1, display_y1, display_x2, display_y2,
            fill="",
            outline="#FF0000",
            width=2,
            dash=(5, 3),
            tags="crop_rect"
        )

        # 绘制遮罩
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # 上遮罩
        if display_y1 > 0:
            self.canvas.create_rectangle(
                0, 0, canvas_width, display_y1,
                fill="black",
                stipple="gray12",
                tags="mask"
            )

        # 下遮罩
        if display_y2 < canvas_height:
            self.canvas.create_rectangle(
                0, display_y2, canvas_width, canvas_height,
                fill="black",
                stipple="gray12",
                tags="mask"
            )

        # 左遮罩
        if display_x1 > 0:
            self.canvas.create_rectangle(
                0, display_y1, display_x1, display_y2,
                fill="black",
                stipple="gray12",
                tags="mask"
            )

        # 右遮罩
        if display_x2 < canvas_width:
            self.canvas.create_rectangle(
                display_x2, display_y1, canvas_width, display_y2,
                fill="black",
                stipple="gray12",
                tags="mask"
            )

    def start_drag(self, event):
        """开始拖动裁剪框"""
        if self.crop_rect is None:
            return

        x1, y1, x2, y2 = self.crop_rect
        display_x1 = self.display_offset_x + int(x1 * self.scale_factor)
        display_y1 = self.display_offset_y + int(y1 * self.scale_factor)
        display_x2 = self.display_offset_x + int(x2 * self.scale_factor)
        display_y2 = self.display_offset_y + int(y2 * self.scale_factor)

        if (display_x1 <= event.x <= display_x2 and
            display_y1 <= event.y <= display_y2):

            self.is_dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.crop_start_x = x1
            self.crop_start_y = y1

            self.drag_horizontal = not self.horizontal_center.get()
            self.drag_vertical = not self.vertical_center.get()

    def drag_crop(self, event):
        """拖动裁剪框"""
        if not self.is_dragging or self.crop_rect is None:
            return

        delta_x = (event.x - self.drag_start_x) / self.scale_factor
        delta_y = (event.y - self.drag_start_y) / self.scale_factor

        new_x = self.crop_start_x
        new_y = self.crop_start_y

        if self.drag_horizontal:
            new_x += delta_x

        if self.drag_vertical:
            new_y += delta_y

        x1, y1, x2, y2 = self.crop_rect
        crop_width = x2 - x1
        crop_height = y2 - y1

        img_width, img_height = self.pil_image.size

        new_x = max(0, min(new_x, img_width - crop_width))
        new_y = max(0, min(new_y, img_height - crop_height))

        self.crop_rect = (int(new_x), int(new_y), 
                         int(new_x + crop_width), int(new_y + crop_height))

        self.update_display()

    def stop_drag(self, event):
        """停止拖动"""
        self.is_dragging = False

    def reset_position(self):
        """重置裁剪框位置"""
        if self.pil_image is None:
            return

        self.update_crop_rect()

    def on_canvas_resize(self, event):
        """画布大小变化事件"""
        self.update_display()

    def save_crop(self):
        """保存单张裁剪结果"""
        if self.pil_image is None or self.crop_rect is None:
            messagebox.showwarning("警告", "请先打开并设置裁剪区域")
            return

        filetypes = [
            ("JPEG文件", "*.jpg"),
            ("PNG文件", "*.png"),
            ("所有文件", "*.*")
        ]

        target_width = self.target_width.get()
        target_height = self.target_height.get()
        default_name = f"证件照_{target_width}x{target_height}.jpg"

        filename = filedialog.asksaveasfilename(
            title="保存裁剪图片",
            defaultextension=".jpg",
            initialfile=default_name,
            filetypes=filetypes
        )

        if not filename:
            return

        try:
            # 从原图裁剪
            x1, y1, x2, y2 = self.crop_rect
            cropped = self.pil_image.crop((x1, y1, x2, y2))

            # 调整到目标尺寸
            target_size = (target_width, target_height)
            if cropped.size != target_size:
                cropped = cropped.resize(target_size, Image.Resampling.LANCZOS)

            # 设置DPI
            dpi = self.target_dpi.get()
            cropped.info['dpi'] = (dpi, dpi)

            # 保存图片
            if filename.lower().endswith('.png'):
                cropped.save(filename, 'PNG', dpi=(dpi, dpi))
            else:
                cropped.save(filename, 'JPEG', quality=95, dpi=(dpi, dpi))

            self.status_var.set(f"已保存: {os.path.basename(filename)}")

            messagebox.showinfo(
                "成功", 
                f"图片已保存为:\n{filename}\n"
                f"尺寸: {target_width}×{target_height}像素\n"
                f"DPI: {dpi}"
            )

        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{str(e)}")

def main():
    """主函数"""
    root = tk.Tk()

    # 设置窗口图标
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass

    # 创建应用
    app = SmartBatchCropApp(root)

    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    # 检查依赖
    try:
        from PIL import Image, ImageTk
    except ImportError as e:
        print(f"缺少依赖库: {e}")
        print("请安装: pip install pillow")
        import sys
        sys.exit(1)

    main()