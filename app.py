import os
import pandas as pd
from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

app = Flask(__name__)
CSV_PATH = 'destinos.csv'

# --- CONFIGURAÇÕES DE FONTE ---
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
    print("--- SUCESSO: Fontes carregadas ---")
except Exception as e:
    print(f"!!! ERRO CRÍTICO: Não foi possível carregar fontes: {e} !!!")

# --- FUNÇÃO PARA CARREGAR DADOS ---
def carregar_dataframe():
    if not os.path.exists(CSV_PATH):
        print(f"!!! ERRO CRÍTICO: Arquivo '{CSV_PATH}' não encontrado. !!!")
        return pd.DataFrame() # Retorna um DataFrame vazio
    return pd.read_csv(CSV_PATH)

# --- ROTA PRINCIPAL (GERAR ETIQUETAS) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    df = carregar_dataframe()
    # Verifica se o DataFrame não está vazio e tem a coluna 'sigla'
    if not df.empty and 'sigla' in df.columns:
        df = df.dropna(subset=['sigla'])
        destinos_dict = df.set_index('sigla').to_dict('index')
    else:
        destinos_dict = {}

    if request.method == 'POST':
        if not destinos_dict:
            return "Erro: A base de dados de destinos está vazia ou não pôde ser carregada."

        sigla = request.form.get('sigla').upper()
        quantidade = int(request.form.get('quantidade'))
        
        if sigla not in destinos_dict:
            return f"Erro: Sigla '{sigla}' não encontrada na base de dados."

        dados_recebedor = destinos_dict[sigla]
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(150 * mm, 100 * mm))
        styles = getSampleStyleSheet()
        style_normal = ParagraphStyle(name='Normal', parent=styles['Normal'], fontName='Arial', fontSize=11, leading=13, alignment=TA_LEFT)
        
        for i in range(1, quantidade + 1):
            margem_h = 5 * mm
            largura_maxima = 140 * mm
            c.setFont('Arial-Bold', 56)
            c.drawString(margem_h, 75 * mm, sigla)
            numero_str = f"#{i}"
            c.setFont('Arial-Bold', 49)
            largura_texto_num = c.stringWidth(numero_str, 'Arial-Bold', 49)
            c.drawString((150 * mm) - margem_h - largura_texto_num, 75 * mm, numero_str)
            c.setFont('Arial-Bold', 46)
            c.drawString(margem_h, 55 * mm, "Overpack used")
            expedidor_text = "<b>EXPEDIDOR:</b> NEW POST LOGISTICA ENDEREÇO: R UBALDO FAGGEANI, 355,0 - JARDIM RESIDENCIAL LAS PALMAS MUNICÍPIO: PORTO FERREIRA - SP CEP: 13660-000 CNPJ/CPF: 28.678.104/0001-79 IE: 555074223110 UF: SP PAÍS: BRASIL"
            recebedor_text = f"<b>RECEBEDOR:</b> {dados_recebedor['nome_recebedor']} CNPJ {dados_recebedor['cnpj_recebedor']} ENDEREÇO: {dados_recebedor['endereco_recebedor']}, {dados_recebedor['cidade_recebedor']} - {dados_recebedor['uf_recebedor']} CEP: {dados_recebedor['cep_recebedor']}"
            p_expedidor = Paragraph(expedidor_text, style_normal)
            p_expedidor.wrapOn(c, largura_maxima, 40 * mm)
            p_expedidor.drawOn(c, margem_h, 28 * mm)
            p_recebedor = Paragraph(recebedor_text, style_normal)
            p_recebedor.wrapOn(c, largura_maxima, 20 * mm)
            p_recebedor.drawOn(c, margem_h, 5 * mm)
            c.showPage()
        
        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f'etiquetas_{sigla}.pdf', mimetype='application/pdf')

    return render_template('index.html', destinos=destinos_dict.keys())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)