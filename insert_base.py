
from config import login, password, TOKEN, vacancy, channelid
import psycopg2
import pickle
from os.path import isfile
import time
import datetime
from selenium import webdriver
import requests as req

conn = psycopg2.connect(
    host="127.0.0.1",
    port="5432",
    database="bobdb",
    user="bob",
    password="qwerty"
)
cur = conn.cursor()


def Auth():

    url = 'https://ulan-ude.hh.ru/account/login?from=employer_index_header&backurl=%2Femployer'
    driver = webdriver.Firefox(executable_path='./geckodriver')
    driver.get(url)
    add = driver.find_element_by_link_text('Работодателям')
    add.click()
    time.sleep(5)

    input_login = driver.find_element_by_xpath("//input[@placeholder = 'Email']")
    input_login.send_keys(login)
    time.sleep(5)

    input_pass = driver.find_element_by_xpath("//input[@placeholder = 'Пароль']")
    input_pass.send_keys(password)
    time.sleep(5)

    log_in_HH = driver.find_element_by_xpath('//button[@data-qa="account-login-submit"]')
    log_in_HH.click()
    time.sleep(15)
    pickle.dump(driver.get_cookies(), open('cookies_HH', 'wb'))
    print('received')
    driver.close()


def pars_new(data_new_user, user_id_, driver):

    data_new_user.append(user_id_)
    gender = driver.find_element_by_xpath('//span[@data-qa = "resume-personal-gender"]')
    data_new_user.append(gender.text)

    try:
        age = driver.find_element_by_xpath('//span[@data-qa = "resume-personal-age"]')
        data_new_user.append(age.text)
    except:
        data_new_user.append('отсутствует')
    try:
        birthday = driver.find_element_by_xpath('//span[@data-qa = "resume-personal-birthday"]')
        data_new_user.append(birthday.text)
    except:
        data_new_user.append('отсутствует')

    location = driver.find_element_by_xpath('//span[@data-qa = "resume-personal-address"]')
    data_new_user.append(location.text)

    online = driver.find_element_by_xpath(
        '//div[@class = "resume-online-status" or @class="resume-online-status resume-online-status_online"]')
    data_new_user.append(online.text)

    update = driver.find_element_by_xpath('//div[@class = "resume-header-additional__update-date"]')
    data_new_user.append(update.text)
    time.sleep(3)

    print(data_new_user)

    insert_new_data = ('''INSERT INTO users (user_id,gender,age,birthday,location,online,update) 
        VALUES (%s,%s,%s,%s,%s,%s,%s);''')
    cur.execute(insert_new_data, data_new_user)
    conn.commit()
    driver.close()
    driver.switch_to.window(driver.window_handles[0])


def authorization(driver):
    for cookie in pickle.load(open('cookies_HH', 'rb')):
        driver.add_cookie(cookie)
    time.sleep(5)
    driver.refresh()
    time.sleep(10)
    print('log in success')


def search_vacancy(vacancy, driver):
    search = driver.find_element_by_xpath('//span[contains(text(),"Поиск")]')
    search.click()
    time.sleep(2)
    search_by_resume_and_skills = driver.find_element_by_xpath(
        '//input[@placeholder = "Поиск по резюме и навыкам"]')
    search_by_resume_and_skills.send_keys(vacancy)
    time.sleep(5)
    search_button = driver.find_element_by_xpath('//button[contains(text(),"Найти")]')
    search_button.click()
    time.sleep(5)


def send_telegram(line):
    channel_id = channelid
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    resp = req.post(url, data={
        "chat_id": channel_id,
        "text": ' Новая вакансия !' + '\n' +
                  line + '\n' +
                  str(datetime.datetime.now())
             })


def main():
    url = 'https://ulan-ude.hh.ru/account/login?from=employer_index_header&backurl=%2Femployer'
    # options = FirefoxOptions()
    # options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path='./geckodriver')
    driver.get(url)

    cur.execute('''CREATE TABLE IF NOT EXISTS users(
                           user_id    text,
                           gender     text,
                           age        text,
                           birthday   text,
                           location   text,
                           online     text,
                           update     text);''')
    conn.commit()
    print('table')
    authorization(driver)
    search_vacancy(vacancy, driver)

    time.sleep(10)
    search_resume = driver.find_elements_by_class_name("resume-search-item__name")
    data_new_user = []
    for resume_url in search_resume:
        resume_href = resume_url.get_attribute('href')
        line = resume_href.partition('?')[0]
        user_id_ = line.lstrip('https://ulan-ude.hh.ru/resume/')
        cur.execute(f"select * from users where user_id='{user_id_}'")
        data_user = cur.fetchone()
        if data_user is None:
            resume_url.click()
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(8)
            pars_new(data_new_user, user_id_, driver)
            send_telegram(line)
            print('добавлен')
            data_new_user = []
        else:
            print('пользователь есть')
            continue
    print(datetime.datetime.now())


if __name__ == '__main__':
    while True:
        if not isfile('cookies_HH'):
            Auth()
        else:
            print('go')
            pass
        main()
        time.sleep(10)
