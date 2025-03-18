import tkinter as tk
from tkinter import Canvas, Button, Frame, Label
from PIL import Image, ImageTk, ImageChops
import pyautogui
import keyboard
import time
import numpy as np
import os
import sys
import threading
import webbrowser
import pystray
from pystray import MenuItem as item

class LongScreenshotTool:
    def __init__(self):
        # 应用程序图标 - 使用BASE64编码存储简单图标
        self.icon_data = """
        iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA
        dgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAB+SURBVDiNY/z/
        //9/BkoAExTjDKxZs2Y2IyPjfCCTgQLwHyj+CoaBGDDhcAdBgM0Asr2AywBCgGwDsLqAFAM+fPjwf9Wq
        VSKM5AYiIyMjAyO5ocDIyAi3ZdSAUQNGDRjaBhA9M5HihaevXr1iYGBgYCTVC7gMIMcLDAwMAMXHIUG4
        JlgmAAAAAElFTkSuQmCC
        """
        
        # 保存最新截图路径
        self.last_screenshot = None
        
        # 创建托盘图标
        self.create_tray_icon()

    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 从BASE64解码图标
    
        icon_data = self.icon_data.encode('ascii')
        import base64
        import io
        icon_image = Image.open(io.BytesIO(base64.b64decode(icon_data)))
        
        # 创建托盘菜单项
        menu = (
            item('开始截图', self.start_screenshot),
            item('查看最近截图', self.open_last_screenshot),
            item('退出', self.quit_app)
        )
        
        # 创建并运行托盘图标
        self.tray_icon = pystray.Icon("长截图工具", icon_image, "长截图工具", menu)
        self.tray_icon.run_detached()
        
        # 首次运行显示欢迎窗口
        self.show_welcome()

    def show_welcome(self):
        """显示欢迎窗口"""
        self.welcome = tk.Tk()
        self.welcome.title("长截图工具")
        self.welcome.geometry("320x200")
        self.welcome.resizable(False, False)
        
        # 设置居中
        self.welcome.update_idletasks()
        width = self.welcome.winfo_width()
        height = self.welcome.winfo_height()
        x = (self.welcome.winfo_screenwidth() // 2) - (width // 2)
        y = (self.welcome.winfo_screenheight() // 2) - (height // 2)
        self.welcome.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        frame = Frame(self.welcome, padx=20, pady=20)
        frame.pack(expand=True, fill=tk.BOTH)
        
        Label(frame, text="长截图工具", font=("Arial", 16, "bold")).pack(pady=(0, 10))
        Label(frame, text="本工具可以方便地制作网页长截图").pack()
        Label(frame, text="点击下方按钮开始，或通过系统托盘图标访问").pack(pady=(5, 15))
        
        start_button = Button(frame, text="开始截图", command=self.start_from_welcome, bg="#4CAF50", fg="white", padx=10, pady=5)
        start_button.pack()
        
        # 底部提示信息
        footer = Label(self.welcome, text="提示：本工具已在系统托盘中运行", fg="gray")
        footer.pack(side=tk.BOTTOM, pady=5)
        
        self.welcome.mainloop()

    def start_from_welcome(self):
        """从欢迎窗口启动截图"""
        self.welcome.destroy()
        self.start_screenshot()

    def start_screenshot(self):
        """开始截图流程"""
        # 选择区域
        selector = RegionSelector()
        region = selector.get_region()
        
        if region:
            # 在新线程中执行截图，以避免阻塞UI
            threading.Thread(target=self.do_screenshot, args=(region,)).start()

    def do_screenshot(self, region):
        """执行截图逻辑"""
        print("开始生成长截图...")
        self.last_screenshot = auto_screenshot(region)
        
        # 截图完成后显示通知窗口
        if self.last_screenshot:
            self.show_notification()

    def show_notification(self):
        """显示截图完成通知"""
        notif = tk.Tk()
        notif.title("截图完成")
        notif.geometry("300x100")
        notif.resizable(False, False)
        
        # 设置窗口在屏幕右下角
        notif.update_idletasks()
        width = notif.winfo_width()
        height = notif.winfo_height()
        x = notif.winfo_screenwidth() - width - 20
        y = notif.winfo_screenheight() - height - 60
        notif.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        frame = Frame(notif, padx=15, pady=15)
        frame.pack(expand=True, fill=tk.BOTH)
        
        Label(frame, text="长截图已保存!").pack(pady=(0, 10))
        
        btn_frame = Frame(frame)
        btn_frame.pack()
        
        Button(btn_frame, text="查看截图", command=lambda: self.open_screenshot_and_close(notif)).pack(side=tk.LEFT, padx=5)
        Button(btn_frame, text="关闭", command=notif.destroy).pack(side=tk.LEFT, padx=5)
        
        # 5秒后自动关闭
        notif.after(5000, notif.destroy)
        
        notif.mainloop()

    def open_screenshot_and_close(self, window):
        """打开截图并关闭通知窗口"""
        window.destroy()
        self.open_last_screenshot()
    
    def open_last_screenshot(self):
        """打开最近一次截图"""
        if self.last_screenshot and os.path.exists(self.last_screenshot):
            webbrowser.open(self.last_screenshot)
        else:
            self.show_error("找不到最近的截图")
    
    def show_error(self, message):
        """显示错误消息"""
        error = tk.Tk()
        error.title("错误")
        error.geometry("250x100")
        error.resizable(False, False)
        
        # 居中显示
        error.update_idletasks()
        width = error.winfo_width()
        height = error.winfo_height()
        x = (error.winfo_screenwidth() // 2) - (width // 2)
        y = (error.winfo_screenheight() // 2) - (height // 2)
        error.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        frame = Frame(error, padx=15, pady=15)
        frame.pack(expand=True, fill=tk.BOTH)
        
        Label(frame, text=message).pack(pady=(0, 10))
        Button(frame, text="确定", command=error.destroy).pack()
        
        error.mainloop()
    
    def quit_app(self):
        """退出应用"""
        self.tray_icon.stop()
        sys.exit(0)


# 原有的区域选择器类
class RegionSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("区域选择")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.2)
        self.root.attributes('-topmost', True)
        
        self.canvas = Canvas(self.root, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.start_x = None
        self.start_y = None
        self.selection_rect = None
        self.region = None
        
        # 添加帮助提示
        self.help_text = self.canvas.create_text(
            self.root.winfo_screenwidth()//2,
            50,
            text="请框选要截图的区域，按ESC键取消",
            fill="black",
            font=("Arial", 16, "bold")
        )
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        # 使用现代风格的按钮
        self.confirm_button = Button(self.root, text="确认", command=self.on_confirm, 
                                    bg="#4CAF50", fg="white", font=("Arial", 10), 
                                    relief=tk.RAISED, padx=10, pady=5)
        self.cancel_button = Button(self.root, text="取消", command=self.on_cancel, 
                                   bg="#F44336", fg="white", font=("Arial", 10), 
                                   relief=tk.RAISED, padx=10, pady=5)
    
    def on_press(self, event):
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.confirm_button.place_forget()
            self.cancel_button.place_forget()
        
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.selection_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            fill='white', stipple='gray50', outline='blue', width=2
        )
    
    def on_drag(self, event):
        current_x = self.canvas.canvasx(event.x)
        current_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.selection_rect, self.start_x, self.start_y, current_x, current_y)
    
    def on_release(self, event):
        current_x = self.canvas.canvasx(event.x)
        current_y = self.canvas.canvasy(event.y)
        
        if abs(current_x - self.start_x) < 5 or abs(current_y - self.start_y) < 5:
            return
        
        x1, y1 = min(self.start_x, current_x), min(self.start_y, current_y)
        x2, y2 = max(self.start_x, current_x), max(self.start_y, current_y)
        self.region = (int(x1), int(y1), int(x2-x1), int(y2-y1))
        
        # 显示选区大小信息
        self.canvas.create_text(
            (x1 + x2) / 2,
            y1 - 10,
            text=f"大小: {int(x2-x1)}x{int(y2-y1)}",
            fill="black",
            font=("Arial", 10)
        )
        
        button_y = y2 + 10 if y2 + 50 < self.root.winfo_height() else y1 - 40
        self.confirm_button.place(x=x1, y=button_y)
        self.cancel_button.place(x=x1 + 70, y=button_y)
    
    def on_confirm(self):
        self.root.quit()
    
    def on_cancel(self):
        self.region = None
        self.canvas.delete(self.selection_rect)
        self.selection_rect = None
        self.confirm_button.place_forget()
        self.cancel_button.place_forget()
    
    def get_region(self):
        self.root.mainloop()
        try:
            self.root.destroy()
        except:
            pass
        return self.region


# 原有的截图功能
def is_bottom_reached(img1, img2, threshold=0.95):
    """检查两张图片是否几乎相同（判断是否已到页面底部）"""
    diff = ImageChops.difference(img1, img2)
    diff_stats = ImageChops.difference(img1, img2).getbbox()
    if diff_stats is None:  # 完全相同
        return True
    
    # 计算差异区域占比
    total_pixels = img1.width * img1.height
    diff_pixels = np.sum(np.array(diff) > 0)
    similarity = 1 - (diff_pixels / (total_pixels * 3))  # 3通道
    
    return similarity > threshold


def auto_screenshot(region):
    x, y, w, h = region
    print(f"截图区域：{x},{y} {w}x{h}")
    
    # 初始化变量
    full_image = None
    last_image = None
    scroll_step = min(h // 3, 100)  # 滚动步长默认为区域高度的1/3，最大为100像素
    consecutive_no_change = 0
    max_attempts = 3  # 连续几次无变化则认为已到底
    
    # 不再点击区域中间以获取焦点，根据需求修改点1
    print("开始截图滚动...")
    
    while consecutive_no_change < max_attempts:
        # 获取当前屏幕
        current_img = pyautogui.screenshot(region=(x, y, w, h))
        
        # 第一次截图
        if full_image is None:
            full_image = current_img
            last_image = current_img
            
            # 执行滚动
            pyautogui.scroll(-scroll_step)
            time.sleep(0.8)  # 等待滚动完成和页面加载
            continue
        
        # 检查是否滚动到底（与上一次截图比较）
        if is_bottom_reached(current_img, last_image):
            consecutive_no_change += 1
            print(f"检测到页面无变化 ({consecutive_no_change}/{max_attempts})")
            
            if consecutive_no_change == 1:
                # 第一次检测到无变化，减小滚动步长再试
                new_scroll_step = max(10, scroll_step // 2)
                if new_scroll_step != scroll_step:
                    scroll_step = new_scroll_step
                    print(f"减小滚动步长为 {scroll_step}")
                    consecutive_no_change = 0
        else:
            consecutive_no_change = 0
            
            # 计算重叠区域
            overlap = 0
            for i in range(min(h, 150), 0, -1):  # 从底部向上最多150像素查找匹配
                if ImageChops.difference(
                    last_image.crop((0, h-i, w, h)),
                    current_img.crop((0, 0, w, i))
                ).getbbox() is None:
                    overlap = i
                    break
            
            # 拼接图像
            if overlap > 0:
                new_part = current_img.crop((0, overlap, w, h))
                new_full = Image.new('RGB', (w, full_image.height + h - overlap))
                new_full.paste(full_image, (0, 0))
                new_full.paste(new_part, (0, full_image.height))
                full_image = new_full
                print(f"找到重叠区域: {overlap}px，当前长图高度: {full_image.height}px")
            else:
                # 没找到重叠，直接添加到底部
                new_full = Image.new('RGB', (w, full_image.height + h))
                new_full.paste(full_image, (0, 0))
                new_full.paste(current_img, (0, full_image.height))
                full_image = new_full
                print(f"未找到重叠区域，当前长图高度: {full_image.height}px")
        
        # 保存上一个图像
        last_image = current_img
        
        # 执行滚动
        pyautogui.scroll(-scroll_step)
        time.sleep(0.8)  # 等待滚动完成和页面加载
        
        # 检查ESC键是否被按下
        if keyboard.is_pressed('esc'):
            print("用户取消截图")
            break
    
    print("截图完成")
    
    # 保存长截图
    if full_image:
        # 保存到代码所在文件夹
        save_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 生成文件名
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(save_dir, f"长截图_{timestamp}.png")
        
        full_image.save(filename)
        print(f"长截图已保存: {filename}")
        return filename
    return None


def main():
    """主函数启动桌面应用"""
    app = LongScreenshotTool()
    
    # 保持程序运行
    try:
        # 使用一个简单的循环来保持程序运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.quit_app()


if __name__ == "__main__":
    main()