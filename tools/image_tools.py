# tools/image_tools.py
# 图片分析工具：提取 EXIF 参数 + 色彩分析 → 调色建议

import os


def analyze_image(image_path: str) -> str:
    """
    分析一张图片，返回拍摄参数、色彩分析和调色建议。
    适合影视器材专家给用户提供后期调色思路。
    """
    try:
        if not os.path.exists(image_path):
            return f"图片不存在：{image_path}"

        from PIL import Image
        img = Image.open(image_path)

        parts = []

        # 1. 基本信息
        parts.append("【图片基本信息】")
        parts.append(f"文件：{os.path.basename(image_path)}")
        parts.append(f"尺寸：{img.size[0]} x {img.size[1]} 像素")
        parts.append(f"格式：{img.format}")
        parts.append(f"色彩模式：{img.mode}")

        # 2. EXIF 拍摄参数
        exif_info = _extract_exif(img)
        if exif_info:
            parts.append("")
            parts.append("【拍摄参数 (EXIF)】")
            for key, val in exif_info.items():
                parts.append(f"{key}：{val}")
        else:
            parts.append("")
            parts.append("【拍摄参数】未找到 EXIF 信息（可能是截图或已处理过的图片）")

        # 3. 色彩分析
        color_analysis = _analyze_colors(img)
        parts.append("")
        parts.append("【色彩分析】")
        parts.append(f"整体亮度：{color_analysis['brightness']}")
        parts.append(f"整体色温：{color_analysis['temperature']}")
        parts.append(f"主色调：{color_analysis['dominant']}")
        parts.append(f"色彩饱和度：{color_analysis['saturation']}")
        parts.append(f"对比度：{color_analysis['contrast']}")

        # 4. 调色建议
        parts.append("")
        parts.append("【调色建议】")
        suggestions = _generate_suggestions(color_analysis, exif_info)
        for s in suggestions:
            parts.append(f"- {s}")

        return "\n".join(parts)

    except Exception as e:
        return f"图片分析出错：{e}"


def _extract_exif(img) -> dict:
    """从图片提取 EXIF 拍摄参数"""
    info = {}
    try:
        exif = img._getexif()
        if not exif:
            return info

        # EXIF 标签映射
        TAGS = {
            271: "相机品牌",
            272: "相机型号",
            274: "方向",
            282: "X分辨率",
            283: "Y分辨率",
            305: "软件",
            306: "拍摄日期",
            33434: "快门速度",
            33437: "光圈值",
            34855: "ISO",
            36867: "拍摄时间",
            37377: "快门速度(TV)",
            37378: "光圈(AV)",
            37380: "曝光补偿",
            37381: "最大光圈",
            37383: "测光模式",
            37385: "闪光灯",
            37386: "焦距",
            37500: "厂商说明",
            41486: "焦距(35mm等效)",
            41488: "对焦方式",
            41495: "测光模式",
            41728: "场景类型",
            41986: "白平衡",
            41987: "曝光模式",
            41989: "等效焦距",
            42036: "镜头型号",
        }

        # 测光模式
        METERING = {0: "未知", 1: "平均", 2: "中央重点", 3: "点测光", 4: "多点测光", 5: "评价测光", 6: "局部测光"}

        for tag_id, tag_name in TAGS.items():
            if tag_id in exif:
                val = exif[tag_id]
                # 特殊处理
                if tag_id == 33434:  # 快门速度
                    if isinstance(val, tuple) and len(val) == 2:
                        if val[0] < val[1]:
                            val = f"1/{int(val[1]/val[0])}s"
                        else:
                            val = f"{val[0]/val[1]}s"
                elif tag_id == 33437:  # 光圈
                    if isinstance(val, tuple) and len(val) == 2:
                        val = f"f/{val[0]/val[1]:.1f}"
                elif tag_id == 37386:  # 焦距
                    if isinstance(val, tuple) and len(val) == 2:
                        val = f"{val[0]/val[1]:.0f}mm"
                elif tag_id == 37383:  # 测光模式
                    val = METERING.get(val, str(val))
                elif tag_id == 41986:  # 白平衡
                    val = "自动" if val == 0 else "手动"
                elif isinstance(val, tuple):
                    val = str(val)

                info[tag_name] = str(val)

    except:
        pass
    return info


def _analyze_colors(img) -> dict:
    """分析图片色彩特征"""
    from colorthief import ColorThief
    from PIL import Image
    import io

    result = {
        "brightness": "",
        "temperature": "",
        "dominant": "",
        "saturation": "",
        "contrast": "",
    }

    # 转 RGB
    if img.mode != "RGB":
        img_rgb = img.convert("RGB")
    else:
        img_rgb = img

    # 缩小图片加速分析
    small = img_rgb.resize((200, 200))
    pixels = list(small.getdata())

    # 亮度分析
    avg_brightness = sum(sum(p) / 3 for p in pixels) / len(pixels)
    if avg_brightness > 180:
        result["brightness"] = "偏亮（高调）"
    elif avg_brightness > 120:
        result["brightness"] = "正常"
    elif avg_brightness > 80:
        result["brightness"] = "偏暗（低调）"
    else:
        result["brightness"] = "很暗"

    # 色温分析
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)
    if avg_r > avg_b + 20:
        result["temperature"] = "偏暖（橙黄色调）"
    elif avg_b > avg_r + 20:
        result["temperature"] = "偏冷（蓝色调）"
    else:
        result["temperature"] = "中性"

    # 对比度
    brightness_values = [sum(p) / 3 for p in pixels]
    min_b = min(brightness_values)
    max_b = max(brightness_values)
    contrast_range = max_b - min_b
    if contrast_range > 150:
        result["contrast"] = "高对比"
    elif contrast_range > 100:
        result["contrast"] = "中等对比"
    else:
        result["contrast"] = "低对比（灰雾感）"

    # 主色调（用 ColorThief）
    try:
        # 保存临时文件给 ColorThief 用
        tmp = os.path.join(os.path.dirname(__file__), "_tmp_color.jpg")
        img_rgb.save(tmp, "JPEG")
        ct = ColorThief(tmp)
        dominant = ct.get_color(quality=1)
        palette = ct.get_palette(color_count=5, quality=1)
        result["dominant"] = f"RGB{dominant}"

        # 判断主色调倾向
        r, g, b = dominant
        if r > g and r > b:
            result["dominant"] += "（红色系）"
        elif g > r and g > b:
            result["dominant"] += "（绿色系）"
        elif b > r and b > g:
            result["dominant"] += "（蓝色系）"
        elif r > 200 and g > 200 and b < 150:
            result["dominant"] += "（黄色系）"
        elif r > 200 and g < 150 and b < 150:
            result["dominant"] += "（橙红系）"

        # 饱和度
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        if max_c == 0:
            sat = 0
        else:
            sat = (max_c - min_c) / max_c
        if sat > 0.6:
            result["saturation"] = "高饱和（鲜艳）"
        elif sat > 0.3:
            result["saturation"] = "中等饱和"
        else:
            result["saturation"] = "低饱和（灰调/莫兰迪）"

        # 清理临时文件
        if os.path.exists(tmp):
            os.remove(tmp)
    except:
        result["dominant"] = "分析失败"
        result["saturation"] = "分析失败"

    return result


def _generate_suggestions(color_info: dict, exif_info: dict) -> list:
    """根据色彩分析和拍摄参数生成调色建议"""
    suggestions = []

    brightness = color_info.get("brightness", "")
    temperature = color_info.get("temperature", "")
    contrast = color_info.get("contrast", "")
    saturation = color_info.get("saturation", "")

    # 亮度建议
    if "偏亮" in brightness:
        suggestions.append("画面偏亮：可以适当压低曝光(-0.3~-0.7EV)，恢复高光细节")
        suggestions.append("在 DaVinci Resolve 中使用 Color Wheels，压低 Highlights")
    elif "偏暗" in brightness:
        suggestions.append("画面偏暗：可以提亮阴影(Shadows)，但注意不要提太多产生噪点")
        suggestions.append("如果要提亮暗部，建议先降噪再调色")

    # 色温建议
    if "暖" in temperature:
        suggestions.append("画面偏暖：如果想要中性色调，可以在白平衡中降低色温(向蓝色方向)")
        suggestions.append("如果想要电影感，保留暖调但稍微降低饱和度")
    elif "冷" in temperature:
        suggestions.append("画面偏冷：可以提高色温(向橙色方向)让画面更温暖")
        suggestions.append("冷调适合科技感、悬疑类内容，如果是人像建议适当加暖")

    # 对比度建议
    if "高对比" in contrast:
        suggestions.append("对比度较高：暗部细节可能丢失，可以适当提亮Shadows找回细节")
        suggestions.append("高对比适合戏剧感、电影感画面")
    elif "低对比" in contrast:
        suggestions.append("对比度较低：画面偏灰，可以增加对比度或使用S曲线增加层次")
        suggestions.append("如果拍的是Log灰片，低对比是正常的，需要先还原再调色")

    # 饱和度建议
    if "高饱和" in saturation:
        suggestions.append("饱和度较高：如果觉得太艳，可以降低整体饱和度或只降低特定颜色(如橙色/黄色)")
    elif "低饱和" in saturation:
        suggestions.append("饱和度较低：适合莫兰迪色系/文艺风格")
        suggestions.append("如果想增加活力，适当提高饱和度+5~15，不要加太多会假")

    # 通用建议
    suggestions.append("调色顺序建议：白平衡 → 曝光 → 对比度 → 饱和度 → 局部调整 → 暗角/颗粒")
    suggestions.append("推荐工具：DaVinci Resolve（免费版够用）、Lightroom、剪映专业版")

    return suggestions
