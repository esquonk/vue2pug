from html import unescape
from html.parser import HTMLParser, tagfind_tolerant, attrfind_tolerant


class Tag:
    def __init__(self, parent, name, attrs, self_closing):
        self.parent = parent
        self.attrs = attrs or {}
        self.name = name
        self.children = []
        self.self_closing = self_closing


class VueParser(HTMLParser, Tag):
    def __init__(self, *, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.parent = None
        self.name = "[document]"
        self.attrs = {}
        self.children = []
        self.current_tag = self
        self.self_closing = False

    def handle_starttag(self, tag, attrs):
        tagobj = Tag(self.current_tag, tag, dict(attrs), False)

        self.current_tag.children.append(tagobj)
        self.current_tag = tagobj

    def handle_endtag(self, tag):
        self.current_tag = self.current_tag.parent

    def handle_startendtag(self, tag, attrs):
        tagobj = Tag(self.current_tag, tag, dict(attrs), True)

        self.current_tag.children.append(tagobj)

    def handle_data(self, data):
        self.current_tag.children.append(data)

    def error(self, message):
        pass

    # quick and d
    def parse_starttag(self, i):
        self.__starttag_text = None
        endpos = self.check_for_whole_start_tag(i)
        if endpos < 0:
            return endpos
        rawdata = self.rawdata
        self.__starttag_text = rawdata[i:endpos]

        # Now parse the data between i+1 and j into a tag and attrs
        attrs = []
        match = tagfind_tolerant.match(rawdata, i + 1)
        assert match, 'unexpected call to parse_starttag()'
        k = match.end()
        self.lasttag = tag = match.group(1)
        while k < endpos:
            m = attrfind_tolerant.match(rawdata, k)
            if not m:
                break
            attrname, rest, attrvalue = m.group(1, 2, 3)
            if not rest:
                attrvalue = None
            elif attrvalue[:1] == '\'' == attrvalue[-1:] or \
                    attrvalue[:1] == '"' == attrvalue[-1:]:
                attrvalue = attrvalue[1:-1]
            if attrvalue:
                attrvalue = unescape(attrvalue)
            attrs.append((attrname, attrvalue))
            k = m.end()

        end = rawdata[k:endpos].strip()
        if end not in (">", "/>"):
            lineno, offset = self.getpos()
            if "\n" in self.__starttag_text:
                lineno = lineno + self.__starttag_text.count("\n")
                offset = len(self.__starttag_text) \
                         - self.__starttag_text.rfind("\n")
            else:
                offset = offset + len(self.__starttag_text)
            self.handle_data(rawdata[i:endpos])
            return endpos
        if end.endswith('/>'):
            # XHTML-style empty tag: <span attr="value" />
            self.handle_startendtag(tag, attrs)
        else:
            self.handle_starttag(tag, attrs)
            if tag in self.CDATA_CONTENT_ELEMENTS:
                self.set_cdata_mode(tag)
        return endpos
