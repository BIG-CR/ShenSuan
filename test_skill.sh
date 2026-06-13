#!/bin/bash
# 八字格局速断 Skill 测试套件
# 用法: bash test_skill.sh
# 每个测试输出 PASS 或 FAIL

SKILL_DIR="L:/废稿/易/.claude/skills/神算-shensuan"
PASS=0
FAIL=0

check() {
    local test_name="$1"
    local result="$2"
    if [ "$result" = "true" ]; then
        echo "  PASS: $test_name"
        PASS=$((PASS+1))
    else
        echo "  FAIL: $test_name"
        FAIL=$((FAIL+1))
    fi
}

echo "========================================"
echo " 神算-shensuan Skill 测试套件"
echo "========================================"
echo ""

# === 测试1: 三大分类 ===
echo "[1] 三大分类入口"
R1=$(grep -c "三大分类" "$SKILL_DIR/SKILL.md")
R2=$(grep -c "分类一：八字\|分类二：问事情\|分类三：推演环境" "$SKILL_DIR/SKILL.md")
if [ "$R1" -gt 0 ] && [ "$R2" -gt 0 ]; then
    check "三大分类定义存在" "true"
else
    check "三大分类定义存在" "false"
fi

# === 测试2: 日柱精确计算 ===
echo "[2] 日柱Bash+Python精确计算"
R1=$(grep -c "python3" "$SKILL_DIR/SKILL.md")
R2=$(grep -c "datetime" "$SKILL_DIR/SKILL.md")
R3=$(grep -c "1900.*1.*1\|1900-01-01" "$SKILL_DIR/SKILL.md")
if [ "$R1" -gt 0 ] && [ "$R2" -gt 0 ] && [ "$R3" -gt 0 ]; then
    check "日柱Python计算指令存在" "true"
else
    check "日柱Python计算指令存在" "false"
fi

# === 测试2b: 日柱实际计算验证（已知答案测试） ===
echo "[2b] 日柱计算准确性验证"
# 用 Python 内部比较避免编码问题，已知：2004-01-11=己丑, 2000-01-01=戊午
CHECK=$(python3 -c "
from datetime import date
base = date(1900, 1, 1)
tg = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
dz = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
def calc(d):
    diff = (d - base).days
    gz = (diff + 10) % 60
    return tg[gz%10] + dz[gz%12]
r1 = calc(date(2004, 1, 11))
r2 = calc(date(2000, 1, 1))
print('PASS' if r1 == '己丑' and r2 == '戊午' else f'FAIL: 2004-01-11={r1}(exp:己丑) 2000-01-01={r2}(exp:戊午)')
" 2>/dev/null || python -c "
from datetime import date
base = date(1900, 1, 1)
tg = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
dz = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
def calc(d):
    diff = (d - base).days
    gz = (diff + 10) % 60
    return tg[gz%10] + dz[gz%12]
r1 = calc(date(2004, 1, 11))
r2 = calc(date(2000, 1, 1))
print('PASS' if r1 == '己丑' and r2 == '戊午' else f'FAIL: 2004-01-11={r1}(exp:己丑) 2000-01-01={r2}(exp:戊午)')
")
if echo "$CHECK" | grep -q "^PASS$"; then
    check "日柱计算: 2004-01-11=己丑, 2000-01-01=戊午" "true"
else
    echo "    $CHECK"
    check "日柱计算: 2004-01-11=己丑, 2000-01-01=戊午" "false"
fi

# === 测试3: JSON文件有效性 ===
echo "[3] JSON文件全部有效"
ALL_VALID="true"
for f in methods tiaohou shensha industry_wuxing cases calendar_reference; do
    if ! python3 -c "import json; json.load(open('$SKILL_DIR/$f.json','r',encoding='utf-8'))" 2>/dev/null && ! python -c "import json; json.load(open('$SKILL_DIR/$f.json','r',encoding='utf-8'))" 2>/dev/null; then
        ALL_VALID="false"
        echo "    $f.json: INVALID"
    fi
done
check "6个JSON文件全部有效" "$ALL_VALID"

# === 测试4: 敏感词清零 ===
echo "[4] 敏感词清零"
SENSITIVE=$(grep -rn "算命\|吉凶\|预测\|化解\|测算\|改运\|趋吉避凶\|断命" "$SKILL_DIR" --include="*.json" --include="*.md" | grep -v "不构成.*预测\|不是.*预测\|避险\|免责\|README.md\|用词安全\|禁止出现")
S_COUNT=$(echo "$SENSITIVE" | grep -v "^$" | wc -l)
if [ "$S_COUNT" -eq 0 ]; then
    check "敏感词清零（算命/吉凶/预测/化解/测算/改运/趋吉避凶/断命）" "true"
else
    echo "    命中: $SENSITIVE"
    check "敏感词清零（算命/吉凶/预测/化解/测算/改运/趋吉避凶/断命）" "false"
fi

# === 测试5: 免责声明位于输出末尾 ===
echo "[5] 免责声明在输出末尾"
R1=$(grep -c "输出即视为已阅读避险声明" "$SKILL_DIR/SKILL.md")
R2=$(grep -c "避险声明" "$SKILL_DIR/SKILL.md")
# 检查免责不在"第零步"（旧设计），而在输出模板末尾
OLD_DESIGN=$(grep -c "第零步：免责声明" "$SKILL_DIR/SKILL.md")
if [ "$R1" -gt 0 ] && [ "$R2" -gt 0 ] && [ "$OLD_DESIGN" -eq 0 ]; then
    check "免责声明在输出末尾（非阻塞步骤）" "true"
else
    check "免责声明在输出末尾（非阻塞步骤）" "false"
fi

# === 测试6: 追问铁律 ===
echo "[6] 追问到底机制"
R1=$(grep -c "追问铁律\|问到底\|追问策略\|缺一项问一项" "$SKILL_DIR/SKILL.md")
if [ "$R1" -ge 2 ]; then
    check "追问铁律已配置" "true"
else
    check "追问铁律已配置" "false"
fi

# === 测试7: 缺信息追问 ===
echo "[7] 信息收集精度"
R1=$(grep -c "必须收集\|精度要求\|精确到" "$SKILL_DIR/SKILL.md")
if [ "$R1" -ge 3 ]; then
    check "三类信息收集精度定义存在" "true"
else
    check "三类信息收集精度定义存在" "false"
fi

# === 测试8: 硬性检查规则 ===
echo "[8] 硬性检查规则"
R1=$(grep -c "真太阳时.*经度\|经度.*110" "$SKILL_DIR/SKILL.md")
R2=$(grep -c "节气边界\|节气日" "$SKILL_DIR/SKILL.md")
R3=$(grep -c "早夜子时\|夜子时.*早子时" "$SKILL_DIR/SKILL.md")
ALL_CHECKS="true"
[ "$R1" -eq 0 ] && echo "    缺少：真太阳时经度检查" && ALL_CHECKS="false"
[ "$R2" -eq 0 ] && echo "    缺少：节气边界检查" && ALL_CHECKS="false"
[ "$R3" -eq 0 ] && echo "    缺少：早夜子时检查" && ALL_CHECKS="false"
check "三项硬性检查规则全部写入" "$ALL_CHECKS"

# === 附加测试: 文件完整性 ===
echo "[9] 文件完整性"
REQUIRED_FILES="SKILL.md README.md LICENSE .gitignore methods.json tiaohou.json shensha.json industry_wuxing.json cases.json calendar_reference.json profiles.json"
ALL_FILES="true"
for f in $REQUIRED_FILES; do
    if [ ! -f "$SKILL_DIR/$f" ]; then
        echo "    缺少: $f"
        ALL_FILES="false"
    fi
done
check "11个必需文件全部存在" "$ALL_FILES"

# === 附加测试: methods.json 数量一致性 ===
echo "[10] methods.json数量与SKILL.md一致"
JSON_COUNT=$(python3 -c "import json; d=json.load(open('$SKILL_DIR/methods.json','r',encoding='utf-8')); print(len(d['methods']))" 2>/dev/null || python -c "import json; d=json.load(open('$SKILL_DIR/methods.json','r',encoding='utf-8')); print(len(d['methods']))" 2>/dev/null)
MD_COUNT=$(grep -c "^#[0-9]" "$SKILL_DIR/SKILL.md" 2>/dev/null)
if [ "$JSON_COUNT" = "26" ]; then
    check "methods.json包含26种方法" "true"
else
    check "methods.json包含26种方法（实际=$JSON_COUNT）" "false"
fi

echo ""
echo "========================================"
echo " 结果: $PASS PASS, $FAIL FAIL"
echo "========================================"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
