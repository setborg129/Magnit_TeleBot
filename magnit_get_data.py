import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
import telebot
from config import TOKENS

base_url = 'https://magnit.ru/promo/'
list_cars = []
collect_product = []
collect_product1 = {}
collect_product1['Магнит'] = []


def get_html(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(
        executable_path=r"C:\Users\User129\PycharmProjects\pythonProject\Parsing\Magnit\chromedriver_win32\chromedriver.exe",
        options=options)
    driver.maximize_window()

    try:
        driver.get(url=url)
        time.sleep(3)
        print(driver.current_url)
        while True:
            # Get scroll height
            lenOfPage = driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            match = False
            while (match == False):
                lastCount = lenOfPage
                time.sleep(3)
                lenOfPage = driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                if lastCount == lenOfPage:
                    match = True
                    break
            return driver.page_source
    except Exception as _ex:
        print(_ex)
    finally:
        driver.close()
        driver.quit()


def get_data(text):
    soup = BeautifulSoup(text, 'lxml')
    city = soup.find('a', class_='header__contacts-link_city').text.strip()
    cards = soup.findAll('a', class_='card-sale')
    for num, card in enumerate(cards):
        try:
            card_title = card.find('div', class_='card-sale__title').text.strip()
            card_discont = card.find('div', class_='card-sale__discount').text.strip()
            card_price_old_integer = card.find('div', class_='label__price label__price_old').find('span',
                                                                                                   class_='label__price-integer').text.strip()
            card_price_old_decimal = card.find('div', class_='label__price label__price_old').find('span',
                                                                                                   class_='label__price-decimal').text.strip()
            card_old_price = f'{card_price_old_integer}.{card_price_old_decimal}'

            card_price_new_integer = card.find('div', class_='label__price label__price_new').find('span',
                                                                                                   class_='label__price-integer').text.strip()
            card_price_new_decimal = card.find('div', class_='label__price label__price_new').find('span',
                                                                                                   class_='label__price-decimal').text.strip()
            card_new_price = f'{card_price_new_integer}.{card_price_new_decimal}'
            car_sale_data = card.find('div', class_='card-sale__date').text.strip().replace('\n', ' ')
        except AttributeError:
            continue
        car_econom = float(card_old_price) - float(card_new_price)
        car_econom = round(car_econom, 2)
        car_econom = str(car_econom).replace('.', ',')

        card_title = str(card_title).lower()

        list_cars.append({
            'Наименование': card_title,
            'Процент скидки': card_discont,
            'Старая цена': card_old_price,
            'Новая цена': card_new_price,
            'Дата акции': car_sale_data,
            'Экономия': car_econom
        })
        # собираем json файл.
        with open(f'{city}_{car_sale_data[1]}тест.json', 'w', encoding='utf-8') as file:
            json.dump(list_cars, file, sort_keys=False, indent=4, ensure_ascii=False)


def telegram_bot(token):
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=["start"])
    def start_message(message):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton("👋 Москва")
        markup.add(btn1)
        bot.send_message(message.chat.id,
                         text='Выберите город ! ', reply_markup=markup)

    @bot.message_handler(content_types=['text'])
    def send_text(message):
        print(message.text.lower())
        if message.text.lower() == 'price':
            try:
                bot.send_message(message.chat.id, 'Отправляю тебе данные !')
                bot.send_document(message.chat.id, document=open('./MSK_list1.xlsx', 'rb'))
            except Exception as Ex:
                print(Ex)
                bot.send_message(message.chat.id, 'Что то пошло не так !')
        if message.text.lower() in '👋 москва':
            try:
                bot.send_message(message.chat.id, 'Вы выбрали Москву !')
                bot.send_message(message.chat.id, text='Выберите продукт или его фирму !')


            except Exception as Ex:
                print(Ex)
        else:
            try:
                name_send_info = []
                name_send_info.clear()
                name_send_info = read_file(message.text)

                # Прорабатываем вывод продукции по индексам
                if len(name_send_info) >= 1:
                    ind_prod = 0
                    ind_sale = 1
                    ind_price = 2
                    ind_new_price = 3
                    ind_data = 4
                    ind_ero = 5
                    for item in name_send_info:
                        try:
                            named = f'\n Продукт: {name_send_info[ind_prod]}, \nПроцент скидки: {name_send_info[ind_sale]}, \nСтарая цена: {name_send_info[ind_price]},' \
                                    f' \nНовая цена: {name_send_info[ind_new_price]}, \nДата акции:  {name_send_info[ind_data]}, \nЭкономия:  {name_send_info[ind_ero]} руб.'

                            ind_prod += 6
                            ind_sale += 6
                            ind_price += 6
                            ind_new_price += 6
                            ind_data += 6
                            ind_ero += 6
                            bot.send_message(message.chat.id, named)

                        except IndexError:
                            exit()
                        finally:
                            continue
                elif len(name_send_info) == 0:
                    print('0')
                    bot.send_message(message.chat.id, 'Такого продукта нет ! ')
            except Exception as Ex:
                print(Ex)

    @bot.message_handler(commands=["reset"])
    def cmd_reset(message):
        bot.send_message(message.chat.id, "Что ж, начнём по-новой.")

    bot.polling(none_stop=False)


def read_file(name):
    with open(f'../v2/Москва_тест_lower.json', 'r', encoding='utf-8') as f:
        text = json.load(f)

    for item_text in text:
        if name in item_text['Наименование']:
            collect_product1['Магнит'].append({
                'Наименование': item_text["Наименование"],
                'Процент скидки': item_text["Процент скидки"],
                'Старая цена': item_text["Старая цена"],
                'Новая цена': item_text["Новая цена"],
                'Дата акции': item_text["Дата акции"],
                'Экономия': item_text["Экономия"]
            })

            if name in item_text['Наименование']:
                collect_product.append(item_text["Наименование"])
                collect_product.append(item_text["Процент скидки"])
                collect_product.append(item_text["Старая цена"])
                collect_product.append(item_text["Новая цена"])
                collect_product.append(item_text["Дата акции"])
                collect_product.append(item_text["Экономия"])

    return collect_product


def main():
    telegram_bot(TOKENS)





if __name__ == '__main__':
    main()
