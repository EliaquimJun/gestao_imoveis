import sys
import locale
from PyQt5.QtWidgets import QFileDialog
import mysql.connector
from PyQt5 import QtCore, QtGui, QtWidgets
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
                             QLabel, QInputDialog, QListWidget, QHBoxLayout, QStackedWidget,
                             QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QCalendarWidget, QDialog, QDialogButtonBox,QGridLayout)

from PyQt5.QtGui import QBrush, QColor,QLinearGradient,QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QToolBar, QAction, QMenu, QMenuBar, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QCalendarWidget, QMessageBox, QGridLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QComboBox
import resources


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
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL
        )
    ''')

    # Tabela de itens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item VARCHAR(255) NOT NULL,
            quantidade VARCHAR(255) NOT NULL,
            forma_pg VARCHAR(255) NOT NULL,
            valor DECIMAL(10, 2) NOT NULL,
            data DATE NOT NULL,  # Altere o tipo de dado para DATE
            id_imovel INT,
            FOREIGN KEY (id_imovel) REFERENCES imoveis (id)
        )
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
                    INSERT INTO itens (item, forma_pg, valor, data, id_imovel)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (item, forma_pagamento, valor, data, id_imovel))
                conn.commit()
                conn.close()

    def obter_id_imovel(self, nome_imovel):
        conn = conectar_mysql()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM imoveis WHERE nome = %s', (nome_imovel,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return result[0]  # Retorna o ID encontrado
        return None  # Retorna None se o imóvel não for encontrado

    def total_gastos(self):
        return sum(valor for item, valor, data in self.gastos)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.imoveis = {}
        self.initUI()
        self.imovel_selecionado = None 
        self.mostrando_imoveis = False
        self.itens_imoveis = []
        self.carregar_imoveis()
        self.btn_adicionar_gasto.hide()
        self.btn_ver_gastos.hide()
        
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
        self.action_cadastrar.triggered.connect(self.adicionar_imovel)
        
        
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

        
        self.navbar.setMaximumWidth(230)
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
        self.adicionar_imovel_btn.clicked.connect(self.adicionar_imovel)
        self.navbar.setItemWidget(self.adicionar_imovel_item, self.adicionar_imovel_btn)
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
        
        
        self.tela_opcoes_imovel = QWidget()
        self.opcoes_imovel_layout = QVBoxLayout(self.tela_opcoes_imovel)
        self.opcoes_imovel_layout.setContentsMargins(200, 0, 400, 600)  # Ajustar margens conforme necessário
      
        self.stack.addWidget(self.tela_opcoes_imovel)

        # Criar um layout horizontal para os botões
        self.botoes_layout = QHBoxLayout()

        self.btn_adicionar_gasto = QPushButton('Adicionar Gasto', self.tela_opcoes_imovel)
        self.btn_adicionar_gasto.setFixedWidth(280)
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
"font: 300 14pt \"Segoe UI Variable Small\";\n"
"")
        self.btn_adicionar_gasto.clicked.connect(self.mostrar_adicionar_gasto)
        
        
        self.btn_ver_gastos = QPushButton('Ver Gastos', self.tela_opcoes_imovel)
        self.btn_ver_gastos.setFixedWidth(280)
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
"font: 300 14pt \"Segoe UI Variable Small\";\n"
"")
        self.btn_ver_gastos.clicked.connect(self.mostrar_ver_gastos)
        
        
        
        # Adicionar botões ao layout horizontal
        self.botoes_layout.addWidget(self.btn_adicionar_gasto)
        self.botoes_layout.addWidget(self.btn_ver_gastos)

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
            # Primeiro, obtenha o ID do imóvel
            cursor.execute('SELECT id FROM imoveis WHERE nome = %s', (nome_imovel,))
            id_imovel = cursor.fetchone()[0]

            # Em seguida, exclua todos os itens de gasto associados a esse imóvel
            cursor.execute('DELETE FROM itens WHERE id_imovel = %s', (id_imovel,))

            # Finalmente, exclua o imóvel
            cursor.execute('DELETE FROM imoveis WHERE nome = %s', (nome_imovel,))
            conn.commit()
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

            
     
            
            
    def adicionar_imovel(self):
        nome, ok = QInputDialog.getText(self, 'Adicionar Imóvel', 'Nome do Imóvel:')
        if ok and nome:
            # Conectar ao banco de dados para verificar se o imóvel já existe
            conn = conectar_mysql()
            if conn:
                cursor = conn.cursor()
                # Verificar se já existe um imóvel com o mesmo nome
                cursor.execute('SELECT * FROM imoveis WHERE nome = %s', (nome,))
                resultado = cursor.fetchone()
                if resultado:
                    QMessageBox.warning(self, "Imóvel já existe", "Já existe um imóvel com esse nome. Por favor, escolha um nome diferente.")
                    conn.close()
                else:
                    # Se não existe, inserir o novo imóvel no banco de dados
                    cursor.execute('INSERT INTO imoveis (nome) VALUES (%s)', (nome,))
                    conn.commit()
                    conn.close()
                    
                    # Adicionar imóvel à lista de imóveis e na interface
                    novo_imovel = Imovel(nome)
                    self.imoveis[nome] = novo_imovel
                    self.navbar.addItem(nome)

                
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
        

    def imovel_selecionado(self, current, previous):
        if current and current.text() in self.imoveis:
            nome_imovel = current.text()
            self.imovel_selecionado = self.imoveis[nome_imovel]
            self.botao_voltar.hide()
            self.atualizar_tabela_gastos(self.imovel_selecionado.nome)

            # Atualizar o texto do cabeçalho para o nome do imóvel
            self.header.setText(f"{nome_imovel}")
            self.stack.setCurrentWidget(self.tela_opcoes_imovel)
            self.btn_adicionar_gasto.show()
            self.btn_ver_gastos.show()
        else:
            self.imovel_selecionado = None
            self.stack.setCurrentWidget(self.tela_inicial)
     
            self.btn_adicionar_gasto.hide()
            self.btn_ver_gastos.hide()
            # Restaurar o texto original do cabeçalho
            self.header.setText("CONTROLE DE GASTOS HERMANN")

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
            
            id_imovel = self.imoveis[nome_imovel].obter_id_imovel(nome_imovel)

            # Conectar ao banco de dados e buscar os gastos para esse imóvel
            conn = conectar_mysql()
            if conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, DATE_FORMAT(data, "%d/%m/%Y") , forma_pg, valor,item FROM itens WHERE id_imovel = %s ORDER BY data DESC', (id_imovel,))
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
