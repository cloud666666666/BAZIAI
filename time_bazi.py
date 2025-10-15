#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字计算模块
基于中国农历和二十四节气的严谨八字计算
"""
import json
import os
from datetime import datetime, timedelta
import requests

# 天干地支
Gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
Zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ShengXiao = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# 时辰对应表
SHI_CHEN = {
    "子": (23, 1), "丑": (1, 3), "寅": (3, 5), "卯": (5, 7),
    "辰": (7, 9), "巳": (9, 11), "午": (11, 13), "未": (13, 15),
    "申": (15, 17), "酉": (17, 19), "戌": (19, 21), "亥": (21, 23)
}

# 二十四节气顺序
SOLAR_TERMS = [
    "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
    "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
    "立冬", "小雪", "大雪", "冬至", "小寒", "大寒"
]
def get_solar(year):
    url = "https://v3.alapi.cn/api/solarTerm"
    querystring = {"token":"ve384uvpccenbfcngnn4dopljdtih6","year":year}
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers, params=querystring, verify=False).json()
    data = response['data']
    year_data = {}
    for item in data:
        date = item['date']
        name = item['name']
        year_data[name] = date 
    # 读取现有的数据
    try:
        with open('solar_data.json', 'r', encoding='utf-8') as f:
            solar_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        solar_data = {}
    
    # 添加新年份的数据
    solar_data[str(year)] = year_data
    
    # 写回文件
    with open('solar_data.json', 'w', encoding='utf-8') as f:
        json.dump(solar_data, f, ensure_ascii=False, indent=4)
    print("调用api获取节气数据成功")
    return year_data 
def load_solar_data():
    with open('solar_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)
def get_hour_pillar(hour):
    """根据小时获取时柱"""
    for shi_chen, (start, end) in SHI_CHEN.items():
        if start <= hour < end or (start == 23 and hour >= 23) or (end == 1 and hour < 1):
            return shi_chen
    return "子"  # 默认返回子时

def get_day_pillar(year, month, day):
    """计算日柱"""
    # 使用公历日期计算日柱
    # 以1900年1月31日为基准日（甲子日）
    base_date = datetime(1900, 1, 31)
    target_date = datetime(year, month, day)
    days_diff = (target_date - base_date).days
    
    # 计算天干地支
    gan_index = (days_diff + 0) % 10  # 1900年1月31日是甲子日
    zhi_index = (days_diff + 0) % 12
    
    return Gan[gan_index] + Zhi[zhi_index]

def get_month_pillar(year, month, day, year_pillar):
    """根据二十四节气计算月柱"""
    solar_data = load_solar_data()
    year_str = str(year)
    if year_str not in solar_data:
        year_data = get_solar(year)
        
    else:
        year_data = solar_data[year_str]
    
    # 获取立春日期
    li_chun_date = datetime.strptime(year_data["立春"], "%Y-%m-%d")
    target_date = datetime(year, month, day)
    
    # 确定农历年份（以立春为界）
    if target_date < li_chun_date:
        # 在立春前，属于前一年
        lunar_year = year - 1
    else:
        lunar_year = year
    
    # 计算月柱
    # 以立春为正月开始
    month_start_dates = []
    for i in range(12):
        if i == 0:
            month_start_dates.append(li_chun_date)
        else:
            # 计算下一个节气
            next_term_index = (i * 2) % 24  # 每月两个节气
            if next_term_index == 0:
                next_term_index = 24
            next_term = SOLAR_TERMS[next_term_index - 1]
            if next_term in year_data:
                month_start_dates.append(datetime.strptime(year_data[next_term], "%Y-%m-%d"))
            else:
                # 如果找不到下一个节气，使用估算
                month_start_dates.append(month_start_dates[-1] + timedelta(days=30))
    
    # 确定当前月份
    current_month = 0
    for i, start_date in enumerate(month_start_dates):
        if target_date >= start_date:
            current_month = i
        else:
            break
    
    # 计算月柱天干地支
    # 年干推月干：甲己之年丙作首，乙庚之年戊为头，丙辛之年庚寅上，丁壬壬寅顺水流，戊癸之年何处起，甲寅之上好追求
    year_gan = year_pillar[0]
    month_gan_start = {
        "甲": 2, "己": 2,  # 丙
        "乙": 4, "庚": 4,  # 戊
        "丙": 6, "辛": 6,  # 庚
        "丁": 8, "壬": 8,  # 壬
        "戊": 0, "癸": 0   # 甲
    }
    
    gan_index = (month_gan_start.get(year_gan, 0) + current_month) % 10
    zhi_index = (2 + current_month) % 12  # 正月从寅开始
    
    return Gan[gan_index] + Zhi[zhi_index]

def get_year_pillar(year, month, day):
    """根据立春确定年柱"""
    solar_data = load_solar_data()
    year_str = str(year)
    if year_str not in solar_data:
        year_data = get_solar(year)
    else:
        year_data = solar_data[year_str]
    
    # 获取立春日期
    li_chun_date = datetime.strptime(year_data["立春"], "%Y-%m-%d")
    target_date = datetime(year, month, day)
    
    # 确定农历年份（以立春为界）
    if target_date < li_chun_date:
        # 在立春前，属于前一年
        lunar_year = year - 1
    else:
        lunar_year = year
    
    # 计算年柱
    # 以1984年甲子年为基准
    base_year = 1984
    year_diff = lunar_year - base_year
    
    gan_index = (year_diff + 0) % 10  # 1984年是甲子年
    zhi_index = (year_diff + 0) % 12
    
    return Gan[gan_index] + Zhi[zhi_index]

def get_bazi(year, month, day, hour):
    """计算完整的八字"""
    # 计算年柱
    year_pillar = get_year_pillar(year, month, day)
    
    # 计算月柱
    month_pillar = get_month_pillar(year, month, day, year_pillar)
    
    # 计算日柱
    day_pillar = get_day_pillar(year, month, day)
    
    # 计算时柱
    hour_shi_chen = get_hour_pillar(hour)
    # 日干推时干：甲己还生甲，乙庚丙作初，丙辛从戊起，丁壬庚子居，戊癸何处发，壬子是真途
    day_gan = day_pillar[0]
    hour_gan_start = {
        "甲": 0, "己": 0,  # 甲
        "乙": 2, "庚": 2,  # 丙
        "丙": 4, "辛": 4,  # 戊
        "丁": 6, "壬": 6,  # 庚
        "戊": 8, "癸": 8   # 壬
    }
    
    shi_chen_index = Zhi.index(hour_shi_chen)
    gan_index = (hour_gan_start.get(day_gan, 0) + shi_chen_index) % 10
    hour_pillar = Gan[gan_index] + hour_shi_chen
    
    return {
        "年柱": year_pillar,
        "月柱": month_pillar,
        "日柱": day_pillar,
        "时柱": hour_pillar,
        "生肖": ShengXiao[Zhi.index(year_pillar[1])],
        "八字": year_pillar +" "+ month_pillar + " " + day_pillar + " "  + hour_pillar
    }



if __name__ == "__main__":
    result = get_bazi(2002, 1, 19, 5)
    print(result)