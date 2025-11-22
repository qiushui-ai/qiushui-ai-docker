"""
Markdown 标签提取器

从 Markdown 内容中提取 #标签
"""
import re
from typing import List, Set


class MarkdownTagExtractor:
    """从 Markdown 中提取标签"""

    def extract_tags(self, content: str) -> List[str]:
        """
        从 Markdown 内容中提取所有 #标签

        规则:
        1. 提取 #xxx 或 #aaa/bbb/ccc 格式的标签
        2. 自动排除代码块中的 # 符号
        3. 排除 Markdown 标题 (行首 # + 空格)
        4. 支持中英文、数字、下划线、连字符、斜杠

        示例:
            content = "学习 #Python #AI/机器学习\\n```python\\n# 代码注释\\n```"
            result = ["Python", "AI/机器学习"]

        Args:
            content: Markdown 文本内容

        Returns:
            提取的标签列表，已去重并排序
        """
        tags: Set[str] = set()

        # 1. 移除代码块 (```...```)
        content_no_code = re.sub(r"```[\s\S]*?```", "", content)

        # 2. 移除行内代码 (`...`)
        content_no_code = re.sub(r"`[^`]+`", "", content_no_code)

        # 3. 按行处理，移除 Markdown 标题行
        lines = content_no_code.split("\n")
        non_heading_lines = []
        for line in lines:
            # 跳过 Markdown 标题行 (行首 # + 空格)
            if not re.match(r"^\s*#{1,6}\s+", line):
                non_heading_lines.append(line)

        clean_content = "\n".join(non_heading_lines)

        # 4. 提取标签
        # 匹配 #标签 或 #分类/子分类/标签
        # 支持: 字母、数字、中文、下划线、连字符、斜杠
        pattern = r"#([\w\u4e00-\u9fa5_-]+(?:/[\w\u4e00-\u9fa5_-]+)*)"

        matches = re.findall(pattern, clean_content)
        tags.update(matches)

        return sorted(list(tags))


# 全局实例
_tag_extractor = MarkdownTagExtractor()


def extract_tags_from_markdown(content: str) -> List[str]:
    """
    从 Markdown 内容中提取标签 (便捷函数)

    Args:
        content: Markdown 文本

    Returns:
        标签列表

    示例:
        >>> extract_tags_from_markdown("学习 #Python #AI/机器学习")
        ["AI/机器学习", "Python"]
    """
    return _tag_extractor.extract_tags(content)
