"""Adapt the retained public example to the qualified native package profile, offline."""
import argparse
import copy
import hashlib
import io
import json
import math
import pathlib
import zipfile

from lxml import etree
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTENT_TYPES = 'http://schemas.openxmlformats.org/package/2006/content-types'
WORD = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def build(source, destination):
    source, destination = source.resolve(), destination.resolve()
    if destination.exists() or not destination.is_relative_to(ROOT / 'build'):
        raise ValueError('Require a fresh ignored candidate path; never overwrite the public template')
    with zipfile.ZipFile(source) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    document = etree.fromstring(parts['word/document.xml'])
    original_text = tuple(document.itertext())
    removed_grids = 0
    for grid in document.iter('{' + WORD + '}docGrid'):
        if grid.get('{' + WORD + '}type') not in (None, 'default'):
            raise ValueError('Do not remove an active document grid')
        grid.getparent().remove(grid)
        removed_grids += 1
    removed_unstyled_looks = 0
    for properties in document.iter('{' + WORD + '}tblPr'):
        for look in properties.findall('{' + WORD + '}tblLook'):
            if properties.find('{' + WORD + '}tblStyle') is not None:
                raise ValueError('Do not discard conditional table styling')
            properties.remove(look)
            removed_unstyled_looks += 1
        table = properties.getparent()
        for row in table.findall('{' + WORD + '}tr'):
            row_properties = row.find('{' + WORD + '}trPr')
            if row_properties is None:
                row_properties = etree.Element('{' + WORD + '}trPr')
                row.insert(0, row_properties)
            for repeat in row_properties.findall('{' + WORD + '}tblHeader'):
                row_properties.remove(repeat)
            nonsplit = row_properties.find('{' + WORD + '}cantSplit')
            if nonsplit is None:
                nonsplit = etree.SubElement(row_properties, '{' + WORD + '}cantSplit')
            nonsplit.set('{' + WORD + '}val', '1')
        cells = table.findall('{' + WORD + '}tr/' + '{' + WORD + '}tc/' + '{' + WORD + '}tcPr')
        for cell in cells:
            for tag in ('tcMar', 'tcBorders'):
                declarations = cell.findall('{' + WORD + '}' + tag)
                if declarations and any(etree.tostring(node, method='c14n') != etree.tostring(declarations[0], method='c14n') for node in declarations):
                    raise ValueError('Conflicting duplicate example cell properties require author review')
                for duplicate in declarations[1:]:
                    cell.remove(duplicate)
        margins = [cell.find('{' + WORD + '}tcMar') for cell in cells]
        def margin_values(node):
            return {etree.QName(edge).localname: dict(edge.attrib) for edge in node} if node is not None else None
        if not margins or margins[0] is None or any(margin_values(node) != margin_values(margins[0]) for node in margins):
            raise ValueError('This authored example requires identical explicit cell margins')
        properties.append(copy.deepcopy(margins[0]))
        properties[-1].tag = '{' + WORD + '}tblCellMar'
        for cell, margins_node in zip(cells, margins):
            cell.remove(margins_node)
            for shading in cell.findall('{' + WORD + '}shd'):
                if shading.get('{' + WORD + '}color') is None:
                    shading.set('{' + WORD + '}color', 'auto')
            order = ('tcW', 'gridSpan', 'vMerge', 'tcBorders', 'shd', 'vAlign')
            if any(etree.QName(node).localname not in order for node in cell):
                raise ValueError('Unexpected example cell properties require author review: ' + ', '.join(etree.QName(node).localname for node in cell))
            cell[:] = sorted(cell, key=lambda node: order.index(etree.QName(node).localname))
        if properties.find('{' + WORD + '}tblInd') is None:
            indent = etree.SubElement(properties, '{' + WORD + '}tblInd')
            indent.set('{' + WORD + '}w', '0')
            indent.set('{' + WORD + '}type', 'dxa')
        if properties.find('{' + WORD + '}tblBorders') is None:
            borders = etree.SubElement(properties, '{' + WORD + '}tblBorders')
            # All existing cells already use this same half-point solid border.
            for cell in cells:
                edges = cell.find('{' + WORD + '}tcBorders')
                if edges is None or any(dict(edge.attrib) != {'{' + WORD + '}val': 'single', '{' + WORD + '}sz': '4', '{' + WORD + '}color': 'D9D9D9'} for edge in edges):
                    raise ValueError('Do not replace differing cell borders with uniform defaults')
            for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
                rule = etree.SubElement(borders, '{' + WORD + '}' + edge)
                for key, value in dict(val='single', sz='4', color='D9D9D9').items():
                    rule.set('{' + WORD + '}' + key, value)
        order = ('tblStyle', 'tblW', 'tblInd', 'tblBorders', 'tblLayout', 'tblCellMar')
        if any(etree.QName(node).localname not in order for node in properties):
            raise ValueError('Unexpected example table properties require author review')
        properties[:] = sorted(properties, key=lambda node: order.index(etree.QName(node).localname))
    image_line_boxes = []
    drawing = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
    for paragraph in document.iter('{' + WORD + '}p'):
        if any(etree.QName(parent).namespace == WORD and etree.QName(parent).localname == 'tc' for parent in paragraph.iterancestors()):
            properties = paragraph.find('{' + WORD + '}pPr')
            if properties is None:
                properties = etree.Element('{' + WORD + '}pPr')
                paragraph.insert(0, properties)
            widow = properties.find('{' + WORD + '}widowControl')
            if widow is None:
                widow = etree.Element('{' + WORD + '}widowControl')
                early = ('pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr')
                index = next((i for i, node in enumerate(properties) if etree.QName(node).localname not in early), len(properties))
                properties.insert(index, widow)
            widow.set('{' + WORD + '}val', '0')
        extents = paragraph.findall('.//' + drawing + 'extent')
        placeholder = '{image | image(60, 25, true)}' in ''.join(paragraph.itertext())
        if not extents and not placeholder:
            continue
        height = 90 if placeholder else max(16, math.ceil(max(int(node.get('cy')) / 12700 for node in extents) / 0.8))
        properties = paragraph.find('{' + WORD + '}pPr')
        if properties is None:
            properties = etree.Element('{' + WORD + '}pPr')
            paragraph.insert(0, properties)
        spacing = properties.find('{' + WORD + '}spacing')
        if spacing is None:
            spacing = etree.SubElement(properties, '{' + WORD + '}spacing')
        spacing.set('{' + WORD + '}line', str(height * 20))
        spacing.set('{' + WORD + '}lineRule', 'exact')
        image_line_boxes.append(height)
    assert tuple(document.itertext()) == original_text
    parts['word/document.xml'] = etree.tostring(document, encoding='UTF-8', xml_declaration=True, standalone=True)
    removed = {'docProps/thumbnail.jpeg', 'word/stylesWithEffects.xml'} & parts.keys()
    for name in removed:
        del parts[name]
    renamed = {}
    for name in list(parts):
        if name.startswith('word/media/') and name.lower().endswith(('.jpg', '.jpeg')):
            target = str(pathlib.PurePosixPath(name).with_suffix('.png'))
            if target in parts:
                raise ValueError('Conflicting image name')
            with Image.open(io.BytesIO(parts[name])) as picture:
                pixels = picture.convert('RGB')
                output = io.BytesIO()
                pixels.save(output, format='PNG')
                parts[target] = output.getvalue()
                with Image.open(io.BytesIO(parts[target])) as converted:
                    assert converted.convert('RGB').tobytes() == pixels.tobytes()
            del parts[name]
            renamed[name] = target
    for name, value in list(parts.items()):
        if not name.endswith('.rels'):
            continue
        root = etree.fromstring(value)
        changed = False
        for relationship in list(root):
            target = relationship.get('Target', '')
            if any(target.lstrip('/') == item or target == pathlib.PurePosixPath(item).name for item in removed):
                root.remove(relationship)
                changed = True
            for before, after in renamed.items():
                for prefix in ('word/', ''):
                    old = before.removeprefix(prefix) if prefix else before
                    new = after.removeprefix(prefix) if prefix else after
                    if target == old:
                        relationship.set('Target', new)
                        changed = True
        if changed:
            parts[name] = etree.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
    root = etree.fromstring(parts['[Content_Types].xml'])
    for node in list(root):
        if node.get('PartName', '').lstrip('/') in removed or node.get('Extension') in ('jpg', 'jpeg'):
            root.remove(node)
    if not any(node.get('Extension') == 'png' for node in root):
        etree.SubElement(root, '{' + CONTENT_TYPES + '}Default', Extension='png', ContentType='image/png')
    parts['[Content_Types].xml'] = etree.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
    # Author modern, explicit print defaults instead of the starter's Word 2010
    # compatibility switches and web/save-preview settings. Review in real Word.
    settings = etree.Element('{' + WORD + '}settings', nsmap={'w': WORD})
    etree.SubElement(settings, '{' + WORD + '}defaultTabStop').set('{' + WORD + '}val', '720')
    compat = etree.SubElement(settings, '{' + WORD + '}compat')
    mode = etree.SubElement(compat, '{' + WORD + '}compatSetting')
    for key, value in dict(name='compatibilityMode', uri='http://schemas.microsoft.com/office/word', val='15').items():
        mode.set('{' + WORD + '}' + key, value)
    parts['word/settings.xml'] = etree.tostring(settings, encoding='UTF-8', xml_declaration=True, standalone=True)
    if 'word/webSettings.xml' in parts:
        parts['word/webSettings.xml'] = etree.tostring(etree.Element('{' + WORD + '}webSettings', nsmap={'w': WORD}), encoding='UTF-8', xml_declaration=True, standalone=True)
    styles = etree.fromstring(parts['word/styles.xml'])
    removed_style_metadata = []
    for style in styles.findall('{' + WORD + '}style'):
        for node in list(style):
            if etree.QName(node).namespace == WORD and etree.QName(node).localname in ('next', 'link', 'rsid', 'autoRedefine'):
                removed_style_metadata.append(etree.QName(node).localname)
                style.remove(node)
        if style.get('{' + WORD + '}styleId') == 'Title':
            for node in style.findall('.//' + '{' + WORD + '}pBdr'):
                node.getparent().remove(node)
            for tag in ('spacing', 'kern'):
                for node in style.findall('{' + WORD + '}rPr/' + '{' + WORD + '}' + tag):
                    node.getparent().remove(node)
        for properties in style.findall('{' + WORD + '}rPr'):
            size, complex_size = properties.find('{' + WORD + '}sz'), properties.find('{' + WORD + '}szCs')
            if size is not None and complex_size is not None:
                complex_size.set('{' + WORD + '}val', size.get('{' + WORD + '}val'))
    parts['word/styles.xml'] = etree.tostring(styles, encoding='UTF-8', xml_declaration=True, standalone=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(parts.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, value)
    record = dict(sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  candidateSha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                  removedUnusedParts=sorted(removed), losslessImageRenames=renamed,
                  authoredSettings='Word 2013 compatibility mode 15; 720-twip default tabs; no web/save-preview switches',
                  removedInactiveDocumentGrids=removed_grids,
                  removedUnstyledTableLook=removed_unstyled_looks,
                  bodyTextUnchanged=True, removedStyleEditingMetadata=sorted(set(removed_style_metadata)),
                  authoredTypography='Unbordered Title with ordinary character spacing and no explicit kerning; matching Latin/complex-script size declarations',
                  explicitTableDefaults='Hoisted identical 95-twip cell margins, existing half-point D9D9D9 borders and zero indent; explicit automatic shading foreground',
                  exactImageParagraphHeightsPt=image_line_boxes,
                  tableParagraphPolicy='Explicit widowControl off in cells; row pagination remains owned by the qualified table model',
                  exampleTablePolicy='Short non-splitting rows; no repeated-header flag, so the empty-list case can retain just its static header',
                  qualification='Pending native requests and genuine Word/render review')
    destination.with_suffix('.provenance.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print('Prepared native package candidate:', destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=pathlib.Path, default=ROOT / 'site/downloads/nuaforma-example-template.docx')
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    build(args.source, args.output)
