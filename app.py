import pickle
from pathlib import Path
import logging
import streamlit_authenticator as stauth  # pip install streamlit-authenticator

import streamlit as st
import pandas as pd
import joblib
import gspread
# Загрузка модели
model = joblib.load('gboost_pipeline_2.0.pkl')
# Функция для генерации PDF
from datetime import datetime
from fpdf import FPDF
from PIL import Image

from kurs import return_currency

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
img = Image.open("mobi_icon.ico")
st.set_page_config(
        page_title="MobiCenter",
        page_icon=img,
        layout="wide"
)

names = [
    "Абдурахмонов Джурабек",
    "Алиева Гулзода",
]
usernames = [
    "jurabek",
    "gulzoda",
]

# load hashed passwords
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
    "sales_dashboard", "abcdef", cookie_expiry_days=30)

name_, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")


if authentication_status:
    citizenship = st.sidebar.selectbox("Гражданство", ["Узбекистан", "Таджикистан"])
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                width: 40px important;
                background-color: white;
            }
            .block-container {
                        padding-top: 0rem;
                        padding-bottom: 0rem;
                        padding-left: 5rem;
                        padding-right: 5rem;
                    }
            #ManMenu {visibility:hidden;}
            footer {visibility:hidden;}
            header {visibility:hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    authenticator.logout("Выход", "sidebar")
    if citizenship == "Узбекистан":
        def generate_pdf(data, document_number, date):
            # Create instance of FPDF class
            pdf = FPDF()

            # Add a page
            pdf.add_page()

            # Set font for the title
            pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
            pdf.set_font('DejaVu', '', 14)

            pdf.image('Logo.png', x=15, y=15, w=40)
            pdf.ln(20)
            # Title
            pdf.cell(200, 10, txt="Скоринг рассрочки",  ln=True, align='C')
            pdf.ln(10)  # Add a little space after the title


            # Define the variables list on the left side
            # Mapping between internal variable names and human-readable names
            variable_mapping = {
                "Manager": "Менеджер",
                'Region': 'Филиал',
                'Name': 'ФИО',
                'Address': 'Адрес',
                'Phone': 'Телефон номер',
                'Age': 'Возраст',
                'Gender': 'Пол',
                'Amount': 'Сумма',
                'Duration': 'Период',
                'MaritalStatus': 'Семейный статус',
                'Income': 'Доход',
                'Dependants': 'Иждивенцы',
                "OccupationBranch": 'Сфера деятельности',
                "Occupation": "Должность",
                "ExpCat": 'Опыт работы',
                'Result': 'Результат',
                'Probability': 'Вероятность возврата',
                'Date': 'Дата',
                'DocumentNumber': 'Номер документа'
            }

            var = ['Manager', 'Region', 'Name', 'Address', 'Phone', 'Age', 'Gender', 'Amount', 'Duration', 'MaritalStatus',
                'Income', 'Dependants', 'OccupationBranch', 'Occupation', 'ExpCat', 'Result', 'Probability', 'Date', 'DocumentNumber']

            # Add content to the PDF using a table
            pdf.set_fill_color(255, 255, 255)  # Set white fill color
            col_width = 80
            row_height = 10
            x_position = (pdf.w - col_width * 2) / 2  # Calculate x position to center the table
            y_position = pdf.get_y()
            for var_name in var:
                # Get the human-readable name corresponding to the internal variable name
                variable = variable_mapping.get(var_name, '')
                value = data.get(var_name, [''])[0]  # Get the value from data or empty string if not found
                pdf.set_xy(x_position, y_position)
                pdf.cell(col_width, row_height, txt=variable, border=1, fill=False)
                pdf.cell(col_width, row_height, txt=str(value), border=1, fill=False)
                pdf.ln(row_height)
                y_position = pdf.get_y()
            pdf.set_xy(x_position, pdf.get_y() + 20)  # Move down 10 units
            pdf.cell(col_width, row_height, txt="Менежер:", border=0, fill=False)
            pdf.cell(col_width, row_height, txt="Директор:", border=0, fill=False)

            # Save the PDF to a file
            pdf.output("result.pdf")

            # Return the PDF file name or content depending on your requirement
            with open("result.pdf", "rb") as pdf_file:
                PDFbyte = pdf_file.read()

            st.download_button(label="Скачать документ",
                            data=PDFbyte,
                            file_name="test.pdf",
                            mime='application/octet-stream')

        # st.sidebar.image("Logo.png", use_column_width=False, width=200, height=10)
        st.image("Logo.png", use_column_width=False, width=150)
        # Ввод данных с использованием инпутов
        st.title('Модель скоринга')
        top_left, top_right = st.columns((3, 1))
        prediction = None
        input_data = None
        document_number = None
        current_date = None
        kredit = None
        with top_left:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                managers = {
                    "jurabek": ["Абдурахмонов Джурабек"],
                    "gulzoda": ["Алиева Гулзода"],
                }
                manager = st.selectbox(r'$\textsf{\normalsize Менеджер}$', managers.get(username, "Абдурахмонов Джурабек"))
                region_options = {
                            "Абдурахмонов Джурабек": "Питер",
                            "Алиева Гулзода": "Питер",
                        }
                default_region = "Питер"  # Default district if no match found

                region = region_options.get(manager, default_region)
                st.selectbox(r'$\textsf{\normalsize Филиал}$', [region])
                name = st.text_input(r'$\textsf{\normalsize ФИО}$', '')
                address = st.selectbox(r'$\textsf{\normalsize Адрес}$', ["Андижанская область", "Бухарская область", "Джизакская область",
                                                                                    "Навоийская область", "Наманганская область", "Самаркандская область",
                                                                                    "Сурхандарьинская область", "Сырдарьинская область", "Ташкентская область",
                                                                                    "Ферганская область", "Кашкадарьинская область", "Хорезмская область", "Каракалпакстан"])
            with col2:
                phone = st.text_input(r'$\textsf{\normalsize Телефон номер}$', placeholder="89015879792")
                age = st.number_input(r'$\textsf{\normalsize Возраст}$', value=24, step=1)
                gender = st.selectbox(r'$\textsf{\normalsize Пол}$', ['Мужчина', 'Женщина'])
                amount = st.number_input(r'$\textsf{\normalsize Сумма}$', value=0, placeholder="Цена телефона")
            with col3:
                duration = st.selectbox(r'$\textsf{\normalsize Период}$', [3, 6, 9, 12])
                marital_status = st.selectbox(r'$\textsf{\normalsize Семейный статус}$', ['Женат/Замужем', 'Не женат/Не замужем', 'В разводе', 'Другое'])
                income = st.number_input(r'$\textsf{\normalsize Доход}$', value=0, placeholder="Месячный доход")
                dependants = st.selectbox(r'$\textsf{\normalsize Иждивенцы}$', [0, 1, 2, 3, 4, 5])
            with col4:
                occupation_branch = st.selectbox(r'$\textsf{\normalsize Сфера деятельности}$', ['Производство', 'Другая сфера', 'Торговля', 'Банковское деятельность', 'Военный/Правоохранительные органы', 'Образование', 'Логистика', 'Сельское хозяйство', 'Медицина',
                                                                                'Строительство', 'ЖКХ', 'Пенсионер'])
                occupation = st.selectbox(r'$\textsf{\normalsize Должность}$', ['Рабочий', 'Рядовой сотрудник', 'Высококвалифицированный специалист', 'Пенсионер/Студент', 'Директор', 'Начальник'])
                exp_cat = st.selectbox(r'$\textsf{\normalsize Опыт работы}$', ['От 3-х до 5 лет', 'Более 5 лет', 'От 1-го до 3 лет', 'Менее 1 года', 'Без опыта'])
                button2_color = "#FFFF00"
                button_style = f"""
                    <style>
                    div.stButton > button:first-child {{
                    background-color: #FF8000;
                    color: white !important;}}
                    <style>
                """
                st.markdown(button_style, unsafe_allow_html=True)
                if st.button('Получить результат'):
                    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    document_number = f'Doc_{current_date.replace(" ", "_").replace(":", "_")}'

                    name_dict = {
                        "Женат/Замужем": "Оилали",
                        "Не женат/Не замужем": "Уйланмаган/Турмуш курмаган",
                        "В разводе": "Ажрашган",
                        "Другое": "Бошка",
                        "Производство": 'Ишлаб чикариш',
                        "Торговля": 'Савдо',
                        "Банковское деятельность": 'Банк сохаси',
                        "Военный/Правоохранительные органы": 'Харбий',
                        "Образование": 'Таълим сохаси',
                        "Логистика": 'Логистика',
                        "Сельское хозяйство": 'Кишлок хужалиги',
                        "Медицина": 'Медицина сохаси',
                        "Строительство": 'Курилиш сохаси',
                        "ЖКХ": 'ЖКХ',
                        "Пенсионер": 'Пенсионер',
                        "Другая сфера": 'Бошка соха',
                        "Рабочий": 'Оддий ишчи',
                        "Рядовой сотрудник": 'Оддий ишчи',
                        "Высококвалифицированный специалист": 'Юкори малакали мутхассис',
                        "Пенсионер/Студент": 'Пенсионер/Студент',
                        "Директор": 'Бошлиг/Хужаин',
                        "Начальник": 'Бошлиг/Хужаин',
                        "От 3-х до 5 лет": '3 йилдан 5 гача',
                        "Более 5 лет": '5 йилдан зиёд',
                        "От 1-го до 3 лет": '1 йилдан 3 гача',
                        "Менее 1 года": '1 йилдан кам',
                        "Без опыта": 'Тажрибаси йук'
                    }
                    price_currency = float(return_currency())
                    logger.info("Current currency price: %s", price_currency)
                    logger.info("Amount credit rub: %s", amount)
                    logger.info("Amount credit som: %s", amount*price_currency)
                    logger.info("Income in rub: %s", income)
                    logger.info("Income in som: %s", income*price_currency)
                    input_data = pd.DataFrame({
                        'Age': [age],
                        'Gender': [1 if gender == 'Мужчина' else 0],
                        'Amount': [amount*price_currency],
                        'Duration': [duration],
                        'MaritalStatus': [name_dict[marital_status]],
                        'Income': [income*price_currency],
                        'Dependants': [dependants],
                        'OccupationBranch': [name_dict[occupation_branch]],
                        'Occupation': [name_dict[occupation]],
                        'ExpCat': [exp_cat]
                    })

                    prediction = model.predict_proba(input_data)[:, 0]
                    input_data["MaritalStatus"] = marital_status
                    input_data["Amount"] = amount
                    input_data["CreditHistoryCount"] = 0
                    input_data["Income"] = income
                    input_data["OccupationBranch"] = occupation_branch
                    input_data["Occupation"] = occupation
                    input_data['Manager'] = manager
                    input_data['Region'] = region
                    input_data['Name'] = name
                    input_data["Address"] = address
                    input_data['Phone'] = phone
                    input_data['Result'] = 'Одобрено' if prediction > 1 - 0.1 else 'Отказано'
                    input_data['Gender'] = gender
                    input_data['Probability'] = f'{round(prediction[0]*100, 2)}%'
                    input_data['Date'] = current_date
                    input_data['DocumentNumber'] = document_number

        with top_right:
            def authenticate_gspread():
                # Load Google Sheets API credentials
                from  read_json import  response_json
                response_ = response_json()
                sa = gspread.service_account_from_dict(response_)
                return sa

            # Function to duplicate data to Google Sheets
            def duplicate_to_gsheet(new_row):
                # Authenticate with Google Sheets
                gc = authenticate_gspread()

                # Create a new Google Sheets spreadsheet
                sh = gc.open("MobiCenterRu")

                # Select the first sheet (index 0)
                worksheet = sh.worksheet("Scoring")

                # Check if there's any content in the worksheet
                existing_data = worksheet.get_all_values()

                # Get existing headers if they exist
                headers = existing_data[0] if existing_data else None

                if not headers:
                    headers = ['Менежер', 'Филиал', 'Телефон номер', 'ФИО', 'Адрес', 'Возраст', 'Пол', 'Сумма', 'Период', 'Семейный статус', 'Количество кредитов(история)', 'Доход',
                            'Иждивенцы', 'Сфера занятости', 'Роль', 'Стаж работы', 'Результат', 'Вероятность возврата', 'Дата', 'Номер документа']
                    worksheet.append_row(headers)

                # Convert the new_row DataFrame to a list and append it to the worksheet
                new_row = new_row[['Manager', 'Region', 'Phone', 'Name', 'Address', 'Age', 'Gender', 'Amount', 'Duration', 'MaritalStatus', 'CreditHistoryCount', 'Income',
                                'Dependants', 'OccupationBranch', 'Occupation', 'ExpCat', 'Result', 'Probability', 'Date', 'DocumentNumber']]
                new_row_list = new_row.values.tolist()
                worksheet.append_rows(new_row_list)

            # Предсказание
            st.subheader('Результат:')
            if prediction is not None:
                st.write(f'Кредит кайтариш эхтимоли: {round(prediction[0]*100, 2)}%')

                if prediction > 1 - 0.1:
                    if_success = "Одобрено!"
                    htmlstr1 = f"""<p style='background-color:green;
                                color:white;
                                font-size:35px;
                                border-radius:3px;
                                line-height:60px;
                                padding-left:17px;
                                opacity:0.6'>
                                {if_success}</style>
                                <br></p>"""
                    st.markdown(htmlstr1, unsafe_allow_html=True)

                    st.balloons()
                    generate_pdf(input_data, document_number, current_date)
                    duplicate_to_gsheet(input_data)
                else:
                    st.error(r'$\textsf{\Large Отказано! 😞}$')
                    generate_pdf(input_data, document_number, current_date)
                    duplicate_to_gsheet(input_data)

                # generate_pdf(input_data, document_number, current_date)

    if citizenship == "Таджикистан":

        # Загрузка модели
        model = joblib.load('tj_consolidate_pycaret_02.pkl')

        st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                width: 40px important;
                background-color: white;
            }
            .block-container {
                        padding-top: 1rem;
                        padding-bottom: 0rem;
                        padding-left: 5rem;
                        padding-right: 5rem;
                    }
        </style>
        """,
        unsafe_allow_html=True,
    )

        def generate_pdf(data, document_number, date):
            # Create instance of FPDF class
            pdf = FPDF()

            # Add a page
            pdf.add_page()

            # Set font for the title
            pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
            pdf.set_font('DejaVu', '', 14)

            pdf.image('Logo.png', x=15, y=15, w=40)
            pdf.ln(20)
            # Title
            pdf.cell(200, 10, txt="Скоринг рассрочки",  ln=True, align='C')
            pdf.ln(10)  # Add a little space after the title


            # Define the variables list on the left side
            # Mapping between internal variable names and human-readable names
            variable_mapping = {
                'Manager': 'Менеджер',
                'district': 'Адрес',
                'phone': 'Телефон номер',
                'name': 'ФИО',
                'age': 'Возраст',
                'gender': 'Пол',
                'amount': 'Сумма рассрочки',
                'duration': 'Срок',
                'marital_status': 'Семейный статус',
                'credit_history_count': 'Количество кредитов(история)',
                'Result': 'Результат',
                'Probability': 'Вероятность возврата',
                'Date': 'Дата',
                'DocumentNumber': 'Номер документа'
            }

            var = ['Manager', 'district', 'phone', 'name', 'age', 'gender', 'amount', 'duration',
                'marital_status', 'credit_history_count', 'Result', 'Probability', 'Date', 'DocumentNumber']

            # Add content to the PDF using a table
            pdf.set_fill_color(255, 255, 255)  # Set white fill color
            col_width = 80
            row_height = 10
            x_position = (pdf.w - col_width * 2) / 2  # Calculate x position to center the table
            y_position = pdf.get_y()
            for var_name in var:
                # Get the human-readable name corresponding to the internal variable name
                variable = variable_mapping.get(var_name, '')
                value = data.get(var_name, [''])[0]  # Get the value from data or empty string if not found
                pdf.set_xy(x_position, y_position)
                pdf.cell(col_width, row_height, txt=variable, border=1, fill=False)
                pdf.cell(col_width, row_height, txt=str(value), border=1, fill=False)
                pdf.ln(row_height)
                y_position = pdf.get_y()
            pdf.set_xy(x_position, pdf.get_y() + 20)  # Move down 10 units
            pdf.cell(col_width, row_height, txt="Менеджер:", border=0, fill=False)
            pdf.cell(col_width, row_height, txt="Директор:", border=0, fill=False)

            # current_x = pdf.get_x()  # Get current X position
            # current_y = pdf.get_y()  # Get current Y position

            # # Calculate new positions with desired margins
            # new_x = current_x -100 # Add 20mm to the right
            # new_y = current_y + 15   # Subtract 5mm from the top (moving upwards)

            # # Set new position
            # pdf.set_xy(new_x, new_y)
            # pdf.cell(0, 10, 'Менеджер:', 0, 0, 'L')
            # pdf.cell(0, 10, 'Директор:', 0, 0, 'C')
            # Output the cell
            # pdf.cell(0, 10, txt="Подпись: ______________________", ln=True, align='R')

            # Save the PDF to a file
            pdf.output("result.pdf")

            # Return the PDF file name or content depending on your requirement
            with open("result.pdf", "rb") as pdf_file:
                PDFbyte = pdf_file.read()

            st.download_button(label="Скачать документ",
                            data=PDFbyte,
                            file_name="test.pdf",
                            mime='application/octet-stream')

        st.image("Logo.png", use_column_width=False, width=150)
        # Ввод данных с использованием инпутов
        st.title('Модель скоринга')


        top_left, top_right = st.columns((3, 1))
        prediction = None
        input_data = None
        document_number = None
        current_date = None
        with top_left:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    manager = st.selectbox(r'$\textsf{\normalsize Менеджер}$', [name_])
                    region_options = {
                            "Абдурахмонов Джурабек": "Питер",
                            "Алиева Гулзода": "Питер",
                            }
                    default_region = "Питер"  # Default district if no match found

                    region = region_options.get(manager, default_region)
                    # st.selectbox(r'$\textsf{\normalsize Филиал}$', [region])

                    name = st.text_input(r'$\textsf{\normalsize ФИО}$', '')
                    # surname = st.text_input(r'$\textsf{\normalsize Фамилия}$', '')

                    # # Use district variable in your Streamlit app
                    # st.write(rf'$\textsf{{\normalsize Филиал}}$: {district}')
                    district = st.selectbox(r'$\textsf{\normalsize Адрес}$', ["Джаббор Расулов", "Спитамен", "Пенджикент", "Худжанд", "Душанбе",
                                                                              "Мастчох", "Хиссор", "Гафуров", "Рудаки", "Балхи", "Шахритюз", "Ифсара",
                                                                              "Кулоб", "Истаравшан", "Вахдат", "Конибодом", "Бохтар", "Зафаробод",
                                                                              "Ашт", "Джайхун", "Шахринав", "Ёвон", "Дангара",
                                                                              "Турсунзода", "Деваштич", "Кушониён", "Муминобод", "Хамадони",
                                                                              "Восе", "Кубодиён", "Сомон", "Фархор", "Дусти", "Темурмалик",
                                                                              "Вахш", "Пяндж", "Хуросон", "Шахринав", "Джоми", "Сангтуда",
                                                                              "Кангурт", "Носири Хусрав", "Файзобод", "Фаровон", "Чирик",
                                                                              "Гулистон", "Бустон", "Левакант", "Хоруг", "Табашар",
                                                                              "Норак", "Фардовси", "Фарохор", "Курган"])

                with col2:
                    age = st.number_input(r'$\textsf{\normalsize Возраст}$', value=24, step=1)
                    gender = st.selectbox(r'$\textsf{\normalsize Пол}$', ['Мужчина', 'Женщина'])
                    marital_status = st.selectbox(r'$\textsf{\normalsize Семейный статус}$', ['Женат/Замужем', 'Не женат/Не замужем', 'Вдова/Вдовец', 'Разведен'])


                with col3:
                    amount = st.number_input(r'$\textsf{\normalsize Сумма рассрочки}$', value=0, placeholder="Цена телефона")
                    duration = st.selectbox(r'$\textsf{\normalsize Срок}$', [3, 6, 9, 12])
                    phone = st.text_input(r'$\textsf{\normalsize Телефон номер}$', value=None, placeholder="+7901493243")

                    # credit_history_count = st.number_input(r'$\textsf{\normalsize Количество рассрочки (история клиента)}$', value=0, step=1)
                    # kredit = st.selectbox(r'$\textsf{\normalsize Активный кредит в других банках}$', ['Нет', "Да"])
                    if st.button('Получить результат', type="primary"):
                        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        document_number = f'Doc_{current_date.replace(" ", "_").replace(":", "_")}'
                        mapping_dis = {
                        "Душанбе": "dushanbe",
                        "Худжанд": "khujand",
                        "Пенджикент": "panjakent",
                        "Джаббор Расулов": "j.rasulov",
                        "Спитамен": "spitamen",
                        "Мастчох": 'mastchoh',
                        "Хиссор": 'hissor',
                        "Гафуров": 'b.gafurov',
                        "Рудаки": 'rudaki',
                        "Балхи": 'balkhi',
                        "Шахритюз": 'shahrituz',
                        "Ифсара": 'isfara',
                        "Кулоб": 'kulob',
                        "Истаравшан": 'istaravshan',
                        "Вахдат": 'vahdat',
                        "Конибодом": 'konibodom',
                        "Бохтар": 'bokhtar',
                        "Зафаробод": 'zafarobod',
                        "Ашт": 'asht',
                        "Джайхун": 'jayhun',
                        "Шахристон": 'shahriston',
                        "Ёвон": 'yovon',
                        "Дангара": 'dangara',
                        "Турсунзода": 'tursunzoda',
                        "Деваштич": 'devashtich',
                        "Кушониён": 'kushoniyon',
                        "Муминобод": 'muminobod',
                        "Хамадони": 'hamadoni',
                        "Восе": 'vose',
                        "Кубодиён": 'kubodiyon',
                        "Сомон": 'somon',
                        "Фархор": 'farkhor',
                        "Дусти": 'dusti',
                        "Темурмалик": 'temurmalik',
                        "Вахш": 'vakhsh',
                        "Пяндж": 'panj',
                        "Хуросон": 'khuroson',
                        "Шахринав": 'shahrinav',
                        "Джоми": 'jomi',
                        "Сангтуда": 'sangtuda',
                        "Кангурт": 'kangurt',
                        "Носири Хусрав": 'nosiri khusrav',
                        "Файзобод": 'fayzobod',
                        "Фаровон": 'farovon',
                        "Чирик":  'chirik',
                        "Гулистон": 'guliston',
                        "Бустон": 'buston',
                        "Левакант": 'levakant',
                        "Хоруг": 'khorug',
                        "Табашар": 'tabashar',
                        "Норак": 'norak',
                        "Фардовси": 'firdavsi',
                        "Фарохор": 'farhor',
                        "Курган": 'kurgan'
                        }
                        mapping_mar = {
                            'Женат/Замужем': 'married', 'Не женат/Не замужем': 'single', 'Вдова/Вдовец': 'widow/widower', 'Разведен': 'divorced'
                        }

                        input_data = pd.DataFrame({
                            'age': [age],
                            'amount': [amount],
                            'credit_history_count': [0],
                            'district': [mapping_dis[district]],
                            'duration': [duration],
                            'gender': [1 if gender == 'Мужчина' else 0],
                            'marital_status': [mapping_mar[marital_status]],
                        })

                        prediction = model.predict_proba(input_data)[:, 0]


                        input_data['Manager'] = manager
                        input_data['district'] = district
                        input_data['name'] = name
                        input_data['region'] = region
                        input_data['phone'] = phone
                        input_data['Result'] = 'Одобрено' if prediction > 1 - 0.15 else 'Отказано'
                        input_data['gender'] = gender
                        input_data['marital_status'] = marital_status
                        input_data['Income'] = 0
                        input_data['Dependants'] = 0
                        input_data['OccupationBranch'] = 0
                        input_data['Occupation'] = 0
                        input_data['ExpCat'] = 0
                        input_data['Probability'] = f'{round(prediction[0]*100, 2)}%'
                        input_data['Date'] = current_date
                        input_data['DocumentNumber'] = document_number
        with top_right:
            def authenticate_gspread():
                # Load Google Sheets API credentials
                from  read_json import  response_json
                response_ = response_json()
                sa = gspread.service_account_from_dict(response_)
                return sa

            # Function to duplicate data to Google Sheets
            def duplicate_to_gsheet(new_row):
                # Authenticate with Google Sheets
                gc = authenticate_gspread()

                # Create a new Google Sheets spreadsheet
                sh = gc.open("MobiCenterRu")

                # Select the first sheet (index 0)
                worksheet = sh.worksheet("Scoring")

                # Check if there's any content in the worksheet
                existing_data = worksheet.get_all_values()

                # Get existing headers if they exist
                headers = existing_data[0] if existing_data else None

                if not headers:
                    headers = ['Менеджер', 'Филиал', 'Телефон номер', 'ФИО', 'Адрес', 'Возраст', 'Пол',
                               'Сумма', 'Период', 'Семейный статус', 'Количество кредитов(история)', 'Доход',
                            'Иждивенцы', 'Сфера занятости', 'Роль', 'Стаж работы',
                               'Результат', 'Вероятность возврата', 'Дата', 'Номер документа']
                    worksheet.append_row(headers)

                # Convert the new_row DataFrame to a list and append it to the worksheet
                new_row = new_row[['Manager','region', 'phone', 'name', 'district', 'age', 'gender', 'amount', 'duration', 'marital_status', "credit_history_count",
                                   'Income','Dependants', 'OccupationBranch', 'Occupation', 'ExpCat',
                                    'Result', 'Probability', 'Date', 'DocumentNumber']]
                new_row_list = new_row.values.tolist()
                worksheet.append_rows(new_row_list)

            # Предсказание
            st.subheader('Результат:')



            if prediction is not None:
                st.write(f'Вероятность возврата: {round(prediction[0]*100, 2)}%')
                if prediction > 1 - 0.15:
                    if_success="Одобрено!"
                    htmlstr1=f"""<p style='background-color:green;
                                                            color:white;
                                                            font-size:35px;
                                                            border-radius:3px;
                                                            line-height:60px;
                                                            padding-left:17px;
                                                            opacity:0.6'>
                                                            {if_success}</style>
                                                            <br></p>"""
                    st.markdown(htmlstr1,unsafe_allow_html=True)
                    # st.success(r'$\textsf{\Large }$')
                    st.balloons()
                    generate_pdf(input_data, document_number, current_date)
                    duplicate_to_gsheet(input_data)
                else:
                    st.error(r'$\textsf{\Large Отказано! 😞}$')
                    generate_pdf(input_data, document_number, current_date)
                    duplicate_to_gsheet(input_data)

                # generate_pdf(input_data, document_number, current_date)
