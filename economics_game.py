import pygame
import sys
import math
import random
from pygame.locals import *

# 初始化pygame
pygame.init()
pygame.font.init()

# 屏幕设置
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("税收与公共支出经济模拟游戏")

# 颜色定义
BACKGROUND = (25, 40, 65)
PANEL_BG = (40, 60, 90)
HEADER_BG = (30, 100, 170)
BUTTON_BG = (50, 150, 200)
BUTTON_HOVER = (70, 170, 230)
BUTTON_ACTIVE = (90, 190, 250)
TEXT_COLOR = (220, 240, 255)
HIGHLIGHT = (255, 215, 80)
WARNING = (255, 100, 100)
POSITIVE = (100, 255, 150)
NEGATIVE = (255, 150, 100)
GRID_COLOR = (60, 90, 120)

# 字体
title_font = pygame.font.SysFont("simhei", 36, bold=True)
header_font = pygame.font.SysFont("simhei", 28, bold=True)
normal_font = pygame.font.SysFont("simhei", 22)
small_font = pygame.font.SysFont("simhei", 18)

class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        self.active = False
        
    def draw(self, surface):
        color = BUTTON_ACTIVE if self.active else BUTTON_HOVER if self.hovered else BUTTON_BG
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, TEXT_COLOR, self.rect, 2, border_radius=8)
        
        text_surf = normal_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.action:
                self.active = True
                return self.action()
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.active = False
        return None

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial, label, suffix="%", show_value=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.suffix = suffix
        self.show_value = show_value
        self.dragging = False
        self.handle_radius = 10
        self.handle_x = x + (initial - min_val) / (max_val - min_val) * width
        
    def draw(self, surface):
        # 绘制滑动条背景
        pygame.draw.rect(surface, PANEL_BG, self.rect, border_radius=5)
        
        # 绘制填充部分
        fill_width = (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        color = POSITIVE if self.value < (self.min_val + self.max_val) * 0.6 else NEGATIVE
        pygame.draw.rect(surface, color, fill_rect, border_radius=5)
        
        # 绘制标签
        label_surf = small_font.render(self.label, True, TEXT_COLOR)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 25))
        
        # 绘制值
        if self.show_value:
            value_text = f"{self.value:.1f}{self.suffix}"
            value_surf = small_font.render(value_text, True, TEXT_COLOR)
            value_rect = value_surf.get_rect(midright=(self.rect.right + 60, self.rect.centery))
            surface.blit(value_surf, value_rect)
        
        # 绘制滑块
        handle_pos = (self.handle_x, self.rect.centery)
        pygame.draw.circle(surface, HIGHLIGHT, handle_pos, self.handle_radius)
        pygame.draw.circle(surface, TEXT_COLOR, handle_pos, self.handle_radius, 2)
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(self.handle_x - self.handle_radius, 
                          self.rect.centery - self.handle_radius,
                          self.handle_radius * 2, 
                          self.handle_radius * 2).collidepoint(event.pos):
                self.dragging = True
                
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            
        elif event.type == MOUSEMOTION and self.dragging:
            self.handle_x = max(self.rect.left, min(event.pos[0], self.rect.right))
            self.value = self.min_val + (self.handle_x - self.rect.left) / self.rect.width * (self.max_val - self.min_val)
            return True
        return False

class EconomySimulator:
    def __init__(self):
        # 初始经济参数
        self.GDP = 1000.0  # 初始GDP（十亿元）
        self.tax_rates = {
            'income': 20.0,    # 个人所得税率
            'corporate': 25.0, # 公司税率
            'consumption': 15.0  # 消费税率
        }
        self.gov_spending = {
            'education': 40,   # 教育支出（十亿元）
            'infrastructure': 60,  # 基础设施建设支出
            'healthcare': 30,   # 医疗支出
            'welfare': 20      # 社会福利支出
        }
        self.budget_deficit = 0.0  # 财政赤字（十亿元）
        self.employment_rate = 95.0  # 就业率（%）
        self.welfare_index = 50.0   # 社会福利指数（0-100）
        self.inflation = 2.0      # 通货膨胀率（%）
        
        # 经济模型参数
        self.base_mpc = 0.7       # 边际消费倾向
        self.potential_growth = 3.0  # 潜在经济增长率（%）
        self.natural_unemployment = 5.0  # 自然失业率（%）
        
        # 游戏状态
        self.rounds = 0
        self.max_rounds = 10
        self.target_gdp = 2000  # 目标GDP
        self.max_deficit = 500  # 最大允许赤字
        
        # 历史记录
        self.history = {
            'GDP': [self.GDP],
            'deficit': [self.budget_deficit],
            'employment': [self.employment_rate],
            'welfare': [self.welfare_index],
            'inflation': [self.inflation]
        }
        
        # 创建UI元素
        self.create_ui_elements()
        
    def create_ui_elements(self):
        # 税收滑块
        self.tax_sliders = [
            Slider(50, 180, 300, 20, 5, 80, self.tax_rates['income'], "个人所得税", "%"),
            Slider(50, 230, 300, 20, 5, 80, self.tax_rates['corporate'], "公司税", "%"),
            Slider(50, 280, 300, 20, 5, 50, self.tax_rates['consumption'], "消费税", "%")
        ]
        
        # 支出滑块
        self.spending_sliders = [
            Slider(400, 180, 300, 20, 5, 150, self.gov_spending['education'], "教育支出", "亿"),
            Slider(400, 230, 300, 20, 5, 150, self.gov_spending['infrastructure'], "基础设施建设", "亿"),
            Slider(400, 280, 300, 20, 5, 150, self.gov_spending['healthcare'], "医疗支出", "亿"),
            Slider(400, 330, 300, 20, 5, 150, self.gov_spending['welfare'], "社会福利", "亿")
        ]
        
        # 按钮
        self.execute_button = Button(WIDTH//2 - 100, 400, 200, 50, "执行政策", self.execute_policy)
        self.reset_button = Button(WIDTH - 150, 30, 120, 40, "重新开始", self.reset_game)
        
    def reset_game(self):
        self.__init__()
        return "reset"
    
    def execute_policy(self):
        # 更新税率
        self.tax_rates['income'] = self.tax_sliders[0].value
        self.tax_rates['corporate'] = self.tax_sliders[1].value
        self.tax_rates['consumption'] = self.tax_sliders[2].value
        
        # 更新政府支出
        self.gov_spending['education'] = self.spending_sliders[0].value
        self.gov_spending['infrastructure'] = self.spending_sliders[1].value
        self.gov_spending['healthcare'] = self.spending_sliders[2].value
        self.gov_spending['welfare'] = self.spending_sliders[3].value
        
        # 计算税收变化
        tax_changes = {
            'income': (self.tax_rates['income'] - 20) / 100,
            'corporate': (self.tax_rates['corporate'] - 25) / 100,
            'consumption': (self.tax_rates['consumption'] - 15) / 100
        }
        
        # 计算支出变化
        spending_changes = {
            'education': self.gov_spending['education'] - 40,
            'infrastructure': self.gov_spending['infrastructure'] - 60,
            'healthcare': self.gov_spending['healthcare'] - 30,
            'welfare': self.gov_spending['welfare'] - 20
        }
        
        # 计算税收收入
        tax_revenue = 0
        tax_revenue += self.GDP * 0.6 * (self.tax_rates['income'] / 100)  # 假设60% GDP来自个人收入
        tax_revenue += self.GDP * 0.3 * (self.tax_rates['corporate'] / 100)  # 假设30% GDP来自企业利润
        tax_revenue += self.GDP * 0.7 * (self.tax_rates['consumption'] / 100) * 0.5  # 假设消费占GDP 70%
        
        # 计算政府支出
        total_spending = sum(self.gov_spending.values())
        
        # 计算财政赤字
        self.budget_deficit = total_spending - tax_revenue
        
        # 计算乘数效应
        # 税收乘数 (通常为负值)
        tax_multiplier = -self.base_mpc / (1 - self.base_mpc)
        # 政府支出乘数
        spending_multiplier = 1 / (1 - self.base_mpc)
        
        # 计算GDP变化
        tax_impact = (tax_changes['income'] + tax_changes['corporate'] + tax_changes['consumption']) * tax_multiplier * self.GDP
        spending_impact = sum(spending_changes.values()) * spending_multiplier
        
        # 基础增长 + 政策影响
        new_gdp = self.GDP * (1 + self.potential_growth/100) + tax_impact + spending_impact
        
        # 就业率变化 (奥肯定律简化版)
        gdp_growth = (new_gdp - self.GDP) / self.GDP * 100
        employment_change = 0.5 * (gdp_growth - self.potential_growth)
        self.employment_rate = max(85.0, min(99.0, self.employment_rate + employment_change))
        
        # 社会福利指数变化
        welfare_change = 0
        welfare_change += spending_changes['education'] * 0.2
        welfare_change += spending_changes['healthcare'] * 0.3
        welfare_change += spending_changes['welfare'] * 0.4
        welfare_change -= (tax_changes['income'] + tax_changes['corporate']) * 100
        
        self.welfare_index = max(0, min(100, self.welfare_index + welfare_change))
        
        # 通货膨胀影响
        demand_pressure = max(0, gdp_growth - self.potential_growth - 2)
        self.inflation = 2.0 + demand_pressure * 0.5
        
        # 更新GDP
        self.GDP = new_gdp
        self.rounds += 1
        
        # 更新历史记录
        self.history['GDP'].append(self.GDP)
        self.history['deficit'].append(self.budget_deficit)
        self.history['employment'].append(self.employment_rate)
        self.history['welfare'].append(self.welfare_index)
        self.history['inflation'].append(self.inflation)
        
        return "execute"
    
    def check_game_status(self):
        """检查游戏是否结束"""
        if self.rounds >= self.max_rounds:
            return False, "游戏结束！已达到最大回合数"
        
        if self.GDP >= self.target_gdp and abs(self.budget_deficit) <= self.max_deficit:
            return False, ("恭喜！你成功实现了经济增长目标 "
                          f"(GDP: ¥{self.GDP:.1f}亿)，同时维持了财政健康！")
        
        if self.budget_deficit > self.max_deficit:
            return False, ("财政危机！赤字过高 "
                          f"(¥{self.budget_deficit:.1f}亿)。游戏结束！")
        
        return True, ""
    
    def draw(self, surface):
        # 绘制背景
        surface.fill(BACKGROUND)
        
        # 绘制标题
        title_text = title_font.render("税收与公共支出经济模拟游戏", True, HIGHLIGHT)
        surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 20))
        
        # 绘制回合信息
        round_text = header_font.render(f"回合: {self.rounds+1}/{self.max_rounds}", True, TEXT_COLOR)
        surface.blit(round_text, (WIDTH - 150, 80))
        
        # 绘制目标信息
        target_text = normal_font.render(f"目标: GDP ¥{self.target_gdp}亿 | 赤字限额 ¥{self.max_deficit}亿", True, TEXT_COLOR)
        surface.blit(target_text, (50, 80))
        
        # 绘制经济指标面板
        self.draw_economy_panel(surface, 50, 450, WIDTH-100, 220)
        
        # 绘制图表
        self.draw_charts(surface, 750, 100, 220, 340)
        
        # 绘制税收面板
        pygame.draw.rect(surface, PANEL_BG, (30, 120, 360, 260), border_radius=10)
        tax_title = header_font.render("税收政策调整", True, TEXT_COLOR)
        surface.blit(tax_title, (50, 130))
        
        # 绘制支出面板
        pygame.draw.rect(surface, PANEL_BG, (380, 120, 360, 260), border_radius=10)
        spending_title = header_font.render("公共支出调整", True, TEXT_COLOR)
        surface.blit(spending_title, (400, 130))
        
        # 绘制滑块
        for slider in self.tax_sliders + self.spending_sliders:
            slider.draw(surface)
        
        # 绘制按钮
        self.execute_button.draw(surface)
        self.reset_button.draw(surface)
        
        # 绘制状态信息
        status, message = self.check_game_status()
        if not status:
            self.draw_message_box(surface, message)
    
    def draw_economy_panel(self, surface, x, y, width, height):
        pygame.draw.rect(surface, PANEL_BG, (x, y, width, height), border_radius=10)
        title = header_font.render("当前经济指标", True, TEXT_COLOR)
        surface.blit(title, (x + 20, y + 10))
        
        # 绘制指标
        indicators = [
            ("GDP", f"¥{self.GDP:.1f}亿", POSITIVE if self.GDP >= 1000 else NEGATIVE),
            ("财政赤字", f"¥{self.budget_deficit:.1f}亿", POSITIVE if self.budget_deficit <= 0 else NEGATIVE),
            ("就业率", f"{self.employment_rate:.1f}%", POSITIVE if self.employment_rate >= 90 else NEGATIVE),
            ("社会福利指数", f"{self.welfare_index:.1f}/100", POSITIVE if self.welfare_index >= 50 else NEGATIVE),
            ("通货膨胀率", f"{self.inflation:.1f}%", POSITIVE if self.inflation <= 3.0 else NEGATIVE)
        ]
        
        for i, (label, value, color) in enumerate(indicators):
            label_surf = normal_font.render(label, True, TEXT_COLOR)
            value_surf = normal_font.render(value, True, color)
            
            surface.blit(label_surf, (x + 30, y + 60 + i*35))
            surface.blit(value_surf, (x + width - value_surf.get_width() - 30, y + 60 + i*35))
    
    def draw_charts(self, surface, x, y, width, height):
        pygame.draw.rect(surface, PANEL_BG, (x, y, width, height), border_radius=10)
        title = header_font.render("经济趋势", True, TEXT_COLOR)
        surface.blit(title, (x + 20, y + 10))
        
        # 绘制网格
        grid_color = (80, 110, 140)
        for i in range(1, 5):
            pygame.draw.line(surface, grid_color, (x, y + i*height//5), (x+width, y + i*height//5), 1)
        
        # 绘制GDP图表
        if len(self.history['GDP']) > 1:
            points = []
            max_gdp = max(max(self.history['GDP']), self.target_gdp)
            min_gdp = min(min(self.history['GDP']), 800)
            
            for i, gdp in enumerate(self.history['GDP']):
                x_pos = x + 20 + i * (width - 40) / (len(self.history['GDP']) - 1)
                y_pos = y + height - 40 - (gdp - min_gdp) / (max_gdp - min_gdp) * (height - 60)
                points.append((x_pos, y_pos))
            
            # 绘制目标线
            target_y = y + height - 40 - (self.target_gdp - min_gdp) / (max_gdp - min_gdp) * (height - 60)
            pygame.draw.line(surface, HIGHLIGHT, (x, target_y), (x+width, target_y), 2)
            target_text = small_font.render(f"目标: ¥{self.target_gdp}亿", True, HIGHLIGHT)
            surface.blit(target_text, (x+width - target_text.get_width() - 10, target_y - 20))
            
            # 绘制GDP线
            if len(points) > 1:
                pygame.draw.lines(surface, POSITIVE, False, points, 3)
                
                # 绘制点
                for point in points:
                    pygame.draw.circle(surface, POSITIVE, point, 4)
            
            # 绘制标签
            gdp_text = small_font.render("GDP增长趋势", True, POSITIVE)
            surface.blit(gdp_text, (x+20, y+30))
    
    def draw_message_box(self, surface, message):
        box_width, box_height = 700, 200
        box_x, box_y = (WIDTH - box_width) // 2, (HEIGHT - box_height) // 2
        
        # 绘制半透明背景
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        surface.blit(s, (0, 0))
        
        # 绘制消息框
        pygame.draw.rect(surface, PANEL_BG, (box_x, box_y, box_width, box_height), border_radius=15)
        pygame.draw.rect(surface, HIGHLIGHT, (box_x, box_y, box_width, box_height), 3, border_radius=15)
        
        # 绘制消息文本
        lines = []
        words = message.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if normal_font.size(test_line)[0] < box_width - 50:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        
        for i, line in enumerate(lines):
            text_surf = normal_font.render(line, True, TEXT_COLOR)
            surface.blit(text_surf, (box_x + (box_width - text_surf.get_width()) // 2, 
                                   box_y + 60 + i * 35))
        
        # 绘制按钮
        restart_btn = Button(box_x + box_width//2 - 120, box_y + box_height - 60, 100, 40, "重新开始", self.reset_game)
        quit_btn = Button(box_x + box_width//2 + 20, box_y + box_height - 60, 100, 40, "退出游戏")
        
        restart_btn.draw(surface)
        quit_btn.draw(surface)
        
        return restart_btn, quit_btn

# 主游戏循环
def main():
    clock = pygame.time.Clock()
    game = EconomySimulator()
    running = True
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            # 处理滑块事件
            slider_updated = False
            for slider in game.tax_sliders + game.spending_sliders:
                if slider.handle_event(event):
                    slider_updated = True
            
            # 处理按钮事件
            if game.execute_button.handle_event(event) == "reset":
                game = EconomySimulator()
            if game.reset_button.handle_event(event) == "reset":
                game = EconomySimulator()
        
        # 更新UI状态
        game.execute_button.check_hover(mouse_pos)
        game.reset_button.check_hover(mouse_pos)
        
        # 绘制游戏
        game.draw(screen)
        
        # 绘制鼠标悬停提示
        if game.execute_button.hovered:
            pygame.draw.rect(screen, HIGHLIGHT, game.execute_button.rect, 3, border_radius=8)
            tip = small_font.render("应用当前税收和支出政策", True, HIGHLIGHT)
            screen.blit(tip, (mouse_pos[0] + 15, mouse_pos[1] + 15))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()
