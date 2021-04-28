from PyQt5 import QtWidgets, QtCore, QtGui
import design
import ctypes
from settings import EXCEL_ROW_OFFSET
#from field_detection import *
from new_table import convert_excel_to_list, row_to_dictionary
from new_field import *
from selenium.common.exceptions import NoSuchElementException
import options
import logging
from datetime import date
import os
from pathlib import Path
import win32clipboard
from urllib.parse import quote
import webbrowser

class Exceptional_message(QtWidgets.QMessageBox):
    def __init__(self, information):
        super().__init__()
        window_object = QtWidgets.QMessageBox
        window_object.setWindowTitle(self, 'Требуется вмешательство')
        window_object.setWindowFlags(self, QtCore.Qt.WindowStaysOnTopHint)
        window_object.addButton(self, QtWidgets.QPushButton('Продолжить'), 0)
        window_object.setText(self, information)
        self.data_address = information[information.find('Исходный указанный адрес:') + 25:]
        copy_ = QtWidgets.QPushButton('Скопировать адрес')
        window_object.addButton(self, copy_, 6)
        copy_.clicked.disconnect()
        copy_.clicked.connect(self.copy_to_clipboard)

    def copy_to_clipboard(self):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(self.data_address, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except:
            logging.warning(f"Couldn't copy to clipboard, text: {self.data_address}")


class Options_window(QtWidgets.QMainWindow, options.Ui_MainWindow):
    def path_search(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Выберите файл ChromeDriver...')[0]
        if file_path:
            self.chr_input.setText(file_path)
            Options_window.cdrpath = file_path


    def apply_settings(self):
        self.save_offset()
        if self.mode_manual_button.isChecked():
            self.work_mode_assign('manual')
        elif self.mode_back_button.isChecked():
            self.work_mode_assign('back')
        elif self.mode_auto_button.isChecked():
            self.work_mode_assign('auto')
        self.update_log_alias()
        self.close()


    def save_offset(self):
        if self.firstlines.text().strip().isdigit():
            Options_window.offset = max(int(self.firstlines.text().strip()) - 1, 0)
        else:
            self.firstlines.clear()
            self.firstlines.setPlaceholderText('Введите число!')


    def work_mode_assign(self, mode):
        Options_window.work_mode = mode


    def update_log_alias(self):
        if self.log_alias_field.text().strip() == '':
            Options_window.is_log_alias_filled = False
        else:
            Options_window.is_log_alias_filled = True
            Options_window.log_alias = self.log_alias_field.text()


    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.chr_path.clicked.connect(self.path_search)
        #self.save_firstlines.clicked.connect(self.save_offset)
        #self.mode_manual_button.clicked.connect(lambda: self.work_mode_assign('manual'))
        #self.mode_back_button.clicked.connect(lambda: self.work_mode_assign('back'))
        #self.mode_auto_button.clicked.connect(lambda: self.work_mode_assign('auto'))
        #self.log_alias_button.clicked.connect(self.update_log_alias)
        self.opt_save.clicked.connect(self.apply_settings)
        self.opt_decline.clicked.connect(self.close)




class Ending_message(QtWidgets.QMessageBox):
    def closure_signal(self, value):
        Ending_message.closure_flag = bool(value)
        self.close()


    def __init__(self, message):
        super().__init__()
        window_object = QtWidgets.QMessageBox
        window_object.setWindowTitle(self, 'Пациент обработан')
        window_object.setWindowFlags(self, QtCore.Qt.WindowStaysOnTopHint)
        window_object.setText(self, message)
        cont_ = QtWidgets.QPushButton('Продолжить')
        window_object.addButton(self, cont_, 5)
        stop_ = QtWidgets.QPushButton('Остановить программу')
        window_object.addButton(self, stop_, 6)

        cont_.clicked.connect(lambda: self.closure_signal(0))
        stop_.clicked.connect(lambda: self.closure_signal(1))


class Main_application(QtWidgets.QMainWindow, design.Ui_main_window):
    def table_selection(self):
        self.file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Выберите таблицу...')[0]
        if self.file_path[-5:] == '.xlsx' or self.file_path[-4:] == '.xls':
            self.path_to_table_input.setText(self.file_path)
            self.covid_frame.setDisabled(False)
            self.covid_descript.setDisabled(False)
            self.default_log_alias = os.path.basename(self.file_path)[:10]
        else:
            self.path_to_table_input.setPlaceholderText('Выберите файл формата .xls или .xlsx!')


    def paint_if_wrong(self, row):
        self.table_widget.item(row, 0).setBackground(QtGui.QColor('red'))
        self.table_widget.item(row, 1).setBackground(QtGui.QColor('red'))


    def add_table_row(self, first_column, second_column):
        table_row_count = self.table_widget.rowCount()
        for item in self.replacement_dict:
            first_column = first_column.replace(item, self.replacement_dict[item])
        self.table_widget.setRowCount(table_row_count + 1)
        self.table_widget.setItem(table_row_count, 0, QtWidgets.QTableWidgetItem(first_column))
        self.table_widget.setItem(table_row_count, 1, QtWidgets.QTableWidgetItem(second_column))
        logging.info(f'First column: {first_column}\n')
        logging.info(f'Second column: {second_column}\n')

        if first_column != '+':
            self.paint_if_wrong(table_row_count)
            self.error_counter += 1


    def create_appended_row(self, dictionary):
        output_str = ''
        for item in ['surname', 'name', 'patronymic', 'commentary_msg']:
            output_str += f"{self.replacement_dict[item]}: {dictionary[item]}\n"
        output_str += f"Дата рождения: {dictionary['birth_date'][:2]}.{dictionary['birth_date'][2:4]}.{dictionary['birth_date'][4:]}"
        return output_str


    def parsing_main(self):
        self.login_big_frame.setDisabled(True)
        self.start_main_algorithm.setDisabled(True)
        self.table_widget.setRowCount(0)
        self.is_data_correct = True
        self.converted_data = []
        self.error_counter = 0

        if Options_window.is_log_alias_filled:
            decided_alias = Options_window.log_alias
        else:
            decided_alias = self.default_log_alias

        logging_path = f"{date.today().strftime('%b-%d-%Y')}/{decided_alias}.log"
        Path(date.today().strftime('%b-%d-%Y')).mkdir(parents = True, exist_ok = True)
        open(logging_path, 'w+').close()
        #logging.basicConfig(filename = logging_path, encoding='utf-8', level=logging.INFO)
        fh = logging.FileHandler(logging_path, 'w', 'utf-8')
        fh.setLevel(level = logging.INFO)
        logging.basicConfig(handlers = [fh])


        logging.info('------------------------------------')
        logging.info(f'Table Name: {os.path.basename(self.file_path)}')
        logging.info(f'COVID: {self.path_to_table_ill.isChecked()}')
        logging.info(f'Offset: {Options_window.offset}')
        logging.info(f'Mode: {Options_window.work_mode}')
        logging.info(f'ChromeDriver Path: {Options_window.cdrpath}')
        logging.info(f'Path to the table: {self.path_to_table_input.text()}')
        logging.info('Processing the table')

        table_path = self.path_to_table_input.text()
        table = convert_excel_to_list(table_path, Options_window.offset)

        for row_index in range(len(table)):
            logging.info(f'Current index:{row_index}')
            logging.info(f'Raw table data: {table[row_index]}')
            converted_row = row_to_dictionary(table[row_index])

            if converted_row['wrong_field'] == '':
                converted_row['wrong_field'] = '+'
            else:
                self.is_data_correct = False

            if self.path_to_table_ok.isChecked():
                converted_row['analysis-results'] = 'Отрицательный'
            elif self.path_to_table_ill.isChecked():
                converted_row['analysis-results'] = 'Положительный'

            self.converted_data.append(converted_row)

            self.add_table_row(converted_row['wrong_field'], self.create_appended_row(converted_row))



        if self.is_data_correct:
            self.login_big_frame.setDisabled(False)
            self.start_main_algorithm.setDisabled(False)
            self.table_parse_error_descript.setText('Ошибок не выявлено.')

        else:
            self.table_parse_error_descript.setText(f'Выявлено {self.error_counter} ошибочных строк в таблице.')

        self.table_widget.resizeRowsToContents()

    def filling_form_main(self):
        Patient.browser = webdriver.Chrome(Options_window.cdrpath)
        Patient.browser.get(LINK_TO_LOGIN_PAGE)
        Patient.log_in_system(self.username_input.text(), self.password_input.text())
        x = 0


        logging.info('Starting to fill the forms\n')
        for item in self.converted_data:
            self.patient = Patient(item)
            logging.info(f'Current index: {x}\n')
            logging.info(f'Data filled: {item}\n')

            self.patient.click_new_patient_button()

            self.patient.wait_for_main_page()

            self.patient.fill_name()

            self.patient.fill_prior_elements()

            try:
                self.patient.fill_other_personal_info()
            except NameError:
                win_object = Exceptional_message(f'Телефон не удалось распознать. Телефон: {Patient.wrong_number} Исправьте ошибку и продолжите, нажав на кнопку "Продолжить".')
                logging.warning(f"Couldn't recognize the phone pattern. Phone: {Patient.wrong_number}\n")
                win_object.exec_()

            self.patient.fill_document_info()

            try:
                self.patient.fill_living_info()
            except NoSuchElementException:
                print('living crash')
                printed = item['living_address']
                win_object = Exceptional_message(f'Адрес проживания не удается определить. Исправьте ошибку и продолжите, нажав на кнопку "Продолжить". Исходный указанный адрес: {printed}')
                logging.warning(f"Couldn't recognize the living address pattern. Phone: {printed}\n")
                win_object.exec_()

            try:
                self.patient.fill_registry_info()
            except NoSuchElementException:
                print('registry crash')
                printed = item['reg_address']
                win_object = Exceptional_message(f'Адрес регистрации не удается определить. Исправьте ошибку и продолжите, нажав на кнопку "Продолжить". Исходный указанный адрес: {printed}')
                logging.warning(f"Couldn't recognize the registry address pattern. Phone: {printed}\n")
                win_object.exec_()

            try:
                self.patient.fill_workplace_info()
            except NoSuchElementException:
                print('workplace crash')
                printed = item['workplace_address']
                win_object = Exceptional_message(f'Адрес места работы не удается определить. Исправьте ошибку и продолжите, нажав на кнопку "Продолжить". Исходный указанный адрес: {printed}')
                logging.warning(f"Couldn't recognize the workplace address pattern. Phone: {printed}\n")
                win_object.exec_()

            self.patient.fill_medical_info()

            self.patient.fill_referral_info()

            self.patient.fill_analysis_info()

            if self.path_to_table_ill.isChecked():
                self.patient.fill_commentary()

            end_window = Ending_message(f'Проверьте правильность заполнения формы, после чего нажмите кнопку "Продолжить" или закончите выполнение программы, нажав на кнопку "Остановить программу". Введен {str(x+1)} по счету пациент из {len(self.converted_data)}.')
            end_window.exec_()
            if Ending_message.closure_flag == 1:
                self.opt_window.close()
                self.table_parse_error_descript.setText(f'Обработано пациентов: {str(x+1)} из {len(self.converted_data)} перед остановкой программы.')
                #self.close()
                break

            self.patient.submit_form(Options_window.work_mode)
            x += 1


    def showhide_opt(self, is_show):
        self.opt_window.hide()
        if is_show:
            self.opt_window.show()


    def report_issue(self):
        webbrowser.open("mailto:%s?subject=%s" % ("triplenonick@gmail.com", quote("Program error report")))


    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.replacement_dict = {'surname': 'Фамилия',
                                'name':'Имя',
                                'patronymic':'Отчество',
                                'birth_date':'Дата рождения',
                                'gender':'Пол',
                                'phone_number':'Номер телефона',
                                'document_type':'Тип документа',
                                'document_series':'Серия документа',
                                'document_number':'Номер документа',
                                'date_document_given':'Дата выдачи документа',
                                'who_gave_document':'Кем выдан документ',
                                'living_address':'Адрес проживания',
                                'reg_address':'Адрес регистрации',
                                'workplace_name':'Название места работы',
                                'workplace_address':'Адрес места работы',
                                'symptoms':'Наличие симптомов ОРВИ',
                                'doctor_name':'Имя доктора',
                                'pre_diagnosis':'Предварительный диагноз',
                                'sample_taken_date':'Дата взятия анализа',
                                'sample_taken_time':'Время взятия анализа',
                                'result_date':'Дата получения результата',
                                'result_time':'Время получения результата',
                                'commentary_msg':'Комментарий',
                                'wrong_field':'Неправильно заполненные поля'}
        self.opt_window = Options_window()
        Options_window.cdrpath = CHROME_DRIVER_PATH
        Options_window.offset = EXCEL_ROW_OFFSET
        Options_window.work_mode = 'manual'
        Options_window.log_alias = ''
        Options_window.is_log_alias_filled = False
        self.path_to_table_button.clicked.connect(self.table_selection)
        self.path_to_table_ok    .clicked.connect(lambda: self.start_parsing_button.setDisabled(False))
        self.path_to_table_ill   .clicked.connect(lambda: self.start_parsing_button.setDisabled(False))
        self.start_parsing_button.clicked.connect(self.parsing_main)
        self.start_main_algorithm.clicked.connect(self.filling_form_main)
        self.toolButton.clicked.connect(lambda: self.showhide_opt(True))
        self.toolButton_2.clicked.connect(self.report_issue)




def main():
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(' ')
    app = QtWidgets.QApplication([])
    window = Main_application()
    window.setWindowFlags(QtCore.Qt.MSWindowsFixedSizeDialogHint)
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
