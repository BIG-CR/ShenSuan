#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
八字排盘引擎 — 基于寿星天文历(sxtwl) + 真太阳时
用法: python paipan.py 2004 1 19 12 0 118.5 25.5 男
      或作为模块: from paipan import BaziChart
"""

import sys
import json
import math
from datetime import datetime, timedelta

# ── 常量表 ──────────────────────────────────────────────

TG = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DZ = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
      '庚': '金', '辛': '金', '壬': '水', '癸': '水',
      '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
      '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}

# 六十甲子纳音表
NAYIN_TABLE = {
    '甲子': '海中金', '乙丑': '海中金', '丙寅': '炉中火', '丁卯': '炉中火',
    '戊辰': '大林木', '己巳': '大林木', '庚午': '路旁土', '辛未': '路旁土',
    '壬申': '剑锋金', '癸酉': '剑锋金', '甲戌': '山头火', '乙亥': '山头火',
    '丙子': '涧下水', '丁丑': '涧下水', '戊寅': '城头土', '己卯': '城头土',
    '庚辰': '白蜡金', '辛巳': '白蜡金', '壬午': '杨柳木', '癸未': '杨柳木',
    '甲申': '泉中水', '乙酉': '泉中水', '丙戌': '屋上土', '丁亥': '屋上土',
    '戊子': '霹雳火', '己丑': '霹雳火', '庚寅': '松柏木', '辛卯': '松柏木',
    '壬辰': '长流水', '癸巳': '长流水', '甲午': '沙中金', '乙未': '沙中金',
    '丙申': '山下火', '丁酉': '山下火', '戊戌': '平地木', '己亥': '平地木',
    '庚子': '壁上土', '辛丑': '壁上土', '壬寅': '金箔金', '癸卯': '金箔金',
    '甲辰': '覆灯火', '乙巳': '覆灯火', '丙午': '天河水', '丁未': '天河水',
    '戊申': '大驿土', '己酉': '大驿土', '庚戌': '钗钏金', '辛亥': '钗钏金',
    '壬子': '桑柘木', '癸丑': '桑柘木', '甲寅': '大溪水', '乙卯': '大溪水',
    '丙辰': '沙中土', '丁巳': '沙中土', '戊午': '天上火', '己未': '天上火',
    '庚申': '石榴木', '辛酉': '石榴木', '壬戌': '大海水', '癸亥': '大海水',
}

# 时辰映射
HOUR_TO_DZ = {
    0: '子', 1: '丑', 2: '丑', 3: '寅', 4: '寅', 5: '卯', 6: '卯',
    7: '辰', 8: '辰', 9: '巳', 10: '巳', 11: '午', 12: '午',
    13: '未', 14: '未', 15: '申', 16: '申', 17: '酉', 18: '酉',
    19: '戌', 20: '戌', 21: '亥', 22: '亥', 23: '子',
}

# 地支藏干
CANG_GAN = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '庚', '戊'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲'],
}

# 五虎遁（月干起法）
WUHU_DUN = {
    0: 2,  # 甲年: 丙寅起 → 丙=2
    1: 4,  # 乙年: 戊寅起 → 戊=4
    2: 6,  # 丙年: 庚寅起 → 庚=6
    3: 8,  # 丁年: 壬寅起 → 壬=8
    4: 0,  # 戊年: 甲寅起
    5: 2,  # 己年: 丙寅起
    6: 4,  # 庚年: 戊寅起
    7: 6,  # 辛年: 庚寅起
    8: 8,  # 壬年: 壬寅起
    9: 0,  # 癸年: 甲寅起
}

# 五鼠遁（时干起法）
WUSHU_DUN = {
    0: 0,  # 甲日: 甲子起
    1: 2,  # 乙日: 丙子起
    2: 4,  # 丙日: 戊子起
    3: 6,  # 丁日: 庚子起
    4: 8,  # 戊日: 壬子起
    5: 0,  # 己日: 甲子起
    6: 2,  # 庚日: 丙子起
    7: 4,  # 辛日: 戊子起
    8: 6,  # 壬日: 庚子起
    9: 8,  # 癸日: 壬子起
}

# 十神关系（日干 vs 他干）
# key: 生克关系: 1=同, 2=我生, 3=我克, 4=克我, 5=生我
SHISHEN = {
    (1, 0): '比肩', (1, 1): '劫财',
    (2, 0): '食神', (2, 1): '伤官',
    (3, 0): '偏财', (3, 1): '正财',
    (4, 0): '七杀', (4, 1): '正官',
    (5, 0): '偏印', (5, 1): '正印',
}

# 节气名
JIEQI_NAMES = [
    '冬至', '小寒', '大寒', '立春', '雨水', '惊蛰',
    '春分', '清明', '谷雨', '立夏', '小满', '芒种',
    '夏至', '小暑', '大暑', '立秋', '处暑', '白露',
    '秋分', '寒露', '霜降', '立冬', '小雪', '大雪',
]


# ── 真太阳时计算 ───────────────────────────────────────

def true_solar_time_offset(longitude, dt):
    """
    计算真太阳时偏移量（分钟）。
    offset = (longitude - 120) * 4 + EoT(equation of time)
    """
    # 1. 经度修正：每度4分钟
    lon_offset = (longitude - 120.0) * 4.0

    # 2. 均时差(EoT)近似计算
    # 使用 Spencer (1971) 公式
    day_of_year = dt.timetuple().tm_yday
    B = 2 * math.pi * (day_of_year - 1) / 365.0
    eot = 229.18 * (0.000075 + 0.001868 * math.cos(B) - 0.032077 * math.sin(B)
                    - 0.014615 * math.cos(2*B) - 0.040849 * math.sin(2*B))

    return lon_offset + eot


# ── 辅助函数 ────────────────────────────────────────────

def gz_str(tg_idx, dz_idx):
    """干支索引→字符串"""
    return f'{TG[tg_idx]}{DZ[dz_idx]}'


def nayin(pillar_str):
    """查纳音"""
    return NAYIN_TABLE.get(pillar_str, '')


def shishen_name(day_tg, other_tg):
    """计算十神名称"""
    diff = (other_tg - day_tg) % 10
    if diff == 0:
        return '比肩'
    is_yang = (day_tg % 2 == 0)
    if is_yang:
        rel_map = {
            1: (1, 1),  # 劫财
            2: (2, 0),  # 食神
            3: (2, 1),  # 伤官
            4: (3, 0),  # 偏财
            5: (3, 1),  # 正财
            6: (4, 0),  # 七杀
            7: (4, 1),  # 正官
            8: (5, 0),  # 偏印
            9: (5, 1),  # 正印
        }
    else:
        rel_map = {
            1: (2, 1),  # 伤官
            2: (2, 0),  # 食神
            3: (3, 1),  # 正财
            4: (3, 0),  # 偏财
            5: (4, 1),  # 正官
            6: (4, 0),  # 七杀
            7: (5, 1),  # 正印
            8: (5, 0),  # 偏印
            9: (1, 1),  # 劫财
        }
    return SHISHEN.get(rel_map[diff], '') if diff in rel_map else ''


def day_pillar_index_by_solar(year, month, day):
    """通过 sxtwl 获取日柱干支索引（tg, dz）"""
    try:
        import sxtwl
        d = sxtwl.fromSolar(year, month, day)
        gz = d.getDayGZ()
        return gz.tg, gz.dz
    except ImportError:
        # 回退: 以 1900-01-01 甲戌日为基准推算
        base = datetime(1900, 1, 1)
        d = datetime(year, month, day)
        diff = (d - base).days
        gz_idx = (diff + 10) % 60  # 甲戌=10
        return gz_idx % 10, gz_idx % 12


# ── 排盘核心类 ──────────────────────────────────────────

class BaziChart:
    """八字命盘"""

    def __init__(self, year, month, day, hour=12, minute=0,
                 longitude=120.0, latitude=30.0, gender='男'):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.longitude = longitude
        self.latitude = latitude
        self.gender = '男' if gender in ('男', 'male', 'm') else '女'

        self.y_tg = self.y_dz = self.m_tg = self.m_dz = None
        self.d_tg = self.d_dz = self.h_tg = self.h_dz = None
        self.nayin_map = {}
        self.shishen_map = {}
        self.canggan_map = {}
        self.shensha = []
        self.dayun = []
        self.warnings = []
        self.true_solar_offset = 0.0

    def calculate(self):
        """执行完整排盘，返回 self（支持链式调用）"""
        dt = datetime(self.year, self.month, self.day, self.hour, self.minute)

        # 1. 真太阳时
        self.true_solar_offset = true_solar_time_offset(self.longitude, dt)

        # 2. 四柱
        self._calc_four_pillars()

        # 3. 纳音
        self.nayin_map = {
            '年柱': nayin(gz_str(self.y_tg, self.y_dz)),
            '月柱': nayin(gz_str(self.m_tg, self.m_dz)),
            '日柱': nayin(gz_str(self.d_tg, self.d_dz)),
            '时柱': nayin(gz_str(self.h_tg, self.h_dz)),
        }

        # 4. 藏干
        for label, dz_idx in [('年柱', self.y_dz), ('月柱', self.m_dz),
                               ('日柱', self.d_dz), ('时柱', self.h_dz)]:
            self.canggan_map[label] = CANG_GAN.get(DZ[dz_idx], [])

        # 5. 十神（以日干为中心）
        for label, tg_idx in [('年柱', self.y_tg), ('月柱', self.m_tg),
                               ('时柱', self.h_tg)]:
            self.shishen_map[label] = shishen_name(self.d_tg, tg_idx)

        # 6. 神煞
        self._calc_shensha()

        # 7. 大运
        self._calc_dayun()

        # 8. 硬性检查
        self._hard_checks()

        return self

    def _calc_four_pillars(self):
        """计算四柱干支"""
        try:
            import sxtwl
            d = sxtwl.fromSolar(self.year, self.month, self.day)

            y_gz = d.getYearGZ()
            m_gz = d.getMonthGZ()
            d_gz = d.getDayGZ()

            self.y_tg, self.y_dz = y_gz.tg, y_gz.dz
            self.m_tg, self.m_dz = m_gz.tg, m_gz.dz
            self.d_tg, self.d_dz = d_gz.tg, d_gz.dz

            # 时柱：用真太阳时修正后的时间
            total_minutes = self.hour * 60 + self.minute + self.true_solar_offset
            if total_minutes < 0:
                total_minutes += 1440
            elif total_minutes >= 1440:
                total_minutes -= 1440
            true_hour_int = int(total_minutes / 60.0) % 24
            h_gz = d.getHourGZ(true_hour_int)
            self.h_tg, self.h_dz = h_gz.tg, h_gz.dz

        except ImportError:
            # 纯 Python 回退
            self._calc_four_pillars_pure()

    def _calc_four_pillars_pure(self):
        """纯 Python 回退排盘（无 sxtwl 时使用）"""
        dt = datetime(self.year, self.month, self.day)

        # 日柱
        base = datetime(1900, 1, 1)
        diff = (dt - base).days
        gz_idx = (diff + 10) % 60
        self.d_tg, self.d_dz = gz_idx % 10, gz_idx % 12

        # 年柱（简化：按农历年边界判断，用立春≈2月4日）
        if self.month < 2 or (self.month == 2 and self.day < 4):
            solar_year = self.year - 1
        else:
            solar_year = self.year
        # 1984年是甲子年，tg=0, dz=0
        y_idx = (solar_year - 1984) % 60
        self.y_tg, self.y_dz = y_idx % 10, y_idx % 12

        # 月柱
        # 按节气近似：立春2/4→寅, 惊蛰3/6→卯, ...
        month_dz_map = [
            (1, 5), (1, 20), (2, 4), (3, 6), (4, 5), (5, 6),
            (6, 6), (7, 7), (8, 8), (9, 8), (10, 8), (11, 7), (12, 7)
        ]
        # DZ index for each solar term month
        dz_index = None
        md = self.month * 100 + self.day
        approximations = [
            (206, 2), (306, 3), (405, 4), (506, 5), (606, 6), (707, 7),
            (808, 8), (908, 9), (1008, 10), (1107, 11), (1207, 0), (106, 1)
        ]
        for threshold_md, dz_i in approximations:
            if md >= threshold_md:
                dz_index = dz_i
                break
        if dz_index is None:
            dz_index = 1
        self.m_dz = dz_index

        # 月天干用五虎遁
        start_tg = WUHU_DUN[self.y_tg]
        self.m_tg = (start_tg + self.m_dz) % 10 if self.m_dz >= 2 else \
                    (start_tg + (self.m_dz + 12) - 2) % 10
        if self.m_dz >= 2:
            self.m_tg = (start_tg + self.m_dz - 2) % 10
        else:
            self.m_tg = (start_tg + self.m_dz + 10) % 10

        # 时柱
        true_hour = self.hour + self.true_solar_offset / 60.0
        if true_hour < 0:
            true_hour += 24
        elif true_hour >= 24:
            true_hour -= 24
        self.h_dz = int(true_hour / 2) % 12 if true_hour < 23 else 0
        if true_hour >= 23:
            self.h_dz = 0
        elif true_hour >= 1:
            self.h_dz = int((true_hour + 1) / 2) % 12
        else:
            self.h_dz = 0

        start_h_tg = WUSHU_DUN[self.d_tg]
        self.h_tg = (start_h_tg + self.h_dz) % 10

    def _calc_shensha(self):
        """计算神煞 — 逐柱检查"""
        self.shensha = []
        for label, tg_idx, dz_idx in [
            ('年柱', self.y_tg, self.y_dz),
            ('月柱', self.m_tg, self.m_dz),
            ('日柱', self.d_tg, self.d_dz),
            ('时柱', self.h_tg, self.h_dz),
        ]:
            self.shensha += self._shensha_one_pillar(tg_idx, dz_idx, label)

    def _shensha_one_pillar(self, tg_idx, dz_idx, pillar):
        """单柱神煞检查"""
        results = []
        # 天乙贵人: 以日干/年干查
        # 甲戊庚见丑未, 乙己见子申, 丙丁见亥酉, 壬癸见卯巳, 辛见寅午
        for check_tg in [tg_idx, self.d_tg]:
            if ((check_tg in [0, 4, 6] and dz_idx in [1, 7]) or
                (check_tg in [1, 5] and dz_idx in [0, 8]) or
                (check_tg in [2, 3] and dz_idx in [11, 9]) or
                (check_tg in [8, 9] and dz_idx in [3, 5]) or
                (check_tg == 7 and dz_idx in [2, 6])):
                results.append({'name': '天乙贵人', 'pillar': pillar})
                break

        # 文昌贵人: 以日干查
        wen_chang = {0: 5, 1: 6, 2: 8, 3: 9, 4: 8, 5: 9, 6: 11, 7: 0, 8: 2, 9: 3}
        if dz_idx == wen_chang.get(self.d_tg):
            results.append({'name': '文昌贵人', 'pillar': pillar})

        # 驿马: 以年支/日支查 — 申子辰见寅, 寅午戌见申, 巳酉丑见亥, 亥卯未见巳
        for ref_dz in [self.y_dz, self.d_dz]:
            ma = None
            if ref_dz in [8, 0, 4] and dz_idx == 2:
                ma = '驿马'
            elif ref_dz in [2, 6, 10] and dz_idx == 8:
                ma = '驿马'
            elif ref_dz in [5, 9, 1] and dz_idx == 11:
                ma = '驿马'
            elif ref_dz in [11, 3, 7] and dz_idx == 5:
                ma = '驿马'
            if ma:
                results.append({'name': ma, 'pillar': pillar})
                break

        # 桃花: 以年支/日支查 — 申子辰见酉, 寅午戌见卯, 巳酉丑见午, 亥卯未见子
        for ref_dz in [self.y_dz, self.d_dz]:
            tao = None
            if ref_dz in [8, 0, 4] and dz_idx == 9:
                tao = '桃花'
            elif ref_dz in [2, 6, 10] and dz_idx == 3:
                tao = '桃花'
            elif ref_dz in [5, 9, 1] and dz_idx == 6:
                tao = '桃花'
            elif ref_dz in [11, 3, 7] and dz_idx == 0:
                tao = '桃花'
            if tao:
                results.append({'name': tao, 'pillar': pillar})
                break

        # 华盖: 以年支/日支查 — 申子辰见辰, 寅午戌见戌, 巳酉丑见丑, 亥卯未见未
        for ref_dz in [self.y_dz, self.d_dz]:
            hg = None
            if ref_dz in [8, 0, 4] and dz_idx == 4:
                hg = '华盖'
            elif ref_dz in [2, 6, 10] and dz_idx == 10:
                hg = '华盖'
            elif ref_dz in [5, 9, 1] and dz_idx == 1:
                hg = '华盖'
            elif ref_dz in [11, 3, 7] and dz_idx == 7:
                hg = '华盖'
            if hg:
                results.append({'name': hg, 'pillar': pillar})
                break

        # 将星: 以年支/日支查 — 申子辰见子, 寅午戌见午, 巳酉丑见酉, 亥卯未见卯
        for ref_dz in [self.y_dz, self.d_dz]:
            jx = None
            if ref_dz in [8, 0, 4] and dz_idx == 0:
                jx = '将星'
            elif ref_dz in [2, 6, 10] and dz_idx == 6:
                jx = '将星'
            elif ref_dz in [5, 9, 1] and dz_idx == 9:
                jx = '将星'
            elif ref_dz in [11, 3, 7] and dz_idx == 3:
                jx = '将星'
            if jx:
                results.append({'name': jx, 'pillar': pillar})
                break

        return results

    def _calc_dayun(self):
        """计算大运（含精确起运年龄）"""
        yang_nian = self.y_tg % 2 == 0
        shun_pai = (yang_nian and self.gender == '男') or \
                   (not yang_nian and self.gender == '女')

        # 精确起运年龄：距节气天数 ÷ 3
        qiyun_age = self._calc_qiyun_age(shun_pai)

        self.dayun = []
        direction = 1 if shun_pai else -1
        for i in range(8):
            da_tg = (self.m_tg + direction * (i + 1)) % 10
            da_dz = (self.m_dz + direction * (i + 1)) % 12
            start_age = round(qiyun_age + i * 10, 1)
            self.dayun.append({
                '干支': gz_str(da_tg, da_dz),
                '纳音': nayin(gz_str(da_tg, da_dz)),
                '起运年龄': start_age,
                '十年区间': f'{start_age}-{start_age + 9:.1f}岁',
            })

    def _calc_qiyun_age(self, shun_pai):
        """精确计算起运年龄：距节气天数 ÷ 3"""
        try:
            import sxtwl
            birth_hour = self.hour + self.minute / 60.0
            birth_time = sxtwl.Time(self.year, self.month, self.day,
                                    int(birth_hour), int((birth_hour % 1) * 60), 0)
            birth_jd = sxtwl.toJD(birth_time)

            # 收集前后两年的节气
            all_jq = []
            for yr in [self.year - 1, self.year, self.year + 1]:
                jq_list = sxtwl.getJieQiByYear(yr)
                for jq in jq_list:
                    all_jq.append((jq.jd, jq.jqIndex))

            all_jq.sort()

            if shun_pai:
                # 顺排：找下一个节气
                for jd, idx in all_jq:
                    if jd > birth_jd:
                        days_to_jq = jd - birth_jd
                        return round(days_to_jq / 3.0, 1)
                return 1.0  # fallback
            else:
                # 逆排：找上一个节气
                prev_jd = None
                for jd, idx in all_jq:
                    if jd >= birth_jd:
                        break
                    prev_jd = jd
                if prev_jd is not None:
                    days_since_jq = birth_jd - prev_jd
                    return round(days_since_jq / 3.0, 1)
                return 1.0  # fallback
        except ImportError:
            return 1.0

    def _hard_checks(self):
        """硬性检查：真太阳时、节气边界、早夜子时"""
        # 1. 真太阳时检查
        if self.longitude < 110:
            offset_min = abs(self.true_solar_offset)
            self.warnings.append(
                f'真太阳时提醒：出生地经度{self.longitude}°E（<110°E），'
                f'真太阳时与北京时间相差约{offset_min:.0f}分钟。'
                f'已自动以真太阳时校正排盘。'
            )

        # 2. 节气边界检查
        try:
            import sxtwl
            d = sxtwl.fromSolar(self.year, self.month, self.day)
            if d.hasJieQi():
                jq = d.getJieQi()
                jq_name = JIEQI_NAMES[jq] if jq < len(JIEQI_NAMES) else f'节气索引{jq}'
                self.warnings.append(
                    f'节气日提醒：你出生在{jq_name}当日，月柱归属取决于具体出生时间。'
                    f'若出生在节气交节时刻之前，月柱属上月；之后则属下月。'
                )
        except ImportError:
            # 近似检查
            boundaries = [(2, 4), (2, 19), (3, 6), (4, 5), (5, 6), (6, 6),
                          (7, 7), (8, 8), (9, 8), (10, 8), (11, 7), (12, 7),
                          (1, 6)]
            for bm, bd in boundaries:
                if self.month == bm and self.day in [bd - 1, bd, bd + 1]:
                    self.warnings.append(
                        f'节气日提醒：你出生在{bm}月{self.day}日，临近节气日，'
                        f'月柱归属取决于具体出生时间。'
                    )
                    break

        # 3. 早夜子时检查
        if self.hour == 23:
            self.warnings.append(
                '夜子时提醒：你出生在夜子时（23:00-23:59），'
                '时柱用当日日干起算。如果出生时间是00:00-00:59（早子时），'
                '时柱用次日日干起算，结果会不同。'
            )
        elif self.hour == 0:
            self.warnings.append(
                '早子时提醒：你出生在早子时（00:00-00:59），'
                '若为23:00-23:59（夜子时），时柱可能不同。'
            )

    def to_dict(self):
        """输出为字典"""
        return {
            '输入': {
                '公历': f'{self.year}年{self.month}月{self.day}日',
                '时间': f'{self.hour:02d}:{self.minute:02d}',
                '地点经度': f'{self.longitude}°E',
                '性别': self.gender,
            },
            '真太阳时': {
                '偏移分钟': round(self.true_solar_offset, 1),
                '说明': f'北京时间 + {self.true_solar_offset:.0f}分钟 = 真太阳时',
            },
            '四柱': {
                '年柱': {
                    '干支': gz_str(self.y_tg, self.y_dz),
                    '天干': TG[self.y_tg],
                    '地支': DZ[self.y_dz],
                    '五行': f'{WX[TG[self.y_tg]]}{WX[DZ[self.y_dz]]}',
                    '纳音': self.nayin_map['年柱'],
                    '藏干': self.canggan_map['年柱'],
                    '十神': self.shishen_map.get('年柱', '日主'),
                },
                '月柱': {
                    '干支': gz_str(self.m_tg, self.m_dz),
                    '天干': TG[self.m_tg],
                    '地支': DZ[self.m_dz],
                    '五行': f'{WX[TG[self.m_tg]]}{WX[DZ[self.m_dz]]}',
                    '纳音': self.nayin_map['月柱'],
                    '藏干': self.canggan_map['月柱'],
                    '十神': self.shishen_map.get('月柱', ''),
                },
                '日柱': {
                    '干支': gz_str(self.d_tg, self.d_dz),
                    '天干': TG[self.d_tg],
                    '地支': DZ[self.d_dz],
                    '五行': f'{WX[TG[self.d_tg]]}{WX[DZ[self.d_dz]]}',
                    '纳音': self.nayin_map['日柱'],
                    '藏干': self.canggan_map['日柱'],
                    '十神': '日主',
                },
                '时柱': {
                    '干支': gz_str(self.h_tg, self.h_dz),
                    '天干': TG[self.h_tg],
                    '地支': DZ[self.h_dz],
                    '五行': f'{WX[TG[self.h_tg]]}{WX[DZ[self.h_dz]]}',
                    '纳音': self.nayin_map['时柱'],
                    '藏干': self.canggan_map['时柱'],
                    '十神': self.shishen_map.get('时柱', ''),
                },
            },
            '神煞': self.shensha,
            '大运': self.dayun,
            '日主': {
                '天干': TG[self.d_tg],
                '五行': WX[TG[self.d_tg]],
            },
            '检查提醒': self.warnings,
        }

    def to_json(self, indent=2):
        """输出为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_text(self):
        """输出为人类可读文本"""
        d = self.to_dict()
        lines = []
        lines.append('═' * 50)
        lines.append('  八 字 命 盘')
        lines.append('═' * 50)
        lines.append('')
        lines.append(f"  出生: {d['输入']['公历']} {d['输入']['时间']}  性别: {d['输入']['性别']}")
        lines.append(f"  经度: {d['输入']['地点经度']}  真太阳时偏移: {d['真太阳时']['偏移分钟']}分钟")
        lines.append('')

        # 四柱表
        hdr = f"{'':6s} {'年柱':^14s} {'月柱':^14s} {'日柱':^14s} {'时柱':^14s}"
        lines.append(hdr)
        lines.append('─' * 65)

        for key in ['干支', '天干', '地支', '五行', '纳音']:
            vals = [d['四柱'][p][key] for p in ['年柱', '月柱', '日柱', '时柱']]
            lines.append(f"  {key:4s}  {vals[0]:^14s} {vals[1]:^14s} {vals[2]:^14s} {vals[3]:^14s}")

        # 藏干
        cg = [','.join(d['四柱'][p]['藏干']) for p in ['年柱', '月柱', '日柱', '时柱']]
        lines.append(f"  {'藏干':4s}  {cg[0]:^14s} {cg[1]:^14s} {cg[2]:^14s} {cg[3]:^14s}")

        # 十神
        ss = [d['四柱'][p]['十神'] for p in ['年柱', '月柱', '日柱', '时柱']]
        lines.append(f"  {'十神':4s}  {ss[0]:^14s} {ss[1]:^14s} {ss[2]:^14s} {ss[3]:^14s}")

        lines.append('')
        lines.append(f"  日主: {d['日主']['天干']} ({d['日主']['五行']})")

        # 神煞
        if d['神煞']:
            lines.append('')
            lines.append('  神煞:')
            for s in d['神煞']:
                lines.append(f"    · {s['name']} ({s['pillar']})")

        # 大运
        if d['大运']:
            lines.append('')
            lines.append('  大运:')
            for da in d['大运']:
                lines.append(f"    {da['十年区间']}  {da['干支']} ({da['纳音']})")

        # 检查提醒
        if d['检查提醒']:
            lines.append('')
            lines.append('  ⚠ 硬性检查提醒:')
            for w in d['检查提醒']:
                lines.append(f'    · {w}')

        lines.append('')
        lines.append('═' * 50)
        return '\n'.join(lines)


# ── 命令行入口 ──────────────────────────────────────────

def main():
    if len(sys.argv) < 4:
        print('用法: python paipan.py <年> <月> <日> [时] [分] [经度] [纬度] [性别] [--json]')
        print('示例: python paipan.py 2004 1 19 12 0 118.5 25.5 男')
        print('      python paipan.py 2004 1 19              # 默认午时、北京、男')
        print('      python paipan.py 2004 1 19 --json      # JSON输出')
        sys.exit(1)

    year, month, day = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    args = sys.argv[4:]

    hour = int(args[0]) if len(args) >= 1 and args[0] not in ('男', '女', 'male', 'female', 'm', 'f', '--json') else 12
    minute = int(args[1]) if len(args) >= 2 and args[1] not in ('男', '女', 'male', 'female', 'm', 'f', '--json') else 0
    lon = float(args[2]) if len(args) >= 3 and args[2] not in ('男', '女', 'male', 'female', 'm', 'f', '--json') else 120.0
    lat = float(args[3]) if len(args) >= 4 and args[3] not in ('男', '女', 'male', 'female', 'm', 'f', '--json') else 30.0

    gender = '男'
    json_mode = False
    for a in args:
        if a == '--json':
            json_mode = True
        elif a in ('男', '女', 'male', 'female', 'm', 'f'):
            gender = a

    chart = BaziChart(year, month, day, hour, minute, lon, lat, gender)
    chart.calculate()

    if json_mode:
        print(chart.to_json())
    else:
        print(chart.to_text())


if __name__ == '__main__':
    main()
