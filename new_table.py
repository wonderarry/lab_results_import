import pandas
from settings import *

def convert_excel_to_list(table_path, table_offset):
    table = pandas.ExcelFile(table_path)
    table = table.parse(converters = {NAME_OF_DOC_SERIES_HEADER: lambda x: str(x),
                                    NAME_OF_DOC_NUMBER_HEADER: lambda x: str(x)})
    table_length = len(table.index)
    table_list = []
    for row_index in range(table_offset, table_length):
        appended_row = table.iloc[row_index].tolist()
        appended_row = [str(item).strip() for item in appended_row]
        table_list.append(appended_row)
    return table_list


def clear_date(item):
    if item == 'nan':
        return 'НЕКОРРЕКТНОЕ ЗНАЧЕНИЕ'
    if item[2] == '.':
        return item.replace('.', '')
    return item[8:10] + item[5:7] + item[:4] #Day, Month, Year


def clear_time(item):
    if item == 'nan':
        return ''
    return item


def required(item):
    if item == 'nan' or item == '0':
        return 'НЕКОРРЕКТНОЕ ЗНАЧЕНИЕ'
    return item


def clear_if_empty(item):
    if item == 'nan':
        return ''
    return item


def clear_gender(item):
    if item == 'nan':
        return 'НЕКОРРЕКТНОЕ ЗНАЧЕНИЕ'
    item = str(int(float(item)))
    if item == '1':
        return 'М'
    elif item == '2':
        return 'Ж'
    return 'НЕКОРРЕКТНОЕ ЗНАЧЕНИЕ'


def clear_doc_type(item, series, number):
    if item != 'nan':
        item = str(int(float(item)))
        if item == '1':
            return 'Паспорт'
        elif item == '2':
            return 'Свидетельство о рождении'
        elif item == '3' or item == '4':
            return 'Заграничный паспорт'
    if len(series) == 4 and len(number) == 6:
        return 'Паспорт'
    return 'НЕКОРРЕКТНОЕ ЗНАЧЕНИЕ'


def one_of_addresses(array_values, index):
    if array_values[0] == '' and array_values[1] == '':
        return 'НЕКОРРЕКТНОЕ ЗНАЧЕНИЕ'
    if array_values[0] == '' or array_values[1] == '':
        return array_values[0] + array_values[1]
    return array_values[index]


def row_to_dictionary(row):
    returned_dict = {
            #Basic information about the patient
            'surname':              required(row[row_indices['SURNAME_ROW']]),
            'name':                 required(row[row_indices['NAME_ROW']]),
            'patronymic':           clear_if_empty(row[row_indices['PATRONYMIC_ROW']]),
            'birth_date':           clear_date(row[row_indices['BIRTH_DATE_ROW']]),
            'gender':               clear_gender(row[row_indices['GENDER_ROW']]),
            'phone_number':         required(row[row_indices['PHONE_NUMBER_ROW']]),
            #Document to identify the patient
            'document_type':        clear_doc_type(row[row_indices['DOCUMENT_TYPE_ROW']], row[row_indices['DOCUMENT_SERIES_ROW']], row[row_indices['DOCUMENT_NUMBER_ROW']]),
            'document_series':      clear_if_empty(row[row_indices['DOCUMENT_SERIES_ROW']]),
            'document_number':      required(row[row_indices['DOCUMENT_NUMBER_ROW']]),
            'date_document_given':  clear_date(row[row_indices['DATE_DOCUMENT_GIVEN_ROW']]),
            'who_gave_document':    required(row[row_indices['WHO_GAVE_DOCUMENT_ROW']]),
            #Address where the patient lives
            'living_address':       one_of_addresses([row[row_indices['LIVING_ADDRESS_ROW']], row[row_indices['REG_ADDRESS_ROW']]], 0),
            #Address where the patient is registered
            'reg_address':          one_of_addresses([row[row_indices['LIVING_ADDRESS_ROW']], row[row_indices['REG_ADDRESS_ROW']]], 1),
            #Address where the patient works
            'workplace_name':       clear_if_empty(row[row_indices['WORKPLACE_NAME_ROW']]),
            'workplace_address':    clear_if_empty(row[row_indices['WORKPLACE_ADDRESS_ROW']]),
            #Medical information
            'symptoms':             'нет',
            'doctor_name':          'БЕЗНОСЕНКО ВД',
            'pre_diagnosis':        'Лабораторное обследование',
            #Referral
            'sample_taken_date':    clear_date(row[row_indices['SAMPLE_TAKEN_DATE_ROW']]),
            'sample_taken_time':    clear_time(row[row_indices['SAMPLE_TAKEN_TIME_ROW']]),
            'result_date':          clear_date(row[row_indices['RESULT_DATE_ROW']]),
            'result_time':          clear_time(row[row_indices['RESULT_TIME_ROW']]),
            #Commentary
            'commentary_msg':       clear_if_empty(row[row_indices['IDS_ROW']]),
            #Wrong input in certain fields will be filled in here
            'wrong_field':          ''
            }

    for key in returned_dict:
        if returned_dict[key] == 'НЕКОРРЕКТНОЕ ЗНАЧЕНИЕ':
            returned_dict['wrong_field'] += key + '\n'

    return returned_dict
