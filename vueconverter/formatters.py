from vueconverter.vueparser import Tag


def add_tab(text: str) -> str:
    return '\n'.join(f'    {line}' for line in text.splitlines())


class Formatter:
    def __init__(self, root: Tag):
        self.root = root

    def format(self) -> str:
        return self.format_tag(self.root)

    def format_attribute(self, key: str, val) -> str:
        raise NotImplementedError()

    def format_tag(self, tag: Tag) -> str:
        raise NotImplementedError()

    def format_text(self, text: str):
        return text


class VueSfcFormatter(Formatter):
    def format_attribute(self, key: str, val) -> str:
        if val is None:
            return key
        else:
            return f'{key}="{val}"'

    def format_tag(self, tag: Tag) -> str:
        if tag.parent and tag.parent.name == '[document]' and tag.name == 'template' and tag.attrs.get('lang') != 'pug':
            try:
                root_tag = next(filter(lambda x: isinstance(x, Tag), tag.children))
            except StopIteration:
                pug_template = ''
            else:
                pug_formatter = PugFormatter(root_tag)
                pug_template = add_tab(pug_formatter.format())
            
            templateAttrs = [ 'lang="pug"' ]
            
            if 'functional' in tag.attrs:
                templateAttrs.append('functional')

            attrs_str = ' '.join(templateAttrs)

            return f'<template {attrs_str}>\n{pug_template}\n</template>'

        if tag.name == '[document]':
            result = []
        else:
            result = [f"<{tag.name}"]

            if tag.attrs:
                result.append(' ')
                result.append(' '.join(self.format_attribute(k, v) for k, v in tag.attrs.items()))

            if tag.self_closing:
                result.append('/>')
            else:
                result.append('>')

        for child in tag.children:
            if isinstance(child, Tag):
                result.append(self.format_tag(child))
            else:
                result.append(self.format_text(child))

        if tag.name != '[document]':
            result.append(f'</{tag.name}>')

        return ''.join(result)


class PugFormatter(Formatter):

    def format_attribute(self, key: str, val) -> str:
        if val is None:
            return key

        if '\n' in val:
            val = '\\\n'.join(val.splitlines())

        return f'{key}="{val}"'

    def format_tag(self, tag: Tag) -> str:
        if tag.name == 'div' and (tag.attrs.get('id', '').strip() or tag.attrs.get('class', '').strip()):
            result = []
        elif tag.name == '[document]':
            result = []
        else:
            result = [tag.name]

        attrs = tag.attrs.copy()

        if 'id' in attrs:
            result.append(f'#{attrs.pop("id")}')

        if 'class' in attrs:
            result.append(''.join(f'.{cn}' for cn in attrs.pop('class').split()))

        if attrs:
            if len(attrs) < 3:
                attr_str = ", ".join(self.format_attribute(k, v) for k, v in attrs.items())
                result.append(f'({attr_str})')
            else:
                attr_str = add_tab("\n".join(self.format_attribute(k, v) for k, v in attrs.items()))
                result.append(f'(\n{attr_str})')

        children = (child for child in tag.children if not (isinstance(child, str) and child.isspace()))

        for (index, child) in enumerate(children):
            if isinstance(child, Tag):
                if index != 0:
                    result.append('\n')
                result.append('\n' + add_tab(self.format_tag(child)))
            elif isinstance(child, str):
                result.append('\n' + self.format_text(child))
            else:
                result.append(str(child))

        return ''.join(result)

    def format_text(self, text: str):
        return '\n'.join('    | ' + line for line in text.strip().splitlines())
