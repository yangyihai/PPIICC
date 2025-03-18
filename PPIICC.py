import tkinter as tk
from tkinter import Canvas, Button
from PIL import Image, ImageTk, ImageChops
import pyautogui
import keyboard
import time
import numpy as np
import os

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
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        self.confirm_button = Button(self.root, text="确认", command=self.on_confirm, bg="#4CAF50", fg="white", padx=10, pady=5)
        self.cancel_button = Button(self.root, text="取消", command=self.on_cancel, bg="#F44336", fg="white", padx=10, pady=5)
    
    def on_press(self, event):
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.confirm_button.place_forget()
            self.cancel_button.place_forget()
        
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.selection_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            fill='white', stipple='gray50', outline=''
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
        # a获取当前屏幕
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
        # 修改保存路径为当前代码所在文件夹，根据需求修改点2
        save_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 生成文件名
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(save_dir, f"长截图_{timestamp}.png")
        
        full_image.save(filename)
        print(f"长截图已保存: {filename}")
        return filename
    return None

def main():
    print("长截图工具启动")
    print("请框选要截图的区域，然后点击确认按钮")
    
    # 选择区域
    selector = RegionSelector()
    region = selector.get_region()
    
    if region:
        print("开始生成长截图...")
        auto_screenshot(region)
    else:
        print("已取消")

if __name__ == "__main__":
    main()