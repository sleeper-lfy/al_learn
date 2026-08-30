import re


class DocumentCleaner:

    def clean(self, text: str) -> str:

        text = self.remove_page_number(text)

        text = "\n".join(line.strip() for line in text.splitlines())

        text = re.sub(r"[ \t]+", " ", text)

        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def merge_broken_lines(self, text: str) -> str:

        lines = text.splitlines()

        result = []

        for line in lines:

            line = line.strip()

            if not line:
                result.append("")
                continue

            if not result:
                result.append(line)
                continue

            previous = result[-1]

            if (previous and not previous.endswith(("。", "！", "？", "；", "：")) and not line.startswith(
                ("第", "一、", "二、", "三、"))):
                result[-1] = previous + line

            else:
                result.append(line)

        return "\n".join(result)

    def remove_page_number(self, text: str) -> str:

        lines = text.splitlines()

        result = []

        for line in lines:

            line = line.strip()

            # 单独的一行数字
            if re.fullmatch(r"\d+", line):
                continue

            result.append(line)

        return "\n".join(result)
