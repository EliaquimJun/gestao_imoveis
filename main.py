import sys
import locale
import os
from PyQt5.QtWidgets import QFileDialog
import mysql.connector
from PyQt5 import QtCore, QtGui, QtWidgets
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
                             QLabel, QInputDialog, QListWidget, QHBoxLayout, QStackedWidget,
                             QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QCalendarWidget, QDialog, QDialogButtonBox,QGridLayout)

from PyQt5.QtGui import QBrush, QColor,QLinearGradient,QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QDialog, QFormLayout, QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QToolBar, QAction, QMenu, QMenuBar, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QCalendarWidget, QMessageBox, QGridLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QComboBox
import resources
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QDateEdit, QMessageBox
from PyQt5.QtCore import QDate


def conectar_mysql():
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='controle',
                password='123456',
                database='controle_gastos',
                auth_plugin='mysql_native_password',
                use_pure=True,
                client_flags=[mysql.connector.ClientFlag.LOCAL_FILES]
            )
            return conn
        except mysql.connector.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            return None
def criar_tabelas_mysql(conn):
    cursor = conn.cursor()

   # Tabela de imóveis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS imoveis (
            cod_imovel CHAR(5) ,
            nome VARCHAR(30) NOT NULL,
            endereco VARCHAR(60) NOT NULL,
            PRIMARY KEY (cod_imovel, endereco)
        )
    ''')

    # Tabela de itens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item VARCHAR(20) NOT NULL,
            forma_pg CHAR(20) NOT NULL,
            valor DECIMAL(10, 2) NOT NULL,
            data DATE NOT NULL,
            cod_imovel char(5),
            FOREIGN KEY (cod_imovel) REFERENCES imoveis (cod_imovel)
        )
    ''')

    # Tabela de proprietários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proprietarios (
            cpf CHAR(11) PRIMARY KEY,
            nome VARCHAR(50) NOT NULL,
            email VARCHAR(50),
            telefone CHAR(15)
        )
    ''')

    # Tabela de contratos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            codigo_contrato INT AUTO_INCREMENT PRIMARY KEY,
            cod_imovel char(5),
            cpf_proprietario CHAR(11),
            tipo_contrato ENUM('aluguel', 'venda') NOT NULL,
            data_inicio DATE NOT NULL,
            data_fim DATE,
            valor DECIMAL(10, 2) NOT NULL,
            status ENUM('ativo', 'concluido', 'cancelado') NOT NULL,
            FOREIGN KEY (cod_imovel) REFERENCES imoveis (cod_imovel),
            FOREIGN KEY (cpf_proprietario) REFERENCES proprietarios (cpf)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS imovel_proprietario (
            cod_imovel char(5),
            cpf_proprietario CHAR(11),
            PRIMARY KEY (cod_imovel, cpf_proprietario),
            FOREIGN KEY (cod_imovel) REFERENCES imoveis (cod_imovel) ON DELETE CASCADE,
            FOREIGN KEY (cpf_proprietario) REFERENCES proprietarios (cpf) ON DELETE CASCADE
        );
    ''')
    conn.commit()


class Imovel:
    def __init__(self, nome):
        self.nome = nome
        self.gastos = []

    def adicionar_gasto(self, item, forma_pagamento, valor, data):
        
        id_imovel = self.obter_id_imovel(self.nome)
        if id_imovel is not None:
            conn = conectar_mysql()
            if conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO itens (item, forma_pg, valor, data, cod_imovel)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (item, forma_pagamento, valor, data, id_imovel))
                conn.commit()
                conn.close()

    def obter_id_imovel(self, nome_imovel):
        conn = conectar_mysql()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT cod_imovel FROM imoveis WHERE nome = %s', (nome_imovel,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return result[0]  # Retorna o ID encontrado
        return None  # Retorna None se o imóvel não for encontrado

    def total_gastos(self):
        return sum(valor for item, valor, data in self.gastos)


class AdicionarProprietarioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Cliente")
        self.setGeometry(100, 100, 300, 300)
        layout = QFormLayout(self)

        self.nome_input = QLineEdit(self)
        self.cpf_input = QLineEdit(self)
        self.email_input = QLineEdit(self)
        self.telefone_input = QLineEdit(self)
        salvar_btn = QPushButton("Salvar", self)
        salvar_btn.clicked.connect(self.salvar_proprietario)

        layout.addRow("Nome:", self.nome_input)
        layout.addRow("CPF:", self.cpf_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Telefone:", self.telefone_input)
        layout.addWidget(salvar_btn)

    def salvar_proprietario(self):
        nome = self.nome_input.text()
        cpf = self.cpf_input.text()
        email = self.email_input.text()
        telefone = self.telefone_input.text()

        conn = conectar_mysql()
        if conn:
            try:
                cursor = conn.cursor()
                query = "INSERT INTO proprietarios (nome, cpf, email, telefone) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (nome, cpf, email, telefone))
                conn.commit()
                QMessageBox.information(self, "Sucesso", "Proprietário adicionado com sucesso!")
                
            except mysql.connector.Error as e:
                QMessageBox.warning(self, "Erro", f"Erro ao adicionar proprietário: {e}")
            finally:
                cursor.close()
                conn.close()
            self.close()


        
class GerenciarContratosDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Contratos")
        self.setGeometry(100, 100, 500, 400)
        self.layout = QVBoxLayout()
        
        self.addButton = QPushButton("Adicionar Contrato")
        self.addButton.clicked.connect(self.adicionar_contrato)
        self.layout.addWidget(self.addButton)
        
        self.setLayout(self.layout)
    
    def adicionar_contrato(self, id_imovel, cpf_proprietario, tipo_contrato, data_inicio, data_fim, valor, status):
        conn = conectar_mysql()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO contratos (id_imovel, cpf_proprietario, tipo_contrato, data_inicio, data_fim, valor, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (id_imovel, cpf_proprietario, tipo_contrato, data_inicio, data_fim, valor, status))
                conn.commit()
            finally:
                conn.close()

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.imoveis = {}
        self.initUI()
        self.imovel_selecionado = None 
        self.cod_imovel_selecionado = None  # Novo atributo para armazenar o ID
        self.mostrando_imoveis = False
        self.itens_imoveis = []
        self.carregar_imoveis()
        self.btn_adicionar_gasto.hide()
        self.btn_ver_gastos.hide()
        self.gerenciar_proprietarios_dialog = None
     

        
    def initUI(self):
        
        self.setWindowTitle('Controle de Gastos de Imóveis')
        self.setGeometry(0, 0, 1920, 1080)
        
        
        # Maximizar a janela ao iniciar
        self.showMaximized()

                # Criar a barra de menu
        self.menubar = QMenuBar(self)
        self.setMenuBar(self.menubar)
        

        # Criar o menu "Opções"
        self.menuOpcoes = QMenu("Opções", self)
        self.menubar.addMenu(self.menuOpcoes)

        # Criar a barra de ferramentas
        self.toolBar = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.toolBar)

        # Criar ações
        self.action_procurar = QAction(QIcon(":/main(images)/buscar.png"), "Procurar", self)
        self.action_cadastrar = QAction(QIcon(":/main(images)/create.png"), "Cadastrar", self)
        self.action_apagar = QAction(QIcon(":/main(images)/delete.png"), "Apagar", self)
        self.action_atualizar = QAction(QIcon(":/main(images)/refresh.png"), "Atualizar", self)
        
         # Conectar a ação "Apagar" com o método de apagar imóvel
        # Definir atalhos de teclado
        self.action_apagar.setShortcut("delete")
        self.action_atualizar.setShortcut("Ctrl+S")
        self.action_procurar.setShortcut("Ctrl+F")
        self.action_cadastrar.setShortcut("Ctrl+A")

        # Conectar a ação "Apagar" com o método de apagar imóvel
        self.action_apagar.triggered.connect(self.apagar_imovel)

        self.action_procurar.triggered.connect(self.toggle_search)


        # Conectar a ação "Atualizar" com o método de carregar imóveis
        self.action_atualizar.triggered.connect(self.atualizar_lista_imoveis)
        self.action_cadastrar.triggered.connect(self.setup_adicionar_imovel_widget)
        
        
        # Adicionar ações à barra de ferramentas e ao menu
        self.toolBar.addAction(self.action_procurar)
        self.toolBar.addAction(self.action_cadastrar)
        self.toolBar.addAction(self.action_apagar)
        self.toolBar.addAction(self.action_atualizar)

        self.menuOpcoes.addAction(self.action_procurar)
        self.menuOpcoes.addAction(self.action_cadastrar)
        self.menuOpcoes.addAction(self.action_apagar)
        self.menuOpcoes.addAction(self.action_atualizar)

        # Definir dicas de ferramentas para ações
        self.action_procurar.setToolTip("Procurar Imóvel")
        self.action_cadastrar.setToolTip("Cadastrar Imóvel")
        self.action_apagar.setToolTip("Apagar Imóvel")
        self.action_atualizar.setToolTip("Atualizar Tela")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.header = QLabel('CONTROLE DE GASTOS', self.central_widget)
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("font: bold 20pt \"HP Segoe UI Variable Small\";\n"
"color: rgb(255, 255, 255);\n"
"\n"
"\n"
"background-color: qlineargradient(spread:reflect, x1:0.284, y1:0.948636, x2:1, y2:0.916, stop:0.4375 rgba(0, 0, 64, 255), stop:0.568182 rgba(0, 0, 93, 255), stop:0.670455 rgba(0, 0, 102, 255), stop:0.789773 rgba(0, 18, 117, 255), stop:0.954545 rgba(0, 57, 142, 255), stop:1 rgba(0, 81, 127, 255));\n"
"border-top-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 255), stop:1 rgba(255, 255, 255, 255));\n"

"")
        self.header.setFixedHeight(70)
        self.header.setFont(QFont('Arial', 16))
        self.main_layout.addWidget(self.header)
        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)
        
        self.navbar = QListWidget()

        
        self.navbar.setMaximumWidth(320)
        # Estilizar o NavBar
        self.navbar.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;  # Cor de fundo mais suave
                border: none;  # Remover bordas
                padding: 10px;  # Espaçamento interno
                font-family: Arial;  # Tipo de fonte
            }
            QListWidget::item {
                border-bottom: 1px solid #e0e0e0;  # Linha separadora
                font-family: Arial;  # Tipo de fonte para os itens
                font-size: 12pt;  # Tamanho da fonte
                color: #333;  # Cor da fonte
            }
            QListWidget::item:hover {
                background-color: #d3d3d3;  # Cor de fundo ao passar o mouse
            }
            QPushButton {
                background-color: #4CAF50;  # Cor do botão
                color: white;  # Cor do texto
                border-radius: 5px;  # Bordas arredondadas
                padding: 10px;  # Espaçamento interno
                margin: 5px;  # Espaçamento externo
            }
            QPushButton:hover {
                background-color: #45a049;  # Cor do botão ao passar o mouse
            }
        """)

        self.navbar.currentItemChanged.connect(self.imovel_selecionado)
   
        self.content_layout.addWidget(self.navbar)

        self.navbar_header = QListWidgetItem('IMÓVEIS')
        self.navbar_header.setFont(QFont("Segoe UI Variable Small bold", 14))
        
        
        
        # Criar um gradiente linear
        gradient = QLinearGradient(0, 0, 0, 40)  # Gradiente vertical
        gradient.setColorAt(0.4375, QColor(0, 0, 64))
        gradient.setColorAt(0.568182, QColor(0, 0, 93))
        gradient.setColorAt(0.670455, QColor(0, 0, 102))
        gradient.setColorAt(0.789773, QColor(0, 18, 117))
        gradient.setColorAt(0.954545, QColor(0, 57, 142))
        gradient.setColorAt(1, QColor(0, 81, 127))

        # Definir o gradiente como fundo do QListWidgetItem
        self.navbar_header.setBackground(QBrush(gradient))
        self.navbar_header.setForeground(Qt.white)  # Define a cor do texto para branco
        
        self.navbar_header.setSizeHint(QSize(200, 60))
        self.navbar_header.setTextAlignment(Qt.AlignCenter) 
        self.navbar.addItem(self.navbar_header)
        
        # Criação do QLineEdit para pesquisa
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisa por nome")
        self.search_input.setFixedHeight(20)
        self.search_input.hide()  # Inicialmente oculto



        # Conectar o sinal textChanged do QLineEdit ao método filter_imoveis
        self.search_input.textChanged.connect(self.filter_imoveis)



        
        self.adicionar_imovel_item = QListWidgetItem(self.navbar)
        self.adicionar_imovel_item.setFont(QFont("Arial", 24))
        
        self.navbar.addItem(self.adicionar_imovel_item)
        self.adicionar_imovel_btn = QPushButton('Adicionar Imóvel', self.navbar)
        self.adicionar_imovel_btn.setStyleSheet("background-color: lightblue; color: black;")
        self.adicionar_imovel_btn.setFont(QFont( "HP Segoe UI Variable Small", 12))
        self.adicionar_imovel_btn.clicked.connect(self.mostrar_adicionar_imovel)
        self.navbar.setItemWidget(self.adicionar_imovel_item, self.adicionar_imovel_btn)

        
        
        # Adicionar botão 'Adicionar Proprietário' logo abaixo de 'Adicionar Imóvel'
        self.adicionar_proprietario_item = QListWidgetItem("Adicionar Cliente", self.navbar)
        self.adicionar_proprietario_item.setFont(QFont("Arial", 20))
        self.adicionar_proprietario_btn = QPushButton("Adicionar Cliente", self.navbar)
        self.adicionar_proprietario_btn.setStyleSheet("background-color: lightblue; color: black;")
        self.adicionar_proprietario_btn.setFont(QFont( "HP Segoe UI Variable Small", 12))
        self.adicionar_proprietario_btn.clicked.connect(self.mostrar_adicionar_proprietario)
        self.navbar.setItemWidget(self.adicionar_proprietario_item, self.adicionar_proprietario_btn)

        self.meus_imoveis_item = QListWidgetItem(self.navbar)
        self.meus_imoveis_item.setFont(QFont("Arial", 24))  

        self.navbar.addItem(self.meus_imoveis_item)
        self.meus_imoveis_btn = QPushButton('Meus Imóveis', self.navbar)
        self.meus_imoveis_btn.setStyleSheet("background-color: lightblue; color: black;")
        self.meus_imoveis_btn.setFont(QFont( "HP Segoe UI Variable Small", 12))
        self.meus_imoveis_btn.clicked.connect(self.mostrar_meus_imoveis)
        self.navbar.setItemWidget(self.meus_imoveis_item, self.meus_imoveis_btn)
        
        # Adicionar QLineEdit como um QListWidgetItem no navbar
        self.search_input_item = QListWidgetItem(self.navbar)
        self.navbar.setItemWidget(self.search_input_item, self.search_input)
        self.search_input_item.setSizeHint(self.search_input.sizeHint())
        
        self.search_input.setVisible(not self.search_input.isVisible())
        self.search_input_item.setHidden(not self.search_input.isVisible())
        
        self.stack = QStackedWidget()
        self.content_layout.addWidget(self.stack)
        
        self.tela_inicial = QWidget()

        self.label_tela_inicial = QLabel("Selecione um imóvel para ver ou adicionar gastos!", self.tela_inicial)
        self.label_tela_inicial.setAlignment(Qt.AlignCenter)
        self.label_tela_inicial.setGeometry(50,80,1600,600)
        self.label_tela_inicial.setStyleSheet("font: 75 48pt \"HP Simplified\";\n"
"color: #9b9b9b;\n"


"")
        self.stack.addWidget(self.tela_inicial)
        
         # Widget para adicionar proprietário
        self.adicionar_proprietario_widget = QWidget()
        self.setup_adicionar_imovel_widget()
        self.setup_adicionar_proprietario_widget()
        self.stack.addWidget(self.adicionar_proprietario_widget)
        
        self.tela_opcoes_imovel = QWidget()
        self.opcoes_imovel_layout = QVBoxLayout(self.tela_opcoes_imovel)
        self.opcoes_imovel_layout.setContentsMargins(200, 0, 400, 600)  # Ajustar margens conforme necessário
      
        self.stack.addWidget(self.tela_opcoes_imovel)

        # Criar um layout horizontal para os botões
        self.botoes_layout = QHBoxLayout()

        self.btn_adicionar_gasto = QPushButton('Adicionar Gasto', self.tela_opcoes_imovel)
        self.btn_adicionar_gasto.setFixedWidth(250)
        self.btn_adicionar_gasto.setFixedHeight(80)

        self.btn_adicionar_gasto.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_adicionar_gasto.setStyleSheet("background-color: qlineargradient(spread:reflect, x1:0.284, y1:0.948636, x2:1, y2:0.916, stop:0.4375 rgba(0, 0, 64, 255), stop:0.568182 rgba(0, 0, 93, 255), stop:0.670455 rgba(0, 0, 102, 255), stop:0.789773 rgba(0, 18, 117, 255), stop:0.954545 rgba(0, 57, 142, 255), stop:1 rgba(0, 81, 127, 255));\n"
"border-top-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 255), stop:1 rgba(255, 255, 255, 255));\n"
"\n"
"gridline-color: rgb(255, 255, 255);\n"
"color: rgb(255, 255, 255);\n"
"color: rgb(255, 255, 255);\n"
"\n"
 "border-radius: 5px;"
"font: 300 13pt \"Segoe UI Variable Small\";\n"
"")
        
        self.btn_adicionar_gasto.clicked.connect(self.mostrar_adicionar_gasto)
        self.btn_ver_gastos = QPushButton('Ver Gastos', self.tela_opcoes_imovel)
        self.btn_ver_gastos.setFixedWidth(250)
        self.btn_ver_gastos.setFixedHeight(80)
        self.btn_ver_gastos.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_ver_gastos.setStyleSheet("background-color: qlineargradient(spread:reflect, x1:0.284, y1:0.948636, x2:1, y2:0.916, stop:0.4375 rgba(0, 0, 64, 255), stop:0.568182 rgba(0, 0, 93, 255), stop:0.670455 rgba(0, 0, 102, 255), stop:0.789773 rgba(0, 18, 117, 255), stop:0.954545 rgba(0, 57, 142, 255), stop:1 rgba(0, 81, 127, 255));\n"
"border-top-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 255), stop:1 rgba(255, 255, 255, 255));\n"
"\n"
"gridline-color: rgb(255, 255, 255);\n"
"color: rgb(255, 255, 255);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 5px;"
"\n"
"font: 300 13pt \"Segoe UI Variable Small\";\n"
"")
        self.btn_ver_gastos.clicked.connect(self.mostrar_ver_gastos)
        
        
        
        # Adicionar botões ao layout horizontal
        self.botoes_layout.addWidget(self.btn_adicionar_gasto)
        self.botoes_layout.addWidget(self.btn_ver_gastos)
 # Botão para gerenciar proprietários
       
        
        self.btn_gerenciar_contratos = QPushButton('Gerenciar Contratos', self.tela_opcoes_imovel)
        self.btn_gerenciar_contratos.setFixedWidth(250)
        self.btn_gerenciar_contratos.setFixedHeight(80)
       
        self.btn_gerenciar_contratos.setStyleSheet("/* Seu estilo aqui */")
        self.btn_gerenciar_contratos.clicked.connect(self.abrir_gerenciar_contratos)
        self.btn_gerenciar_contratos.hide()  # Comece escondido
        self.botoes_layout.addWidget(self.btn_gerenciar_contratos)

        self.btn_gerenciar_contratos.setStyleSheet("background-color: qlineargradient(spread:reflect, x1:0.284, y1:0.948636, x2:1, y2:0.916, stop:0.4375 rgba(0, 0, 64, 255), stop:0.568182 rgba(0, 0, 93, 255), stop:0.670455 rgba(0, 0, 102, 255), stop:0.789773 rgba(0, 18, 117, 255), stop:0.954545 rgba(0, 57, 142, 255), stop:1 rgba(0, 81, 127, 255));\n"
        "border-top-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 255), stop:1 rgba(255, 255, 255, 255));\n"
        "\n"
        "gridline-color: rgb(255, 255, 255);\n"
        "color: rgb(255, 255, 255);\n"
        "color: rgb(255, 255, 255);\n"
        "border-radius: 5px;"
        "\n"
        "font: 300 13pt \"Segoe UI Variable Small\";\n"
        "")
        # Adicionar o layout horizontal ao layout vertical principal
        self.opcoes_imovel_layout.addLayout(self.botoes_layout)
        
        
        self.botao_voltar = self.criar_botao_voltar()
        self.botao_voltar.setStyleSheet("background-color: white; color: #000026; border-radius:5px;font: bold 14pt \"Segoe UI Variable Small\";")
        self.botao_voltar.setGeometry(240,82,70,35)
        self.botao_voltar.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.botao_voltar.hide()
        
        
        
# Inicialização do widget para Adicionar Gastos
        self.adicionar_gasto_widget = QWidget()
        self.adicionar_gasto_layout = QVBoxLayout(self.adicionar_gasto_widget)
        self.adicionar_gasto_layout.setSpacing(0)  # Reduzir o espaçamento entre sublayouts
        self.adicionar_gasto_layout.setContentsMargins(50, 30, 0, 400)  # Reduzir as margens do layout
        self.adicionar_gasto_widget.setMaximumWidth(400)


        # Defina a fonte que você deseja usar
        fonte_placeholder = QFont("Arial", 12)  # Altere "Arial" e "12" conforme necessário

        # Item Input
        self.item_input = QLineEdit(self.adicionar_gasto_widget)
        self.item_input.setPlaceholderText("Item")
        self.item_input.setFont(fonte_placeholder)  # Aplicar a fonte ao QLineEdit
        self.item_input.setFixedHeight(70)
        self.adicionar_gasto_layout.addWidget(self.item_input)

        # Forma de Pagamento
        self.forma_pagamento_input = QLineEdit(self.adicionar_gasto_widget)
        self.forma_pagamento_input.setPlaceholderText("Forma de pagamento")
        self.forma_pagamento_input.setFont(fonte_placeholder)  # Aplicar a fonte ao QComboBox
        self.forma_pagamento_input.setFixedHeight(70)
        self.adicionar_gasto_layout.addWidget(self.forma_pagamento_input)

        # Valor Input
        self.valor_input = QLineEdit(self.adicionar_gasto_widget)
        self.valor_input.setPlaceholderText("Valor")
        self.valor_input.setFont(fonte_placeholder)  # Aplicar a fonte ao QLineEdit
        self.valor_input.setFixedHeight(70)
        self.adicionar_gasto_layout.addWidget(self.valor_input)

        # Data Input
        self.data_input = QLineEdit(self.adicionar_gasto_widget)
        self.data_input.setPlaceholderText("Data (YYYY-MM-DD)")
        self.data_input.setFont(fonte_placeholder)  # Aplicar a fonte ao QLineEdit
        self.data_input.setFixedHeight(70)
        self.data_input.mousePressEvent = self.mostrar_calendario
        self.data_input.hide()  # Ocultar o campo de entrada de data inicialmente
        self.adicionar_gasto_layout.addWidget(self.data_input)




    
        # Inicialização do widget para Ver Gastos
        self.mostrar_gastos_widget = QWidget()
        self.mostrar_gastos_layout = QVBoxLayout(self.mostrar_gastos_widget)

        # Adicionar QLabel na tela de Ver Gastos
        self.nome_imovel_label_ver = QLabel("Selecione um imóvel", self.mostrar_gastos_widget)
        self.nome_imovel_label_ver.setFont(QFont('Arial', 12))
        self.mostrar_gastos_layout.addWidget(self.nome_imovel_label_ver, 0, Qt.AlignTop)
        
        self.stack.addWidget(self.adicionar_gasto_widget)
        


        
        self.adicionar_gasto_widget.setStyleSheet("""
            QLineEdit {
                border: 1px solid #BDBDBD;
                border-radius: 5px;
                padding: 20px;
                height:20px;
    

                
            }
            
            QComboBox{
                border: 1px solid #BDBDBD;
                border-radius: 5px;
                padding: 20px;
                height:20px;
    

                
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 5px;
                color: white;
                padding: 20px 15px;
                text-align: center;
               
            
                text-decoration: none;
        
                font-size: 16px;
                margin: 4px 2px;
         
            }

        """)
        
        # Primeiro, crie um widget para o card e defina o seu layout
        self.card_widget = QWidget(self.adicionar_gasto_widget)
        self.card_layout = QVBoxLayout(self.card_widget)

        # Ajuste do layout de adicionar gastos
        self.adicionar_gasto_layout.setSpacing(2)  # Define o espaçamento entre os widgets

        # Adicionando a legenda para o campo "Item" e o próprio campo
        item_label = QLabel("Item:", self.adicionar_gasto_widget)
        self.adicionar_gasto_layout.addWidget(item_label)
        self.adicionar_gasto_layout.addWidget(self.item_input)
        self.adicionar_gasto_layout.addStretch(1)  # Adiciona um espaço expansível
        

        # Adicionando a legenda para o campo "Forma de Pagamento"
        forma_pagamento_label = QLabel("Forma de Pagamento:", self.adicionar_gasto_widget)
        self.adicionar_gasto_layout.addWidget(forma_pagamento_label)
        self.adicionar_gasto_layout.addWidget(self.forma_pagamento_input)
        self.adicionar_gasto_layout.addStretch(1)  # Adiciona um espaço expansível
        # Adicionando a legenda para o campo "Valor"
        valor_label = QLabel("Valor:", self.adicionar_gasto_widget)
        self.adicionar_gasto_layout.addWidget(valor_label)
        self.adicionar_gasto_layout.addWidget(self.valor_input)
        self.adicionar_gasto_layout.addStretch(1)  # Adiciona um espaço expansível
        # Adicionando a legenda para o campo "Data"
        data_label = QLabel("Data:", self.adicionar_gasto_widget)
        self.adicionar_gasto_layout.addWidget(data_label)
        self.adicionar_gasto_layout.addWidget(self.data_input)
        self.adicionar_gasto_layout.addStretch(1)  # Adiciona um espaço expansível

        self.confirmar_gasto_btn = QPushButton('Confirmar', self.adicionar_gasto_widget)
        self.confirmar_gasto_btn.setFixedHeight(80)
        self.confirmar_gasto_btn.setFont(QFont("Arial",35))
        self.confirmar_gasto_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.confirmar_gasto_btn.clicked.connect(self.confirmar_gasto)
        self.adicionar_gasto_layout.addWidget(self.confirmar_gasto_btn)
        
        self.mostrar_gastos_widget = QWidget()
        self.mostrar_gastos_layout = QVBoxLayout(self.mostrar_gastos_widget)
        self.stack.addWidget(self.mostrar_gastos_widget)
        self.tabela_gastos = QTableWidget(0, 4, self.mostrar_gastos_widget)
        self.tabela_gastos.itemClicked.connect(self.on_table_item_selected)
        self.tabela_gastos.itemChanged.connect(self.on_item_changed)


        self.tabela_gastos.setHorizontalHeaderLabels(["Data","Item", "Forma de pagamento", "Valor"])
        self.tabela_gastos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_gastos.horizontalHeader().setStyleSheet(
    "QHeaderView::section {"
    "    border-bottom: 1px solid #a0a0a0;"
    "    padding: 4px;"
    "    font:  14pt \"HP Segoe UI Variable Small\";"
    "    background-color: white;"

    "    color: black;"
     
    "}"
)

        self.mostrar_gastos_layout.addWidget(self.tabela_gastos)
        self.total_label = QLabel("Total: R$0.00", self.mostrar_gastos_widget)
        self.total_label.setStyleSheet("font:  12pt \"HP Simplified\";")
        self.mostrar_gastos_layout.addWidget(self.total_label)

         # Adicionar o botão à interface
        botao_gerar_pdf = QPushButton('Gerar PDF', self)
        botao_gerar_pdf.clicked.connect(self.gerar_pdf)
        self.mostrar_gastos_layout.addWidget(botao_gerar_pdf)
        self.show()
        
    def carregar_proprietarios(self):
        conn = conectar_mysql()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome FROM proprietarios")
                while True:
                    row = cursor.fetchone()
                    if row is None:
                        break
                    self.proprietario_combo.addItem(row[1], row[0])
            finally:
                cursor.close()
                conn.close()
            
    def setup_adicionar_imovel_widget(self):
        # Criação do widget que será usado para adicionar imóveis
        self.adicionar_imovel_widget = QWidget()
        layout = QVBoxLayout(self.adicionar_imovel_widget)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)
        
        # Estilizar os labels e inputs
        label_style = "font-size: 14pt; font-weight: bold; color: #333;"
        input_style = "font-size: 12pt; padding: 10px;"

        # Entrada para o código do imóvel
        cod_imovel_layout = QVBoxLayout()
        cod_imovel_label = QLabel("Código do Imóvel:")
        cod_imovel_label.setStyleSheet(label_style)
        self.cod_imovel_input = QLineEdit()
        self.cod_imovel_input.setFixedHeight(40)
        self.cod_imovel_input.setPlaceholderText("Digite o código do imóvel aqui")
        self.cod_imovel_input.setStyleSheet(input_style)
        cod_imovel_layout.addWidget(cod_imovel_label)
        cod_imovel_layout.addWidget(self.cod_imovel_input)

        # Entrada para o nome do imóvel
        nome_layout = QVBoxLayout()
        nome_label = QLabel("Nome do Imóvel:")
        nome_label.setStyleSheet(label_style)
        self.nome_imovel_input = QLineEdit()
        self.nome_imovel_input.setFixedHeight(40)
        self.nome_imovel_input.setPlaceholderText("Digite o nome do imóvel aqui")
        self.nome_imovel_input.setStyleSheet(input_style)
        nome_layout.addWidget(nome_label)
        nome_layout.addWidget(self.nome_imovel_input)

        # Entrada para o endereço do imóvel
        endereco_layout = QVBoxLayout()
        endereco_label = QLabel("Endereço do Imóvel:")
        endereco_label.setStyleSheet(label_style)
        self.endereco_imovel_input = QLineEdit()
        self.endereco_imovel_input.setFixedHeight(40)
        self.endereco_imovel_input.setPlaceholderText("Digite o endereço do imóvel aqui")
        self.endereco_imovel_input.setStyleSheet(input_style)
        endereco_layout.addWidget(endereco_label)
        endereco_layout.addWidget(self.endereco_imovel_input)

        # ComboBox para seleção do proprietário
        proprietario_layout = QVBoxLayout()
        proprietario_label = QLabel("Proprietário:")
        proprietario_label.setStyleSheet(label_style)
        self.proprietario_combo = QComboBox()
        self.proprietario_combo.setStyleSheet(input_style)
        self.carregar_proprietarios()  # Este método deve carregar os proprietários no QComboBox
        proprietario_layout.addWidget(proprietario_label)
        proprietario_layout.addWidget(self.proprietario_combo)

        # Botão para salvar o imóvel
        salvar_imovel_btn = QPushButton("Salvar Imóvel")
        salvar_imovel_btn.setFixedHeight(40)
        salvar_imovel_btn.setStyleSheet("font-size: 14pt; font-weight: bold; color: white; background-color: #4CAF50; padding: 10px;")
        salvar_imovel_btn.clicked.connect(self.salvar_imovel)

        # Adicionando todos os layouts ao layout principal
        layout.addLayout(cod_imovel_layout)
        layout.addLayout(nome_layout)
        layout.addLayout(endereco_layout)
        layout.addLayout(proprietario_layout)
        layout.addWidget(salvar_imovel_btn, alignment=Qt.AlignCenter)

        # Adiciona o widget configurado ao stack
        self.stack.addWidget(self.adicionar_imovel_widget)


        
    def carregar_proprietarios(self):
        conn = conectar_mysql()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT cpf, nome FROM proprietarios')
                proprietarios = cursor.fetchall()
                self.proprietario_combo.clear()
                for row in proprietarios:
                    self.proprietario_combo.addItem(f"{row[1]} ({row[0]})", row[0])
            except mysql.connector.Error as e:
                QMessageBox.warning(self, "Erro", f"Erro ao carregar proprietários: {e}")
            finally:
                cursor.close()
                conn.close()


    def toggle_search(self):
        self.search_input.setVisible(not self.search_input.isVisible())
        self.search_input_item.setHidden(not self.search_input.isVisible())

        if self.search_input.isVisible():
            self.search_input.setFocus()  # Coloca o foco no campo de texto

        # Reiniciar a pesquisa quando ocultar/mostrar
        self.search_input.clear()
        self.filter_imoveis()

    def filter_imoveis(self):
        search_text = self.search_input.text().lower()
        
        # Em vez de limpar o navbar, altere a visibilidade dos itens
        self.navbar_header.setHidden(False)
        self.search_input_item.setHidden(not self.search_input.isVisible())
        self.adicionar_imovel_item.setHidden(False)
        self.meus_imoveis_item.setHidden(False)

        for nome_imovel in self.imoveis:
            item = self.navbar.findItems(nome_imovel, Qt.MatchExactly)
            if item:
                item[0].setHidden(not (search_text in nome_imovel.lower()))

  
        
    def gerenciar_contratos(self):
            if not self.gerenciar_contratos_dialog:
                self.gerenciar_contratos_dialog = GerenciarContratosDialog(self)
            self.gerenciar_contratos_dialog.show()
    
    def apagar_imovel(self):
            if self.tabela_gastos.currentRow() >= 0:
                self.apagar_item_gasto()
   
                
            elif self.imovel_selecionado:
                self.apagar_imovel_selecionado()
                self.carregar_imoveis()
            else:
                QMessageBox.warning(self, "Atenção", "É necessário selecionar um imóvel ou um item primeiro para deletar.")
                
                
    def atualizar_lista_imoveis(self):
        self.carregar_imoveis()
        QMessageBox.information(self, "Atualização", "Lista atualizada com sucesso.")
  

    def apagar_item_gasto(self):
        # Implementação para apagar o item de gasto selecionado
        row = self.tabela_gastos.currentRow()
        item_id = self.tabela_gastos.item(row, 0).data(Qt.UserRole)  # Supondo que o ID está armazenado como UserRole
        resposta = QMessageBox.question(self, "Confirmar Exclusão", "Tem certeza que deseja apagar este item ?", QMessageBox.Yes | QMessageBox.No)
        
        if resposta == QMessageBox.Yes:
            # Aqui você deverá implementar a lógica para apagar o item do banco de dados
            conn = conectar_mysql()
            if conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM itens WHERE id = %s', (item_id,))
                conn.commit()
                conn.close()
            self.atualizar_tabela_gastos(self.imovel_selecionado.nome)

    def apagar_imovel_selecionado(self):
            nome_imovel = self.imovel_selecionado.nome
            resposta = QMessageBox.question(self, "Confirmar Exclusão", f"Tem certeza que deseja apagar o imóvel '{nome_imovel}'?", QMessageBox.Yes | QMessageBox.No)
            
            if resposta == QMessageBox.Yes:
                self.excluir_imovel(nome_imovel)
                QMessageBox.information(self, 'Exclusão', f'Imóvel "{nome_imovel}" excluído com sucesso.')
                self.carregar_imoveis()

    def excluir_imovel(self, nome_imovel):
        conn = conectar_mysql()
        if conn:
            cursor = conn.cursor()
            try:
                # Primeiro, obtenha o código do imóvel
                cursor.execute('SELECT cod_imovel FROM imoveis WHERE nome = %s', (nome_imovel,))
                resultado = cursor.fetchone()
                if resultado is None:
                    raise ValueError(f"Imóvel com nome '{nome_imovel}' não encontrado.")
                
                cod_imovel = resultado[0]
                
                # Em seguida, exclua todos os itens de gasto associados a esse imóvel
                cursor.execute('DELETE FROM itens WHERE cod_imovel = %s', (cod_imovel,))
                conn.commit()  # Confirma a exclusão dos itens

                # Excluir as associações entre imóvel e proprietário
                cursor.execute('DELETE FROM imovel_proprietario WHERE cod_imovel = %s', (cod_imovel,))
                conn.commit()  # Confirma a exclusão das associações

                # Excluir o contrato associado ao imóvel
                cursor.execute('DELETE FROM contratos WHERE cod_imovel = %s', (cod_imovel,))
                conn.commit()  # Confirma a exclusão do contrato

                # Finalmente, exclua o imóvel
                cursor.execute('DELETE FROM imoveis WHERE cod_imovel = %s', (cod_imovel,))
                conn.commit()  # Confirma a exclusão do imóvel

                QMessageBox.information(self, "Sucesso", f"Imóvel '{nome_imovel}' excluído com sucesso!")
            except mysql.connector.Error as e:
                QMessageBox.warning(self, "Erro", f"Erro ao excluir imóvel: {e}")
            except ValueError as ve:
                QMessageBox.warning(self, "Erro", str(ve))
            finally:
                cursor.close()
                conn.close()

            # Remover o imóvel da lista de imóveis do programa
            if nome_imovel in self.imoveis:
                del self.imoveis[nome_imovel]

            # Remover o item do navbar
            for index in range(self.navbar.count()):
                item = self.navbar.item(index)
                if item is not None and item.text() == nome_imovel:
                    self.navbar.takeItem(index)
                    break

            self.carregar_imoveis()

            
   
    # Criação do layout vertical para organizar os campos verticalmente
    def setup_adicionar_proprietario_widget(self):
    # Configuração inicial do layout principal
        layout = QVBoxLayout()
        self.adicionar_proprietario_widget = QWidget()  # Verifique a inicialização adequada

        # Configuração de um layout de formulário
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)  
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setAlignment(Qt.AlignTop)

        # Entrada para o Nome
        self.nome_input = QLineEdit()
        self.nome_input.setFixedHeight(40)
        self.nome_input.setFixedWidth(350)
        self.nome_input.setPlaceholderText("Nome do proprietário")
        form_layout.addRow("Nome:", self.nome_input)

        # Entrada para o CPF
        self.cpf_input = QLineEdit()
        self.cpf_input.setFixedHeight(40)
        self.cpf_input.setFixedWidth(350)
        self.cpf_input.setPlaceholderText("CPF (somente números)")
        form_layout.addRow("CPF:", self.cpf_input)

        # Entrada para o Email
        self.email_input = QLineEdit()
        self.email_input.setFixedHeight(40)
        self.email_input.setFixedWidth(350)
        self.email_input.setPlaceholderText("Email do proprietário")
        form_layout.addRow("Email:", self.email_input)

        # Entrada para o Telefone
        self.telefone_input = QLineEdit()
        self.telefone_input.setFixedHeight(40)
        self.telefone_input.setFixedWidth(350)
        self.telefone_input.setPlaceholderText("Telefone de contato")
        form_layout.addRow("Telefone:", self.telefone_input)

        # Botão de Salvar
        salvar_btn = QPushButton("Salvar Proprietário")
        salvar_btn.setFixedHeight(40)
        salvar_btn.clicked.connect(self.salvar_proprietario)
        layout.addLayout(form_layout)
        layout.addWidget(salvar_btn, 0, Qt.AlignCenter)  # Adicionar o botão centralizado no layout

        self.adicionar_proprietario_widget.setLayout(layout)
        
       
        
                
    def salvar_proprietario(self):
        nome = self.nome_input.text()
        cpf = self.cpf_input.text()
        email = self.email_input.text()
        telefone = self.telefone_input.text()

        if not (nome and cpf and email and telefone):
            QMessageBox.warning(self, "Erro", "Todos os campos são obrigatórios.")
            return

        conn = conectar_mysql()
        if conn:
            try:
                cursor = conn.cursor()
                query = "INSERT INTO proprietarios (nome, cpf, email, telefone) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (nome, cpf, email, telefone))
                conn.commit()
                QMessageBox.information(self, "Sucesso", "Proprietário adicionado com sucesso!")
                self.nome_input.clear()
                self.cpf_input.clear()
                self.email_input.clear()
                self.telefone_input.clear()
                
            except mysql.connector.Error as e:
                QMessageBox.warning(self, "Erro", f"Erro ao adicionar proprietário: {e}")
            finally:
                cursor.close()
                conn.close()
                
    def salvar_imovel(self):
        cod_imovel = self.cod_imovel_input.text()
        nome = self.nome_imovel_input.text()
        endereco = self.endereco_imovel_input.text()
        cpf_proprietario = self.proprietario_combo.currentData()

        if cod_imovel and nome and endereco and cpf_proprietario:
            conn = conectar_mysql()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT * FROM imoveis WHERE cod_imovel = %s', (cod_imovel,))
                    resultado = cursor.fetchone()
                    if resultado:
                        QMessageBox.warning(self, "Imóvel já existe", "Já existe um imóvel com este código. Por favor, escolha um código diferente.")
                    else:
                        cursor.execute('SELECT * FROM imoveis WHERE nome = %s AND endereco = %s', (nome, endereco))
                        resultado = cursor.fetchone()
                        if resultado:
                            QMessageBox.warning(self, "Imóvel já existe", "Já existe um imóvel com este nome e endereço. Por favor, escolha um nome ou endereço diferente.")
                        else:
                            cursor.execute('INSERT INTO imoveis (cod_imovel, nome, endereco) VALUES (%s, %s, %s)', (cod_imovel, nome, endereco))
                            cursor.execute('INSERT INTO imovel_proprietario (cod_imovel, cpf_proprietario) VALUES (%s, %s)', (cod_imovel, cpf_proprietario))
                            conn.commit()
                            QMessageBox.information(self, "Sucesso", "Imóvel adicionado com sucesso!")
                            
                            # Limpar os campos de entrada após salvar
                            self.cod_imovel_input.clear()
                            self.nome_imovel_input.clear()
                            self.endereco_imovel_input.clear()
                            self.proprietario_combo.setCurrentIndex(0)
                            self.botao_voltar.hide()

                            # Mudar a tela atual para a tela de opções do imóvel
                            self.stack.setCurrentWidget(self.tela_opcoes_imovel)
                except mysql.connector.Error as e:
                    QMessageBox.warning(self, "Erro", f"Erro ao adicionar imóvel: {e}")
                finally:
                    cursor.close()
                    conn.close()
                    self.carregar_imoveis()  # Recarregar a lista de imóveis
        else:
            QMessageBox.warning(self, "Erro", "Por favor, preencha todos os campos.")

                
    def carregar_imoveis(self):
        

        conn = conectar_mysql()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM imoveis')
            for row in cursor.fetchall():
                nome_imovel = row[0]
                if nome_imovel not in self.imoveis:  # Verifica se já está na lista
                    self.imoveis[nome_imovel] = Imovel(nome_imovel)  # Adiciona ao dicionário
            conn.close()
    def abrir_gerenciar_contratos(self):
        if self.cod_imovel_selecionado:
            self.setup_gerenciar_contratos_widget(self.cod_imovel_selecionado)
        else:
            QMessageBox.warning(self, "Seleção necessária", "Por favor, selecione um imóvel antes de gerenciar contratos.")   
              
   
    def setup_gerenciar_contratos_widget(self, cod_imovel_selecionado):
        if not hasattr(self, 'gerenciar_contratos_widget'):
            self.gerenciar_contratos_widget = QWidget()
            self.gerenciar_contratos_layout = QVBoxLayout(self.gerenciar_contratos_widget)
            self.stack.addWidget(self.gerenciar_contratos_widget)

        # Limpar o layout atual para evitar sobreposição de informações
        self.clear_layout(self.gerenciar_contratos_layout)

        conn = conectar_mysql()
        contrato = None
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT * FROM contratos WHERE cod_imovel = %s
                ''', (cod_imovel_selecionado,))
                contrato = cursor.fetchone()  # Lê o primeiro resultado
            finally:
                cursor.close()
                conn.close()

        if contrato:
            # Se contrato existir, mostrar os detalhes e gerar PDF
            self.gerar_pdf_contrato(contrato)
            QMessageBox.information(self, "Contrato Existente", f"O imóvel já possui um contrato. PDF gerado.")
            # Mudar a tela atual para a tela de opções do imóvel
            self.stack.setCurrentWidget(self.tela_opcoes_imovel)
            
        else:
            # Se não, mostrar o formulário para adicionar novo contrato
            self.add_contract_form(self.gerenciar_contratos_layout)

        self.stack.setCurrentWidget(self.gerenciar_contratos_widget)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def add_contract_form(self, layout):
        form_layout = QFormLayout()

        # Layout para o nome do imóvel (apenas para exibição, não edição)
        imovel_label = QLabel("Imóvel:")
        self.imovel_nome_label = QLabel()
        if self.imovel_selecionado:
            self.imovel_nome_label.setText(self.imovel_selecionado.nome)
        form_layout.addRow(imovel_label, self.imovel_nome_label)

        # Layout para o tipo de contrato
        tipo_contrato_label = QLabel("Tipo de Contrato:")
        self.tipo_contrato_combo = QComboBox()
        self.tipo_contrato_combo.addItems(['aluguel', 'venda'])
        self.tipo_contrato_combo.setFixedHeight(40)
        form_layout.addRow(tipo_contrato_label, self.tipo_contrato_combo)

        # Layout para a data de início
        data_inicio_label = QLabel("Data de Início:")
        self.data_inicio_input = QDateEdit()
        self.data_inicio_input.setCalendarPopup(True)
        self.data_inicio_input.setDate(QDate.currentDate())
        self.data_inicio_input.setFixedHeight(40)
        form_layout.addRow(data_inicio_label, self.data_inicio_input)

        # Layout para o valor do contrato
        valor_label = QLabel("Valor:")
        self.valor_input = QLineEdit()
        self.valor_input.setFixedHeight(40)
        form_layout.addRow(valor_label, self.valor_input)

        # Layout para o status do contrato
        status_label = QLabel("Status:")
        self.status_combo = QComboBox()
        self.status_combo.addItems(['ativo', 'concluído', 'cancelado'])
        self.status_combo.setFixedHeight(40)
        form_layout.addRow(status_label, self.status_combo)

        # Botão para salvar o contrato
        salvar_btn = QPushButton("Salvar Contrato")
        salvar_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;  /* Green background */
                color: white;  /* White text */
                border-radius: 5px;  /* Rounded corners */
                padding: 10px;  /* Padding */
            }
            QPushButton:hover {
                background-color: #45a049;  /* Darker green on hover */
            }
        """)
        salvar_btn.clicked.connect(self.salvar_contrato)
        salvar_btn.setFixedHeight(40)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(salvar_btn)
        button_layout.addStretch()

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        self.gerenciar_contratos_widget.setLayout(layout)
            
    def salvar_contrato(self):
        nome_imovel = self.imovel_nome_label.text()
        cod_imovel = self.obter_id_imovel(nome_imovel)  # Busca o ID do imóvel pelo nome

        # Busca o ID do proprietário associado ao imóvel
        cpf_proprietario = self.obter_cpf_proprietario_de_imovel(cod_imovel)

        tipo_contrato = self.tipo_contrato_combo.currentText()
        data_inicio = self.data_inicio_input.date().toString("yyyy-MM-dd")
        valor = self.valor_input.text()
        status = self.status_combo.currentText()

        conn = conectar_mysql()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO contratos (cod_imovel, cpf_proprietario, tipo_contrato, data_inicio, data_fim, valor, status)
                    VALUES (%s, %s, %s, %s, NULL, %s, %s)
                ''', (cod_imovel, cpf_proprietario, tipo_contrato, data_inicio, valor, status))
                conn.commit()
                QMessageBox.information(self, "Sucesso", "Contrato adicionado com sucesso!")
                
                # Limpar os campos de entrada após salvar
                self.tipo_contrato_combo.setCurrentIndex(0)
                self.data_inicio_input.setDate(QDate.currentDate())
                self.valor_input.clear()
                self.status_combo.setCurrentIndex(0)
             

                # Mudar a tela atual para a tela de opções do imóvel
                self.stack.setCurrentWidget(self.tela_opcoes_imovel)
            except mysql.connector.Error as e:
                QMessageBox.warning(self, "Erro", f"Erro ao adicionar contrato: {e}")
            finally:
                cursor.close()
                conn.close()

    def gerar_pdf_contrato(self, contrato):
        user_directory = os.path.expanduser("~")
        nome_arquivo = f"contrato_imovel_{self.imovel_selecionado.nome}.pdf"
        caminho_arquivo = os.path.join(user_directory, nome_arquivo)

        doc = SimpleDocTemplate(caminho_arquivo, pagesize=letter)
        styles = getSampleStyleSheet()
        flowables = []

        # Título
        title = "CONTRATO DE IMÓVEL"
        flowables.append(Paragraph(title, styles['Title']))
        flowables.append(Spacer(1, 12))

        # Subtítulo
        subtitle = f"Contrato do Imóvel: {self.imovel_selecionado.nome}"
        flowables.append(Paragraph(subtitle, styles['Heading2']))
        flowables.append(Spacer(1, 12))

        # Dados do contrato
        data = [
            ["ID do Imóvel", contrato[1]],
            ["ID do Proprietário", contrato[2]],
            ["Tipo de Contrato", contrato[3]],
            ["Data de Início", contrato[4]],
            ["Data de Fim", contrato[5] if contrato[5] else 'Indefinido'],
            ["Valor", contrato[6]],
            ["Status", contrato[7]]
        ]

        table = Table(data, colWidths=[150, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 12)
        ]))

        flowables.append(table)
        flowables.append(Spacer(1, 24))

        # Texto do contrato
        contrato_texto = """
        Pelo presente instrumento particular, as partes acima identificadas têm entre si justo e acordado o presente Contrato de Imóvel, que se regerá pelas cláusulas e condições seguintes, que mutuamente outorgam e aceitam.

        As partes declaram, para todos os fins de direito, que o imóvel objeto deste contrato encontra-se em perfeito estado de uso e conservação.

        O presente contrato tem início em {data_inicio} e, se aplicável, término em {data_fim}. O valor acordado é de {valor}, com status atual de {status}.
        """.format(data_inicio=contrato[4], data_fim=contrato[5] if contrato[5] else 'Indefinido', valor=contrato[6], status=contrato[7])

        flowables.append(Paragraph(contrato_texto, styles['BodyText']))
        flowables.append(Spacer(1, 48))

        # Linha para assinatura
        assinatura = HRFlowable(width="80%", thickness=1.5, color=colors.black, spaceBefore=30, spaceAfter=30, hAlign='CENTER')
        flowables.append(assinatura)
        flowables.append(Paragraph("Assinatura do Proprietário", styles['BodyText']))
        flowables.append(Spacer(1, 12))
        flowables.append(assinatura)
        flowables.append(Paragraph("Assinatura do Locatário/Vendedor", styles['BodyText']))

        doc.build(flowables)

        os.startfile(caminho_arquivo)
        QMessageBox.information(self, "PDF Gerado", f"O PDF do contrato foi gerado com o nome '{nome_arquivo}' no diretório '{user_directory}'.")

    def obter_cpf_proprietario_de_imovel(self, cod_imovel):
        conn = conectar_mysql()
        cpf_proprietario = None
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT cpf_proprietario FROM imovel_proprietario WHERE cod_imovel = %s
                ''', (cod_imovel,))
                result = cursor.fetchone()
                if result:
                    cpf_proprietario = result[0]
            finally:
                cursor.close()
                conn.close()
        return cpf_proprietario

    def mostrar_calendario(self, event):
        if not hasattr(self, 'calendario'):
            self.calendario = QCalendarWidget(self)
            self.calendario.setWindowModality(Qt.ApplicationModal)
            self.calendario.clicked.connect(self.selecionar_data)
            self.calendario.setWindowTitle('Escolher Data')
            self.calendario.setGeometry(500, 400, 300, 200)

        if self.calendario.isVisible():
            self.calendario.hide()
        else:
            self.calendario.show()
        
    def mostrar_meus_imoveis(self):
        nomes_imoveis = set(self.imoveis.keys())  # Conjunto com os nomes dos imóveis

        if self.mostrando_imoveis:
            # Remove os itens de imóveis da navbar
            for index in reversed(range(self.navbar.count())):
                item = self.navbar.item(index)
                if item and item.text() in nomes_imoveis:
                    self.navbar.takeItem(index)
            self.mostrando_imoveis = False
        else:
            # Adiciona os itens de imóveis na navbar
            for nome_imovel in self.imoveis:
                if nome_imovel not in [self.navbar.item(i).text() for i in range(self.navbar.count())]:
                    item = QListWidgetItem(nome_imovel, self.navbar)
                    item.setForeground(QColor("#333"))  # Definir a cor do texto
                    item.setFont(QFont("HP Simplified", 13))  # Definir a fonte e tamanho
            self.mostrando_imoveis = True

    def selecionar_data(self, date):
        selected_date = date.toString("yyyy-MM-dd")
        self.data_input.setText(selected_date)
        self.calendario.close()
        self.calendario.hide()
        
    def obter_id_imovel(self, nome_imovel):
        conn = conectar_mysql()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT cod_imovel FROM imoveis WHERE nome = %s', (nome_imovel,))
                result = cursor.fetchone()
                if result:
                    return result[0]  # Retorna o ID encontrado
                else:
                    return None  # Se não encontrar, retorna None
            finally:
                conn.close()

    def imovel_selecionado(self, current, previous):
        if current and current.text() in self.imoveis:
            nome_imovel = current.text()
            self.imovel_selecionado = self.imoveis[nome_imovel]
            self.cod_imovel_selecionado = self.obter_id_imovel(nome_imovel)  # Armazena o ID do imóvel

            self.botao_voltar.hide()
            self.atualizar_tabela_gastos(self.imovel_selecionado.nome)
            self.header.setText(f"{nome_imovel}")
            self.stack.setCurrentWidget(self.tela_opcoes_imovel)
            self.btn_adicionar_gasto.show()
            self.btn_ver_gastos.show()
            self.btn_gerenciar_contratos.show()  # Mostre o botão de gerenciar contratos
        else:
            self.imovel_selecionado = None
            self.cod_imovel_selecionado = None
            self.stack.setCurrentWidget(self.tela_inicial)
            self.btn_adicionar_gasto.hide()
            self.btn_ver_gastos.hide()
            self.btn_gerenciar_contratos.hide()  # Esconda o botão
            self.header.setText("GESTAO DE IMOVEIS PARA BANCO DE DADOS")


    def mostrar_adicionar_gasto(self):
        if self.imovel_selecionado:
            # Atualizar o texto do cabeçalho para o nome do imóvel
            self.header.setText(f"Adicionar despesa em {self.imovel_selecionado.nome}")
            self.stack.setCurrentWidget(self.adicionar_gasto_widget)
            self.botao_voltar.show()
            self.data_input.show() # Mostrar campo de entrada de data
        else:
            self.exibir_mensagem("Por favor, selecione um imóvel primeiro.")


    def mostrar_ver_gastos(self):
        if self.imovel_selecionado:
            # Atualizar o texto do cabeçalho para o nome do imóvel
            self.header.setText(f"Gastos do Imóvel {self.imovel_selecionado.nome}")
            self.atualizar_tabela_gastos(self.imovel_selecionado.nome)
            self.stack.setCurrentWidget(self.mostrar_gastos_widget)
            self.botao_voltar.show()
        else:
            print("Por favor, selecione um imóvel primeiro.")

    def mostrar_adicionar_imovel(self):
        # Método para mudar o widget exibido no QStackedWidget para o de adicionar imóvel
        self.stack.setCurrentWidget(self.adicionar_imovel_widget)

    def criar_botao_voltar(self):
        botao_voltar = QPushButton('Voltar', self)
        
        botao_voltar.clicked.connect(self.voltar_para_selecao_imovel)
        return botao_voltar

    def voltar_para_selecao_imovel(self):
        # Restaurar o texto original do cabeçalho
        self.header.setText("CONTROLE DE GASTOS")
        if self.tabela_gastos.currentRow() >= 0:
     

            self.atualizar_tabela_gastos(self.imovel_selecionado.nome)

        self.stack.setCurrentWidget(self.tela_opcoes_imovel)
        self.navbar.setCurrentItem(self.navbar_header)  # Selecionar o cabeçalho da lista
    
        
        self.botao_voltar.hide()  # Ocultar o botão "Voltar" ao retornar

    def confirmar_gasto(self):
        nome_imovel = self.navbar.currentItem().text()
        if nome_imovel in self.imoveis:
            item = self.item_input.text()
            forma_pagamento = self.forma_pagamento_input.text()
            valor_texto = self.valor_input.text().replace(',', '.')
            data = self.data_input.text()

            # Verificar se todos os campos foram preenchidos
            if not item or not forma_pagamento or not valor_texto or not data:
                QMessageBox.warning(self, 'Atenção', 'Por favor, preencha todos os campos.')
                return

            try:
                valor_float = float(valor_texto)
                self.imoveis[nome_imovel].adicionar_gasto(item, forma_pagamento, valor_float, data)
                self.item_input.clear()
                self.forma_pagamento_input.clear()
                self.valor_input.clear()
                self.data_input.clear()
                self.atualizar_tabela_gastos(nome_imovel)

                # Exibir modal de confirmação
                QMessageBox.information(self, 'Sucesso', 'Despesa registrada com sucesso.')
                self.botao_voltar.hide()

                # Mudar a tela atual para a tela de opções do imóvel
                self.stack.setCurrentWidget(self.tela_opcoes_imovel)

            except ValueError:
                QMessageBox.warning(self, 'Erro', 'Por favor, insira um valor numérico válido.')
        else:
            QMessageBox.warning(self, 'Atenção', 'Por favor, selecione um imóvel primeiro.')

    def atualizar_tabela_gastos(self, nome_imovel):
            # Obter o ID do imóvel selecionado
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Use 'pt_BR.UTF-8' for Portuguese (Brazil) formatting
            
            cod_imovel = self.imoveis[nome_imovel].obter_id_imovel(nome_imovel)

            # Conectar ao banco de dados e buscar os gastos para esse imóvel
            conn = conectar_mysql()
            if conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, DATE_FORMAT(data, "%d/%m/%Y") , forma_pg, valor,item FROM itens WHERE cod_imovel = %s ORDER BY data DESC', (cod_imovel,))
                self.tabela_gastos.setRowCount(0)
                total = 0

                # Definir fonte para os itens da tabela
                fonte_item = QFont("Arial", 12)  # Altere "Arial" e "12" conforme necessário

            for id_item, item, forma_pagamento, valor, data in cursor.fetchall():
                row_position = self.tabela_gastos.rowCount()
                self.tabela_gastos.insertRow(row_position)

                # Criação dos itens da tabela com a fonte definida
                item_widget = QTableWidgetItem(item)
                item_widget.setFont(fonte_item)
                item_widget.setData(Qt.UserRole, id_item)
           

                forma_pagamento_widget = QTableWidgetItem(forma_pagamento)
                forma_pagamento_widget.setFont(fonte_item)
                
                
                valor_formatted = locale.format_string('R$ %.2f', valor, grouping=True)  # Format the value according to the locale
                valor_widget = QTableWidgetItem(valor_formatted)
                valor_widget.setFont(fonte_item)
            

                data_widget = QTableWidgetItem(str(data))
                data_widget.setFont(fonte_item)
           

                # Adicionar os itens à linha correspondente com a nova ordem
                self.tabela_gastos.setItem(row_position, 1, data_widget)
                self.tabela_gastos.setItem(row_position, 0, item_widget)
                self.tabela_gastos.setItem(row_position, 2, forma_pagamento_widget)
                self.tabela_gastos.setItem(row_position, 3, valor_widget)
                
                

                total += valor

                formatted_total = locale.format_string('%.2f', total, grouping=True)  # Format the total according to the locale
                self.total_label.setText(f"Total: R${formatted_total}")
            
            conn.close()
    
    def gerar_pdf(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF Files (*.pdf)")
        if not filepath:  # Se nenhum local foi escolhido (operação cancelada)
            return  # Não faça nada

        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter

        # Adicionar título
        c.setFont("Helvetica-Bold", 14)
        c.drawString(190, height - 100, f"Gastos do Imóvel {self.imovel_selecionado.nome}")

        # Posição inicial para a tabela abaixo do título
        x_pos = 50  # Comece um pouco mais à esquerda para caber tudo
        y_pos = height - 150  # Deixe espaço suficiente para o título e cabeçalho

        # Adicionar cabeçalhos da tabela
        headers = ["Data", "Item", "Forma de Pagamento", "Valor"]
        col_width = [100, 150, 150, 100]  # Largura das colunas ajustável

        # Linha superior do cabeçalho
        c.line(x_pos, y_pos + 15, x_pos + sum(col_width), y_pos + 15)

        for i, header in enumerate(headers):
            c.drawString(x_pos + sum(col_width[:i]), y_pos, header)

        # Linha inferior do cabeçalho
        c.line(x_pos, y_pos - 5, x_pos + sum(col_width), y_pos - 5)

        # Adicionar itens da tabela
        c.setFont("Helvetica", 10)
        y_pos_initial = y_pos - 5  # Posição inicial de y para a primeira linha de dados

        for row in range(self.tabela_gastos.rowCount()):
            y_pos -= 20
            # Linha superior de cada entrada de dados
            c.line(x_pos, y_pos + 15, x_pos + sum(col_width), y_pos + 15)
            for col in range(self.tabela_gastos.columnCount()):
                item = self.tabela_gastos.item(row, col)
                if item:  # Verificar se o item não é None
                    text = item.text()
                    c.drawString(x_pos + sum(col_width[:col]), y_pos, text)
            # Linha inferior de cada entrada de dados
            c.line(x_pos, y_pos - 5, x_pos + sum(col_width), y_pos - 5)

        # Linha final após a última entrada
        c.line(x_pos, y_pos - 5, x_pos + sum(col_width), y_pos - 5)

        # Salvar o PDF
        c.save()

        # Informar ao usuário que o PDF foi gerado com sucesso
        QMessageBox.information(self, "PDF Gerado", f"O PDF dos gastos foi gerado com sucesso em: {filepath}")

    def mostrar_adicionar_proprietario(self):
        self.stack.setCurrentWidget(self.adicionar_proprietario_widget)
        
    def on_table_item_selected(self):
    # Supondo que você tenha um método para ser chamado quando um item da tabela é selecionado
        selected_row = self.tabela_gastos.currentRow()  # Pegar a linha selecionada
        if selected_row is not None:
            # Supondo que o ID está armazenado na coluna de data após a reordenação
            id_item = self.tabela_gastos.item(selected_row, 0).data(Qt.UserRole)
            print("ID do item selecionado:", id_item)
            # Aqui você pode usar o id_item para operações como exclusão
                    
    def on_item_changed(self, item):
        # Obter o ID do item editado
        selected_row = self.tabela_gastos.currentRow()  # Pegar a linha selecionada
        if selected_row is not None:
            item_id = self.tabela_gastos.item(selected_row, 0)
            if item_id is not None:  # Verifica se o item existe
                id = item_id.data(Qt.UserRole)
            else:
                return  # Saia do método se o item for None

        # Determinar qual coluna foi editada
        column = item.column()
        newValue = item.text()

        # Verificação para coluna de valor
        if column == 3:  # Coluna 'Valor'
            newValue = newValue.replace('R$', '').replace(',', '.').strip()
            # Tentar converter para float para verificar se é um valor numérico válido
            try:
                float(newValue)  # Tenta converter o newValue para float
            except ValueError:
                QMessageBox.warning(self, "Valor inválido", "Por favor, insira um valor numérico válido.")
                self.atualizar_tabela_gastos(self.imovel_selecionado.nome)  # Atualize a tabela para reverter a edição
                return  # Interromper a execução se o valor não for numérico

        # Construção das queries conforme a coluna editada
        if column == 0:  # 'Data'
            query = "UPDATE itens SET data = STR_TO_DATE(%s, '%d/%m/%Y') WHERE id = %s"
        elif column == 1:  # 'Item'
            query = "UPDATE itens SET item = %s WHERE id = %s"
        elif column == 2:  # 'Forma de pagamento'
            query = "UPDATE itens SET forma_pg = %s WHERE id = %s"
        elif column == 3:  # 'Valor'
            query = "UPDATE itens SET valor = %s WHERE id = %s"
            newValue = newValue  # Já convertido e validado anteriormente

        # Conectar ao banco de dados e executar a atualização
        conn = conectar_mysql()
        if conn:
            cursor = conn.cursor()
            cursor.execute(query, (newValue, id))
            conn.commit()
            conn.close()

            if column == 3 or column == 0:  # Se o valor ou a data foram alterados
                self.atualizar_tabela_gastos(self.imovel_selecionado.nome)  # Atualize a tabela para refletir as mudanças
        
def main():
    conn = conectar_mysql()
    if conn:
        criar_tabelas_mysql(conn)
        conn.close()
    app = QApplication(sys.argv)
    ex = MainApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
