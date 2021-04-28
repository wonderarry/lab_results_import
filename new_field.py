from settings import *
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from time import sleep

class Patient():
    def __init__(self, source):
        self.full_name =            [source['surname'],
                                    source['name'],
                                    source['patronymic']
                                    ]

        self.other_personal_info =  [source['birth_date'],
                                    source['gender'].replace('М', '0').replace('Ж', '1'),
                                    source['phone_number']
                                    ]

        self.document_info =        [source['document_type'].replace('Паспорт', '1').replace('Заграничный паспорт', '2').replace('Свидетельство о рождении', '3'),
                                    source['document_series'],
                                    source['document_number'],
                                    source['date_document_given'],
                                    source['who_gave_document']
                                    ]

        self.living_info =          Patient.reform_address(source['living_address'])

        self.registry_info =        Patient.reform_address(source['reg_address'])

        self.workplace_info =       [source['workplace_name'],
                                    source['workplace_address']
                                    ]

        self.medical_info =         [source['symptoms'],
                                    source['doctor_name'],
                                    source['pre_diagnosis']
                                    ]

        self.referral_info =        [source['sample_taken_date'],
                                    source['sample_taken_time'],
                                    source['analysis-results'].replace('Отрицательный', '1').replace('Положительный', '2'),
                                    source['result_date'],
                                    source['result_time']
                                    ]

        self.commentary =           source['commentary_msg']

        self.is_passport_int =      int(self.document_info[0] == '1')


    def click_new_patient_button(self):
        loader_element = WebDriverWait(Patient.browser, 25).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'Header-Buttons')))
        Patient.browser.find_elements_by_class_name('Button')[4].click()


    def wait_for_main_page(self):
        loader_element = WebDriverWait(Patient.browser, 25).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'FormPage')))


    def select_from_list(self, class_name, class_index, list_class_base, element_index):
        list_item = Patient.browser.find_elements_by_class_name(class_name)[class_index]
        list_item.click()
        item_id = list_class_base + str(element_index)
        loader_element = WebDriverWait(Patient.browser, 25).until(expected_conditions.presence_of_element_located((By.ID, item_id)))
        sleep(1)
        item = list_item.find_element_by_id(item_id)
        item.click()


    def fill_multiple_choice(self, class_name, class_index):
        item = Patient.browser.find_elements_by_class_name(class_name)[class_index].find_element_by_class_name('Field-FieldContainer')
        sleep(2)
        item.click()
        if len(item.find_elements_by_class_name('SearchField-OptionButton')) == 1:
            item.find_element_by_class_name('SearchField-OptionButton').click()
        elif len(item.find_elements_by_class_name('SearchField-OptionButton')) != 1:
            raise NoSuchElementException


    def check_checkbox(self, class_name, class_index):
        item = Patient.browser.find_elements_by_class_name(class_name)[class_index]
        item.click()


    def input_text_field(self, class_name, class_index, value):
        item = Patient.browser.find_elements_by_class_name(class_name)[class_index]
        item.send_keys(value)


    def fill_prior_elements(self):
        self.select_from_list('SelectInput', 2, 'react-select-4-option-', self.document_info[0])
        self.offset = 0
        if self.document_info[0] == '1':
            self.offset = 1

        sleep(0.5)
        self.select_from_list('SelectInput', 9, 'react-select-11-option-', 1)

        sleep(0.5)
        self.check_checkbox('MaterialItem-Checkbox', 0)

        #sleep(2.5)
        loader_element = WebDriverWait(Patient.browser, 25).until(expected_conditions.presence_of_element_located((By.NAME, 'results.res1.isIggOnly')))
        self.select_from_list('SelectInput', 11, 'react-select-13-option-', self.referral_info[2])


    def fill_name(self):
        Patient.browser.find_element_by_name('patient.secondName').click()
        Patient.browser.execute_script("document.getElementsByName('patient.secondName')[0].value='" + self.full_name[0] + "';")

        Patient.browser.find_element_by_name('patient.firstName').click()
        Patient.browser.execute_script("document.getElementsByName('patient.firstName')[0].value='" + self.full_name[1] + "';")

        Patient.browser.find_element_by_name('patient.patronName').click()
        Patient.browser.execute_script("document.getElementsByName('patient.patronName')[0].value='" + self.full_name[2] + "';")


    def fill_other_personal_info(self):
        self.input_text_field('Field', 5, self.other_personal_info[0])

        self.select_from_list('SelectInput', 0, 'react-select-2-option-', self.other_personal_info[1])

        self.select_from_list('PhoneInput-CodeSelect', 0, 'react-select-3-option-', 0)
        if Patient.reform_phone_number(self.other_personal_info[2])[:5] == 'raise':
            self.wrong_number = Patient.reform_phone_number(self.other_personal_info[2])[5:]
            raise NameError
        self.input_text_field('PhoneInput-NumberInput', 0, Patient.reform_phone_number(self.other_personal_info[2]))


    def fill_document_info(self):

        if self.document_info[0] == '1':
            self.input_text_field('Field', 9, self.document_info[1])
            self.input_text_field('Field', 10, self.document_info[2])
        else:
            Patient.browser.find_elements_by_class_name('Field')[9].click()
            sleep(0.5)
            Patient.browser.find_elements_by_class_name('Field')[9].send_keys(Keys.BACK_SPACE)
            Patient.browser.execute_script("document.getElementsByName('patient.document.num')[0].value='" + self.document_info[1] + ' ' + self.document_info[2][:-1] + "';")
            Patient.browser.find_elements_by_class_name('Field')[9].send_keys(self.document_info[2][-1])
        self.input_text_field('Field', 10 + self.offset, self.document_info[3])
        self.input_text_field('Field', 11 + self.offset, self.document_info[4])


    def fill_living_info(self):
        #self.check_checkbox('AddressFieldExtended-LabelCheckbox', 0)
        sleep(1)
        #try:
        self.input_text_field('TextInput--width_wide', 1, self.living_info[0])
        self.input_text_field('Field', 13 + self.offset, self.living_info[1])
        self.fill_multiple_choice('Field', 12 + self.offset)
        #except NoSuchElementException:
        #    item_i = Patient.browser.find_elements_by_class_name('TextInput--width_wide')[1]
        #    item_i.click()
        #    item_i.send_keys(Keys.CONTROL, 'a', Keys.DELETE)
        #    self.check_checkbox('AddressFieldExtended-LabelCheckbox', 0)
        #    self.input_text_field('TextInput--width_wide', 1, self.living_info[0])
        #    self.fill_multiple_choice('Field', 12 + self.offset)
        #item = Patient.browser.find_elements_by_class_name('Field')[12 + self.offset].find_element_by_class_name('Field-FieldContainer')
        #item.click()
        #sleep(2)
        #try:
        #item.find_element_by_class_name('SearchField-OptionButton').click()
        #except NoSuchElementException:
        #    Patient.browser.find_element_by_name('patient.factAddress.address.text').send_keys(Keys.CONTROL, 'a', Keys.DELETE)
        #    Patient.browser.find_elements_by_class_name('Field')[13 + self.offset].send_keys(Keys.CONTROL, 'a', Keys.DELETE)
        #    self.input_text_field('TextInput--width_wide', 1, self.registry_info[0])
        #    self.input_text_field('Field', 13 + self.offset, self.registry_info[1])
        #    sleep(2)
        #    item.click()
        #    item.find_element_by_class_name('SearchField-OptionButton').click()


    def fill_registry_info(self):
        sleep(1)
        #try:
        self.input_text_field('TextInput--width_wide', 2, self.registry_info[0])
        Patient.browser.find_element_by_name('patient.registrationAddress.flat').send_keys(self.registry_info[1])
        self.fill_multiple_choice('Field', 16 + self.offset)
        #except NoSuchElementException:
        #    item_i = Patient.browser.find_elements_by_class_name('TextInput--width_wide')[2]
        #    item_i.click()
        #    item_i.send_keys(Keys.CONTROL, 'a', Keys.DELETE)
        #    self.check_checkbox('AddressFieldExtended-LabelCheckbox', 1)
        #    self.input_text_field('TextInput--width_wide', 2, self.registry_info[0])
        #    self.fill_multiple_choice('Field', 16 + self.offset)
        #item = Patient.browser.find_elements_by_class_name('Field')[16 + self.offset].find_element_by_class_name('Field-FieldContainer')
        #sleep(2)
        #item.click()
        #item.find_element_by_class_name('SearchField-OptionButton').click()


    def fill_workplace_info(self):
        if self.workplace_info[0].lower() in ('нет', 'пенсионер', 'пенсионерка'):
            self.workplace_info[0] = ''
        if self.workplace_info[1].lower() in ('дома','нет', 'пенсионер', 'пенсионерка'):
            self.workplace_info[1] = ''
        self.input_text_field('Field', 20 + self.offset, self.workplace_info[0])
        if self.workplace_info[1] != '':
            try:
                Patient.browser.find_element_by_name('patient.work.factAddress.address').send_keys(self.workplace_info[1])
                self.fill_multiple_choice('SearchField', 2)
            except NoSuchElementException:
                item_i = Patient.browser.find_elements_by_class_name('TextInput--width_wide')[4]
                item_i.click()
                item_i.send_keys(Keys.CONTROL, 'a', Keys.DELETE)
                self.check_checkbox('AddressField-LabelCheckbox', 0)
                self.input_text_field('TextInput--width_wide', 4, self.workplace_info[1])
                self.fill_multiple_choice('SearchField', 2)
            #item = Patient.browser.find_elements_by_class_name('SearchField')[2].find_element_by_class_name('Field-FieldContainer')
            #sleep(2)
            #item.click()
            #item.find_element_by_class_name('SearchField-OptionButton').click()


    def fill_medical_info(self):
        if self.medical_info[0] == 'да':
            Patient.browser.find_elements_by_class_name('CheckboxField')[5].click()
        else:
            Patient.browser.find_elements_by_class_name('CheckboxField')[6].click()
        self.input_text_field('Field', 28 + self.offset, self.medical_info[1])
        self.input_text_field('Field', 29 + self.offset, self.medical_info[2])
        self.fill_multiple_choice('Field', 29 + self.offset)
        #item = Patient.browser.find_elements_by_class_name('Field')[29 + self.offset].find_element_by_class_name('Field-FieldContainer')
        #sleep(1)
        #item.click()
        #item.find_element_by_class_name('SearchField-OptionButton').click()

        #self.check_checkbox('CheckboxField', 6)
        Patient.browser.find_element_by_name('medicalInformation.disDate').send_keys(Keys.CONTROL, 'a', Keys.DELETE)
        Patient.browser.find_element_by_name('medicalInformation.disDate').send_keys(self.referral_info[0])



    def fill_referral_info(self):
        self.input_text_field('Field', 33 + self.offset, self.referral_info[0])
        if self.referral_info[1] != '':
            self.input_text_field('Field', 34 + self.offset, self.referral_info[1])


    def fill_analysis_info(self):
        if self.referral_info[4] != '':
            self.input_text_field('Field', 38 + self.offset, self.referral_info[4])
        else:
            self.check_checkbox('Button--light', 4)
        Patient.browser.find_elements_by_class_name('Field')[37 + self.offset].send_keys(Keys.CONTROL, 'a', Keys.DELETE)
        self.input_text_field('Field', 37 + self.offset, self.referral_info[3])


    def fill_commentary(self):
        self.input_text_field('TextAreaInput', 0, self.commentary)


    def submit_form(self, mode):
        if mode == 'back':
            self.check_checkbox('FormPage-ActionButton', 0)
            Patient.browser.find_element_by_class_name('Modal-Footer').find_elements_by_class_name('Button')[1].click()
        elif mode == 'auto':
            pass


    @classmethod
    def log_in_system(cls, username, password):
        cls.browser.find_element_by_name('login').send_keys(username)
        cls.browser.find_element_by_name('password').send_keys(password)
        cls.browser.find_element_by_class_name('App-SubmitButton').click()


    @staticmethod
    def reform_phone_number(x):
        source = x.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
        if len(source) == 10:
            return source
        elif len(source) == 11 and (source[0] == '8' or source[0] == '7'):
            return source[1:]
        elif len(source) == 12 and source[:2] == '+7':
            return source[2:]
        else:
            return 'raise' + x


    @staticmethod
    def reform_address(source):
        if source.lower().replace(',','').replace(':','').split()[-1] == 'москва' and source.lower().replace(',','').replace(':','').split()[0] in ['город', 'г.']:
            return ['Адрес некорректен!', '']
        if source[:6].isdigit():
            source = source[6:]
        if source[0] == ',':
            source = source[1:]
        if source[-1] == ',':
            source = source[:-1]
        if ':' in source:
            if source[:7] == 'Страна:':
                source = source[7:].strip()
                source = source[6:].strip()
            source = source.replace('Район:', ' ').replace('Город:',' ').replace('Улица:',' ').replace('Дом:',' ').replace('Корпус:',' ').replace('Квартира:',' ')

        elif source.isupper():
            source = source[1:].replace(' РАЙОН', '').replace(' УЛ','').replace(' КОРП','').replace(' КВ','')

        else:
            if '/' in source and not(source[source.find('/')+1:].isdigit()):
                source = source[:source.find('/')] + source[source.find('.')+1:]

            if '/' in source:
                source = source[:source.find('/')] + ' ' + source[source.find('/')+1:]

            replacement = [', ул.', ',ул.',', УЛ.',',УЛ.',', кв.',',кв.',', КВ.',',КВ.',', д.',',д.',', Д.',',Д.',', КОРП.',',КОРП.',', корп.',',корп.', 'ул.', 'УЛ.', 'кв.', 'КВ.', 'д.', 'Д.', 'КОРП.', 'корп.']
            for i in replacement:
                source = source.replace(i, ' ')
        source = source.replace(',', ' ').replace('.', ' ').replace('Россия', ' ').replace('россия', ' ').replace('пр-кт', 'проспект').replace('ПР-КТ', 'проспект').replace('б-р', 'бульвар').replace('Б-Р', 'бульвар')
        return [' '.join(source.split()[:-1]), source.split()[-1]]
