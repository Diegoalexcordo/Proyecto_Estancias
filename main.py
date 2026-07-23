# -*- coding: utf-8 -*-
import os
import shutil
import zipfile
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QLabel, QVBoxLayout, QDialog, QWidget, QScrollArea, QHBoxLayout, QPushButton
)
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem, QAction, QDesktopServices, QIcon
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QLineEdit


from ventana import Ui_Dialog as Ui_VentanaPrincipal
from consulta import Ui_Dialog as Ui_VentanaConsulta
from DocumentosCliente import Ui_Dialog as Ui_DocumentosCliente
import database
from database import get_db_path

def cargar_estilos(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def apply_neon_glow(widget, color=QColor(0, 255, 255), radius=20):
    glow = QGraphicsDropShadowEffect(widget)
    glow.setBlurRadius(radius)
    glow.setColor(color)
    glow.setOffset(0, 0)
    widget.setGraphicsEffect(glow)

def get_archivos_path():
    return os.path.join(os.getenv("LOCALAPPDATA"), "RegistroDolores", "archivos")

class DocumentosClienteDialog(QDialog):
    def __init__(self, cliente_id, cliente_nombre):
        super().__init__()
        self.setWindowTitle(f"Documentos de {cliente_nombre}")
        self.cliente_id = cliente_id
        self.todos_los_archivos = []  # lista completa sin filtrar

        # Widgets de interfaz
        self.buscador = QLineEdit(self)
        self.buscador.setPlaceholderText("Buscar archivo por nombre...")
        self.buscador.textChanged.connect(self.filtrar_archivos)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.contenedor = QWidget()
        self.vbox = QVBoxLayout(self.contenedor)
        self.scroll.setWidget(self.contenedor)

        layout_principal = QVBoxLayout(self)
        layout_principal.addWidget(self.buscador)
        layout_principal.addWidget(self.scroll)

        self.cargar_documentos()

    def cargar_documentos(self):
        self.todos_los_archivos.clear()
        ruta_carpeta = os.path.join(get_archivos_path(), f"cliente_{self.cliente_id}")
        if not os.path.exists(ruta_carpeta):
            return

        archivos = os.listdir(ruta_carpeta)
        for archivo in archivos:
            ruta = os.path.join(ruta_carpeta, archivo)
            self.todos_los_archivos.append((archivo, ruta))

        self.mostrar_archivos(self.todos_los_archivos)

    def mostrar_archivos(self, lista_archivos):
        # Limpia vista actual
        while self.vbox.count():
            item = self.vbox.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for archivo, ruta in lista_archivos:
            widget = QWidget()
            hbox = QHBoxLayout(widget)
            hbox.setContentsMargins(10, 10, 10, 10)
            hbox.setSpacing(10)

            if ruta.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                pixmap = QPixmap(ruta).scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
                label_imagen = QLabel()
                label_imagen.setPixmap(pixmap)
                label_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label_imagen.setFixedWidth(220)
                label_imagen.mousePressEvent = lambda e, r=ruta: self.abrir_documento(r)
                hbox.addWidget(label_imagen)
            else:
                label_icon = QLabel("PDF")
                label_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label_icon.setFixedSize(200, 150)
                label_icon.setStyleSheet("background-color: #ccc; font-size: 40px; border: 1px solid #888;")
                label_icon.mousePressEvent = lambda e, r=ruta: self.abrir_documento(r)
                hbox.addWidget(label_icon)

            vbox_der = QVBoxLayout()
            label_nombre = QLabel(archivo)
            label_nombre.setStyleSheet("font-weight: bold; font-size: 14px;")
            vbox_der.addWidget(label_nombre)

            fecha = os.path.getmtime(ruta)
            fecha_str = datetime.fromtimestamp(fecha).strftime("%Y-%m-%d %H:%M:%S")
            label_fecha = QLabel(f"Fecha modificación: " + fecha_str)
            label_fecha.setStyleSheet("color: gray; font-size: 12px;")
            vbox_der.addWidget(label_fecha)

            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.setStyleSheet("background-color: #d9534f; color: white; padding: 6px;")
            btn_eliminar.clicked.connect(lambda checked, r=ruta, a=archivo: self.eliminar_archivo(r, a))
            vbox_der.addWidget(btn_eliminar)
            vbox_der.addStretch()
            hbox.addLayout(vbox_der)
            self.vbox.addWidget(widget)

        self.vbox.addStretch()

    def filtrar_archivos(self, texto):
        texto = texto.strip().lower()
        filtrados = [item for item in self.todos_los_archivos if texto in item[0].lower()]
        self.mostrar_archivos(filtrados)

    def abrir_documento(self, ruta):
        if ruta.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            dlg = QDialog(self)
            dlg.setWindowTitle(os.path.basename(ruta))
            layout = QVBoxLayout(dlg)
            label_img = QLabel()
            pixmap = QPixmap(ruta).scaled(800, 1000, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label_img.setPixmap(pixmap)
            layout.addWidget(label_img)
            dlg.exec()
        else:
            url = QUrl.fromLocalFile(ruta)
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(self, "Error", "No se pudo abrir el archivo.")

    def eliminar_archivo(self, ruta, nombre_archivo):
        reply = QMessageBox.question(self, "Eliminar archivo",
            f"¿Seguro que deseas eliminar el archivo '{nombre_archivo}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(ruta)
                database.borrar_archivo_por_ruta(ruta)
                QMessageBox.information(self, "Eliminado", "Archivo eliminado correctamente.")
                self.cargar_documentos()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo eliminar el archivo.\n{e}")

class VentanaConsulta(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_VentanaConsulta()
        self.ui.setupUi(self)
        self.setWindowTitle("Consulta de Clientes")

        self.ui.Tipo_de_trabajo_2.addItems(["Todos", "Valoración", "Servicio"])

        self.modelo = QStandardItemModel()
        self.modelo.setHorizontalHeaderLabels(["ID", "Nombre", "Apellido", "F. Insercion", "F. Documento", "Género", "Tipo trabajo", "Documento"])
        self.ui.tableView.setModel(self.modelo)

        self.ui.buscar_1.clicked.connect(self.buscar_clientes)
        self.ui.tableView.doubleClicked.connect(self.abrir_documentos_cliente)
        self.cargar_todos_clientes()

    def buscar_clientes(self):
        nombre = self.ui.textEdit_Nombre_1.toPlainText()
        apellido = self.ui.textEdit_Apellido.toPlainText()
        fecha_insercion = self.ui.Fecha_Actual.date().toString("yyyy-MM-dd")
        fecha_documento = self.ui.Fecha_document.date().toString("yyyy-MM-dd")
        tipo = self.ui.Tipo_de_trabajo_2.currentText()

        resultados = database.buscar_clientes(nombre, apellido, fecha_insercion, fecha_documento, tipo)
        self.modelo.removeRows(0, self.modelo.rowCount())
        ids_agregados = set()

        for cliente_id, nombre, apellido, f_ins, f_doc, genero, tipo_trabajo, _ in resultados:
            if cliente_id in ids_agregados:
                continue
            ids_agregados.add(cliente_id)
            self.modelo.appendRow([
                QStandardItem(str(cliente_id)),
                QStandardItem(nombre),
                QStandardItem(apellido),
                QStandardItem(f_ins),
                QStandardItem(f_doc),
                QStandardItem(genero),
                QStandardItem(tipo_trabajo),
                QStandardItem("Ver documentos")
            ])


    def cargar_todos_clientes(self):
        tipo = self.ui.Tipo_de_trabajo_2.currentText()
        resultados = database.obtener_clientes_con_archivos(tipo)
        self.modelo.removeRows(0, self.modelo.rowCount())
        ids_agregados = set()

        for cliente_id, nombre, apellido, f_ins, f_doc, genero, tipo_trabajo, _ in resultados:
            if cliente_id in ids_agregados:
                continue
            ids_agregados.add(cliente_id)
            self.modelo.appendRow([
                QStandardItem(str(cliente_id)),
                QStandardItem(nombre),
                QStandardItem(apellido),
                QStandardItem(f_ins),
                QStandardItem(f_doc),
                QStandardItem(genero),
                QStandardItem(tipo_trabajo),
                QStandardItem("Ver documentos")
            ])


    def abrir_documentos_cliente(self, index):
        fila = index.row()
        id_cliente = int(self.modelo.item(fila, 0).text())
        nombre_cliente = self.modelo.item(fila, 1).text()
        dlg = DocumentosClienteDialog(id_cliente, nombre_cliente)
        dlg.exec()
class MiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_VentanaPrincipal()
        self.ui.setupUi(self)
        self.setWindowTitle("Dolorfin")
        self.setWindowIcon(QIcon("img/logo.ico"))

        for btn in (
            self.ui.cargar_imagen_o_documentos,
            self.ui.nuevo, self.ui.guardar,
            self.ui.cancelar, self.ui.editar,
            self.ui.borrar,
            self.ui.btnImportar, self.ui.btnExportar
        ):
            apply_neon_glow(btn, QColor(0, 122, 255), radius=30)

        self.archivos_cargados = []
        self.id_cliente_editar = None

        self.ui.selecion_genero.addItems(["Masculino", "Femenino", "Otro"])
        self.ui.comboBox_tipo_trabajo.addItems(["Valoración", "Servicio"])

        self.modelo = QStandardItemModel()
        self.modelo.setHorizontalHeaderLabels(["ID", "Nombre", "Apellido", "F. Insercion", "F. Documento", "Género", "Tipo trabajo", "Documento"])
        self.ui.tableView.setModel(self.modelo)

        self.ui.nuevo.clicked.connect(self.boton_nuevo)
        self.ui.guardar.clicked.connect(self.boton_guardar)
        self.ui.cargar_imagen_o_documentos.clicked.connect(self.cargar_archivos)
        self.ui.cancelar.clicked.connect(self.boton_cancelar)
        self.ui.editar.clicked.connect(self.boton_editar)
        self.ui.borrar.clicked.connect(self.boton_borrar)
        self.ui.btnExportar.clicked.connect(self.exportar_datos)
        self.ui.btnImportar.clicked.connect(self.importar_datos)

        self.crear_menu()
        os.makedirs(get_archivos_path(), exist_ok=True)
        self.habilitar_campos(False)
        self.cargar_datos_existentes()

    def crear_menu(self):
        menubar = self.menuBar()
        menu_inicio = menubar.addMenu("Inicio")
        menu_consultas = menubar.addMenu("Consultas")

        crear_bd_action = QAction("Crear base de datos", self)
        crear_bd_action.triggered.connect(self.crear_base_datos)
        menu_inicio.addAction(crear_bd_action)

        abrir_consulta_action = QAction("Abrir ventana de consultas", self)
        abrir_consulta_action.triggered.connect(self.abrir_consulta)
        menu_consultas.addAction(abrir_consulta_action)

    def crear_base_datos(self):
        database.crear_base_datos()
        QMessageBox.information(self, "Base de datos", "Base de datos y tablas creadas correctamente.")

    def habilitar_campos(self, estado):
        self.ui.textEdit_Nombre.setEnabled(estado)
        self.ui.textEdit_Apellido.setEnabled(estado)
        self.ui.Fecha_Actual.setEnabled(estado)
        self.ui.Fecha_document.setEnabled(estado)
        self.ui.selecion_genero.setEnabled(estado)
        self.ui.comboBox_tipo_trabajo.setEnabled(estado)
        self.ui.cargar_imagen_o_documentos.setEnabled(estado)
        self.ui.guardar.setEnabled(estado)

    def cargar_archivos(self):
        archivos, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar archivos", "", "Archivos (*.png *.jpg *.jpeg *.bmp *.pdf)"
        )
        if archivos:
            self.archivos_cargados = archivos
            QMessageBox.information(self, "Cargado", f"{len(archivos)} archivo(s) cargado(s).")

    def boton_nuevo(self):
        self.archivos_cargados = []
        self.ui.textEdit_Nombre.clear()
        self.ui.textEdit_Apellido.clear()
        self.ui.Fecha_Actual.setDate(datetime.now().date())
        self.ui.Fecha_document.setDate(datetime.now().date())
        self.ui.comboBox_tipo_trabajo.setCurrentIndex(0)
        self.id_cliente_editar = None
        self.habilitar_campos(True)
        QMessageBox.information(self, "Nuevo", "Formulario listo para nuevo cliente.")
    def boton_guardar(self):
        nombre = self.ui.textEdit_Nombre.toPlainText()
        apellido = self.ui.textEdit_Apellido.toPlainText()
        genero = self.ui.selecion_genero.currentText()
        tipo_trabajo = self.ui.comboBox_tipo_trabajo.currentText()
        fecha_insercion = self.ui.Fecha_Actual.date().toString("yyyy-MM-dd")
        fecha_documento = self.ui.Fecha_document.date().toString("yyyy-MM-dd")

        if not nombre or not apellido:
            QMessageBox.warning(self, "Error", "Nombre y apellido no pueden estar vacíos.")
            return

        if self.id_cliente_editar:
            database.actualizar_cliente(self.id_cliente_editar, nombre, apellido, fecha_insercion, fecha_documento, genero, tipo_trabajo)
            cliente_id = self.id_cliente_editar
            QMessageBox.information(self, "Editado", "Cliente actualizado correctamente.")
        else:
            cliente_id = database.insertar_cliente(nombre, apellido, fecha_insercion, fecha_documento, genero, tipo_trabajo)
            QMessageBox.information(self, "Guardado", "Cliente guardado correctamente.")

        carpeta_cliente = os.path.join(get_archivos_path(), f"cliente_{cliente_id}")
        os.makedirs(carpeta_cliente, exist_ok=True)

        for archivo in self.archivos_cargados:
            destino = os.path.join(carpeta_cliente, os.path.basename(archivo))
            shutil.copy2(archivo, destino)
            database.insertar_archivo(cliente_id, destino)

        self.cargar_datos_existentes()
        self.archivos_cargados = []
        self.habilitar_campos(False)
        self.id_cliente_editar = None

    def boton_cancelar(self):
        self.ui.textEdit_Nombre.clear()
        self.ui.textEdit_Apellido.clear()
        self.archivos_cargados = []
        self.id_cliente_editar = None
        self.habilitar_campos(False)
        QMessageBox.information(self, "Cancelar", "Formulario cancelado.")

    def boton_editar(self):
        seleccion = self.ui.tableView.selectionModel().selectedRows()
        if not seleccion:
            QMessageBox.warning(self, "Editar", "Seleccione un cliente para editar.")
            return

        fila = seleccion[0].row()
        self.id_cliente_editar = int(self.modelo.item(fila, 0).text())
        self.ui.textEdit_Nombre.setText(self.modelo.item(fila, 1).text())
        self.ui.textEdit_Apellido.setText(self.modelo.item(fila, 2).text())
        self.ui.Fecha_Actual.setDate(datetime.strptime(self.modelo.item(fila, 3).text(), "%Y-%m-%d"))
        self.ui.Fecha_document.setDate(datetime.strptime(self.modelo.item(fila, 4).text(), "%Y-%m-%d"))
        self.ui.selecion_genero.setCurrentText(self.modelo.item(fila, 5).text())
        self.habilitar_campos(True)

    def boton_borrar(self):
        seleccion = self.ui.tableView.selectionModel().selectedRows()
        if not seleccion:
            QMessageBox.warning(self, "Borrar", "Seleccione un cliente para borrar.")
            return

        fila = seleccion[0].row()
        id_cliente = int(self.modelo.item(fila, 0).text())

        if QMessageBox.question(self, "Borrar", "¿Está seguro que desea borrar este cliente?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            database.borrar_cliente(id_cliente)
            shutil.rmtree(os.path.join(get_archivos_path(), f"cliente_{id_cliente}"), ignore_errors=True)
            self.cargar_datos_existentes()

    def abrir_consulta(self):
        VentanaConsulta().exec()

    def cargar_datos_existentes(self):
        resultados = database.obtener_clientes_con_archivos()
        self.modelo.removeRows(0, self.modelo.rowCount())
        ids_agregados = set()

        for cliente_id, nombre, apellido, f_ins, f_doc, genero, tipo_trabajo, _ in resultados:
            if cliente_id in ids_agregados:
                continue
            ids_agregados.add(cliente_id)
            self.modelo.appendRow([
                QStandardItem(str(cliente_id)),
                QStandardItem(nombre),
                QStandardItem(apellido),
                QStandardItem(f_ins),
                QStandardItem(f_doc),
                QStandardItem(genero),
                QStandardItem(tipo_trabajo),
                QStandardItem("Ver documentos")
            ])


    def exportar_datos(self):
        try:
            zip_path = os.path.join(os.path.expanduser("~"), "Downloads", "backup_dolorfin.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as backup:
                if os.path.exists(get_db_path()):
                    backup.write(get_db_path(), "base_datos.db")

                for carpeta_raiz, _, archivos in os.walk(get_archivos_path()):
                    for archivo in archivos:
                        ruta_completa = os.path.join(carpeta_raiz, archivo)
                        ruta_relativa = os.path.relpath(ruta_completa, get_archivos_path())
                        backup.write(ruta_completa, os.path.join("archivos", ruta_relativa))

            QMessageBox.information(self, "Exportación", f"Backup exportado a:\n{zip_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar el backup:\n{str(e)}")

    def importar_datos(self):
        try:
            zip_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo ZIP", "", "Archivo ZIP (*.zip)")
            if not zip_path:
                return
            with zipfile.ZipFile(zip_path, "r") as backup:
                backup.extractall(os.path.join(os.getenv("LOCALAPPDATA"), "RegistroDolores"))
            QMessageBox.information(self, "Importación", "Backup importado correctamente.")
            self.cargar_datos_existentes()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo importar el backup:\n{str(e)}")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    if not os.path.exists(get_db_path()):
        database.crear_base_datos()

    estilo = cargar_estilos("style.qss")
    app.setStyleSheet(estilo)
    ventana = MiApp()
    ventana.show()
    sys.exit(app.exec())
