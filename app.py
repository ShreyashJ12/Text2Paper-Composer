from flask import Flask, render_template, request, send_file
from docxtpl import DocxTemplate, InlineImage, RichText
from docx.shared import Mm
from io import BytesIO
import re

app = Flask(__name__)
doc = DocxTemplate("./word-template/template.docx")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_paper', methods=['POST'])
def generate_paper():
    # ----------------------Modify for Rich Text Fields----------------------#
    def match_pattern(s):
        pattern = re.compile(r'(\^\^\w+|__\w+)')
        matches = re.split(pattern, s)
        return [match for match in matches if match.strip()]

    def modify_text(text):
        if isinstance(text, str):
            text = [text]
        result = []
        for line in text:
            filtered_line = match_pattern(line)
            rt = RichText()
            for i in filtered_line:
                if i.startswith('^^'):
                    word = i.replace('^^', '')
                    rt.add(word, superscript=True)
                elif i.startswith('__'):
                    word = i.replace('__', '')
                    rt.add(word, subscript=True)
                else:
                    rt.add(i)
            result.append(rt)
        return result

    vol_inp = request.form.get('volume')
    month_inp = request.form.get('month')
    issue_inp = request.form.get('issuedate')
    issn_inp = request.form.get('issndate')
    title_inp = request.form.get('title')
    address_inp = request.form.get('address').split('\n')
    author_inp = request.form.get('authors')
    subdate_inp = request.form.get('sub_date')
    accdate_inp = request.form.get('acc_date')
    abstracts_inp = request.form.get('abstract')
    keywords_inp = request.form.get("keyword")
    page_inp = request.form.get("page_no")
    ref = request.form.get('reference').split('\n')

    sections_inp = []
    for i in range(1, int(request.form.get('sectionIndex'))):
        section_title = request.form.get(f'section_title_{i}')
        section_content = request.form.get(f'section_content_{i}')

        # Create a new section dictionary which will have table or image path afterwards
        section_data = [{
            'title': modify_text(section_title)[0],
            'text': modify_text(section_content)[0],
        }]

        added_fields = request.form.get(f'field_index_{i}')
        if added_fields and int(added_fields) > 0:
            elements = request.form.get(f'element_type_{i}').split(',')
            for j in range(0, int(added_fields) + 1):
                if elements[j] == 'table':
                    table_inp = request.form.get(f'section_table_{i}_{j}')
                    rows = table_inp.strip().split('\n') if table_inp else []
                    raw_data = [{'cols': row.strip().split('\t')} for row in rows]
                    element_dict = {'table': raw_data}
                    section_data.append(element_dict)
                elif elements[j] == 'image':
                    section_image = request.files.get(f'section_image_{i}_{j}')
                    image_path = f"uploads/section_image_{i}.jpg"
                    section_image.save(image_path)
                    element_dict = {'image_center': InlineImage(doc, image_path, width=Mm(100))}
                    section_data.append(element_dict)
        # Append section data to the list
        sections_inp.append(section_data)
    sections_inp.append([])



    context = {
        "vol": vol_inp,
        "issue": issue_inp,
        "address": modify_text(address_inp),
        "month": month_inp,
        "pp": page_inp,
        "issn": issn_inp,
        "title": modify_text(title_inp)[0],
        "authors": modify_text(author_inp)[0],
        "sub_date": subdate_inp,
        "acc_date": accdate_inp,
        "abstract": modify_text(abstracts_inp)[0],
        "keywords": modify_text(keywords_inp)[0],
        'sections': sections_inp,
        'references': modify_text(ref),
    }

    doc.render(context)

    output_stream = BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return send_file(
        output_stream,
        as_attachment=True,
        download_name='formatter_output.docx',
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    # doc.save("word-template-output.docx")
    # return send_file(doc, download_name="formatter_output.docx", as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
