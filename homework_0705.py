import cv2
import numpy as np

class TargetTracker:
    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.start_frame = self.total_frames // 2  # 后半段开始帧
        self.roi = None
        self.roi_hist = None
        self.target_color_rgb = None
        self.target_color_hsv = None
        
    def select_roi(self, frame):
        """让用户选择感兴趣区域"""
        roi = cv2.selectROI("Select Target", frame, False)
        cv2.destroyWindow("Select Target")
        return roi
    
    def rgb_tracking(self, frame, threshold=30):
        """RGB颜色空间跟踪"""
        if self.target_color_rgb is None:
            return frame, np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
        
        # 创建与frame相同大小的目标颜色图像
        target_image = np.full_like(frame, self.target_color_rgb)
        
        # 计算与目标颜色的差异
        diff = cv2.absdiff(frame, target_image)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # 创建掩码
        _, mask = cv2.threshold(gray_diff, threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 形态学操作改善掩码
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 泛洪填充效果
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            # 找到最大轮廓
            largest_contour = max(contours, key=cv2.contourArea)
            flood_mask = np.zeros_like(mask)
            cv2.drawContours(flood_mask, [largest_contour], -1, 255, -1)
            
            # 应用到原图
            result = cv2.bitwise_and(frame, frame, mask=flood_mask)
            return result, flood_mask
        
        return frame, mask
    
    def hsv_tracking(self, frame, h_range=10, s_range=50, v_range=50):
        """HSV颜色空间跟踪"""
        if self.target_color_hsv is None:
            return None
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 定义HSV范围
        lower = np.array([
            self.target_color_hsv[0] - h_range,
            max(0, self.target_color_hsv[1] - s_range),
            max(0, self.target_color_hsv[2] - v_range)
        ])
        upper = np.array([
            self.target_color_hsv[0] + h_range,
            min(255, self.target_color_hsv[1] + s_range),
            min(255, self.target_color_hsv[2] + v_range)
        ])
        
        # 处理H通道的循环性
        if lower[0] < 0:
            lower[0] = 0
            mask1 = cv2.inRange(hsv, lower, upper)
            lower2 = np.array([180 + (self.target_color_hsv[0] - h_range), lower[1], lower[2]])
            upper2 = np.array([180, upper[1], upper[2]])
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
        elif upper[0] > 180:
            upper[0] = 180
            mask1 = cv2.inRange(hsv, lower, upper)
            lower2 = np.array([0, lower[1], lower[2]])
            upper2 = np.array([upper[0] - 180, upper[1], upper[2]])
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv, lower, upper)
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 泛洪填充效果
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            flood_mask = np.zeros_like(mask)
            cv2.drawContours(flood_mask, [largest_contour], -1, 255, -1)
            
            result = cv2.bitwise_and(frame, frame, mask=flood_mask)
            return result, flood_mask
        
        return frame, mask
    
    def histogram_backprojection(self, frame):
        """直方图反投影跟踪"""
        if self.roi_hist is None:
            return None
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 计算反投影
        backproj = cv2.calcBackProject([hsv], [0, 1], self.roi_hist, [0, 180, 0, 256], 1)
        
        # 使用圆形卷积核进行卷积
        disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        backproj = cv2.filter2D(backproj, -1, disc)
        
        # 阈值化
        _, thresh = cv2.threshold(backproj, 50, 255, cv2.THRESH_BINARY)
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 泛洪填充效果
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            flood_mask = np.zeros_like(thresh)
            cv2.drawContours(flood_mask, [largest_contour], -1, 255, -1)
            
            result = cv2.bitwise_and(frame, frame, mask=flood_mask)
            return result, flood_mask
        
        return frame, thresh
    
    def initialize_target(self, frame, roi):
        """初始化目标信息"""
        x, y, w, h = roi
        roi_frame = frame[y:y+h, x:x+w]
        
        # RGB颜色信息 - 计算平均颜色
        mean_color = cv2.mean(roi_frame)[:3]
        self.target_color_rgb = np.array(mean_color, dtype=np.uint8)
        
        # HSV颜色信息
        roi_hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
        self.target_color_hsv = cv2.mean(roi_hsv)[:3]
        
        # 计算直方图
        roi_hist = cv2.calcHist([roi_hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
        self.roi_hist = cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
    
    def run(self):
        """主运行函数"""
        # 跳转到视频后半段
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        
        # 读取第一帧用于选择ROI
        ret, first_frame = self.cap.read()
        if not ret:
            print("无法读取视频")
            return
        
        # 选择ROI
        print("请在窗口中选择要跟踪的目标区域，然后按Enter或Space确认")
        roi = self.select_roi(first_frame)
        if roi[2] == 0 or roi[3] == 0:
            print("未选择有效区域")
            return
        
        # 初始化目标
        self.initialize_target(first_frame, roi)
        
        # 创建窗口
        cv2.namedWindow("Original", cv2.WINDOW_NORMAL)
        cv2.namedWindow("RGB Tracking", cv2.WINDOW_NORMAL)
        cv2.namedWindow("HSV Tracking", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Histogram Backprojection", cv2.WINDOW_NORMAL)
        
        # 重新设置到后半段开始
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # 执行三种跟踪方法
            rgb_result, rgb_mask = self.rgb_tracking(frame.copy())
            hsv_result, hsv_mask = self.hsv_tracking(frame.copy())
            hist_result, hist_mask = self.histogram_backprojection(frame.copy())
            
            # 显示结果
            cv2.imshow("Original", frame)
            cv2.imshow("RGB Tracking", rgb_result)
            cv2.imshow("HSV Tracking", hsv_result)
            cv2.imshow("Histogram Backprojection", hist_result)
            
            # 按'q'退出，按's'保存当前帧结果
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                cv2.imwrite("rgb_tracking.jpg", rgb_result)
                cv2.imwrite("hsv_tracking.jpg", hsv_result)
                cv2.imwrite("hist_tracking.jpg", hist_result)
                print("结果已保存")
        
        self.cap.release()
        cv2.destroyAllWindows()

def main():
    # 使用视频文件
    video_path = "video_006.mp4"
    tracker = TargetTracker(video_path)
    tracker.run()

if __name__ == "__main__":
    main()