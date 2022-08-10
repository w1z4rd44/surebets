import datetime
from datetime import timedelta
import difflib
import requests
import re
import pandas as pd
import numpy as np
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from bs4 import BeautifulSoup as soup

zi1 = datetime.datetime.now()
zi2 = datetime.datetime.now() + timedelta(days=1)
zi3 = datetime.datetime.now() + timedelta(days=2)
zile = [zi1,zi2]
sporturi = ['fotbal','tenis']
miza = 1000
sb = pd.DataFrame()

options = Options()
options.headless = True 

def scroll_to_bottom(driver):
    old_position = 0
    new_position = None
    while new_position != old_position:
        # Get old scroll position
        old_position = driver.execute_script(
                ("return (window.pageYOffset !== undefined) ?"
                 " window.pageYOffset : (document.documentElement ||"
                 " document.body.parentNode || document.body);"))
        # Sleep and Scroll
        time.sleep(2)
        driver.execute_script((
                "var scrollingElement = (document.scrollingElement ||"
                " document.body);scrollingElement.scrollTop ="
                " scrollingElement.scrollHeight;"))
        # Get new position
        new_position = driver.execute_script(
                ("return (window.pageYOffset !== undefined) ?"
                 " window.pageYOffset : (document.documentElement ||"
                 " document.body.parentNode || document.body);"))
        if (new_position - old_position) < 2:
            break

counter = 0
while True:

    # Get matches and odds from Fortuna

    df1 = pd.DataFrame()

    for zi in zile:
        zi_ro = str('{:02d}'.format(zi.day)) + "-" + str('{:02d}'.format(zi.month)) + "-" + str(zi.year)  

        for sport in sporturi:
            url = 'https://efortuna.ro/pariuri-online/'+ sport +'?selectDates=1&date=' + str(zi.year) + "-" + str('{:02d}'.format(zi.month)) + "-" + str('{:02d}'.format(zi.day))
            driver = webdriver.Chrome(options=options)
            try:
                driver.get(url)
            except:
                continue
                print("Nu exista meciuri de " + sport + "in data de " + str(zi.year) + "-" + str('{:02d}'.format(zi.month)) + "-" + str('{:02d}'.format(zi.day)))

            scroll_to_bottom(driver)
            time.sleep(3)
            source_code = driver.page_source
            page_soup1 = soup(source_code, "html.parser")
            sections = page_soup1.findAll("section")
            lista_competitii=[]
            lista_meciuri = []
            lista_meciuri_final = []
            lista_cote = []
            tabele_bune = []
            grupuri_cote = []
            grupuri_evenimente = []
            for section in sections:
                if section.get("data-competition-name") == None:
                    continue
                elif section.get("data-competition-name").endswith(("castigator","castigator play off","golgheter","golgheter-sezon regulat","duel","clasare","clasare finala","clasare finala 1-6","clasa in","(dupa runda 30)","cea mai buna aparare","cel mai bun atac","va marca")):
                    continue
                else:
                    lista_competitii.append(section.get("data-competition-name"))
            sectiuni_bune = page_soup1.findAll("section", {"data-competition-name":lista_competitii}) 
            for sectiune_buna in sectiuni_bune:
                if "running-live tablesorter-hasChildRow" in sectiune_buna:
                    continue
                else:
                    tabele_bune.append(sectiune_buna.findAll("div", {"class" : "events-table-box events-table-box--main-market"}))
            for tabel_bun in tabele_bune:
                for row in tabel_bun:
                    grupuri_cote.append(row.findAll("span",{"class":"odds-value"}))
                    grupuri_evenimente.append(row.findAll("span",{"class":["market-name","event-name"]}))
            for grup_cote in grupuri_cote:
                for cota in grup_cote:
                    if cota.text.strip() == "":
                        lista_cote.append(float(cota.text.strip().replace("","1.00")))
                    else:
                        lista_cote.append(float(cota.text.strip()))
            for grup_evenimente in grupuri_evenimente:
                for eveniment in grup_evenimente:
                    lista_meciuri.append(eveniment.text.strip())
            lista_meciuri_final = (list(dict.fromkeys(lista_meciuri)))
            dict = {}
            if sport =='fotbal':
                dict.update({"Zi": zi_ro, "Sport" : sport, "Meci" : lista_meciuri_final, "1" : lista_cote[::6], "X": lista_cote[1:len(lista_cote):6], "2": lista_cote[2:len(lista_cote):6]})
            else:
                dict.update({"Zi": zi_ro, "Sport" : sport, "Meci" : lista_meciuri_final, "1" : lista_cote[::2], "X": 0, "2": lista_cote[1:len(lista_cote):2]})       
            df_categ = pd.DataFrame(data=dict)
            df1 = pd.concat([df1,df_categ]).reset_index(drop=True)
            driver.quit()

    # Get matches and odds from GetsBet

    df2 = pd.DataFrame()

    for zi in zile:
        zi_ro = str('{:02d}'.format(zi.day)) + "-" + str('{:02d}'.format(zi.month)) + "-" + str(zi.year)  
        for sport in sporturi:
            if sport == 'fotbal':
                url2 = 'https://sports2.getsbet.ro/ro/sport/fotbal/1/toate/0/locatie'
            elif sport == 'tenis':
                url2 = 'https://sports2.getsbet.ro/ro/sport/tenis/3/toate/0/categorie'
            elif sport == 'tenis-de-masa':
                url2 = 'https://sports2.getsbet.ro/ro/sport/tenis-de-masă/63/toate/0/locatie'
            elif sport == 'darts':
                url2 = 'https://sports2.getsbet.ro/ro/sport/darts/45/toate/0/locatie'
            elif sport == 'snooker':
                url2 = 'https://sports2.getsbet.ro/ro/sport/snooker/36/toate/0/locatie'
            driver = webdriver.Chrome(options=options)
            driver.get(url2)
            driver.maximize_window()
            wait = WebDriverWait(driver, 4)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[ text() = "Următoarele 7 zile" ]'))).click()
            wait = WebDriverWait(driver, 4)
            if zi == zi1:
                xpath_zi = '//*[@id="MainContainer"]/div/section/div[2]/div[2]/div[1]/div/div[1]/div/div/div[1]/span/span'
            elif zi == zi2:
                xpath_zi = '//*[@id="MainContainer"]/div/section/div[2]/div[2]/div[1]/div/div[1]/div/div/div[2]/span/span'
            elif zi == zi3:
                xpath_zi = '//*[@id="MainContainer"]/div/section/div[2]/div[2]/div[1]/div/div[1]/div/div/div[3]/span/span'
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath_zi))).click()
            try:
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[ text() = "Mai mult" ]'))).click()
                    time.sleep(1)
            except (NoSuchElementException, StaleElementReferenceException, TimeoutException):
                time.sleep(2)
                source_code = driver.page_source
                page_soup2 = soup(source_code, "html.parser")
                lista_participanti = []
                lista_meciuri = []
                lista_cote = []
                participanti = page_soup2.findAll("span",{"class" : "Details__ParticipantName"})
                cote = page_soup2.findAll("span",{"class" : ["OddsButton__Odds","OM-Icon OM-Icon--Svg OM-Icon--general OM-Icon--lock OM-Icon--Small2"]})
                for participant in participanti:
                    lista_participanti.append(participant.text.strip())
                x=0
                for x in range(0,len(lista_participanti)):
                    if x%2==0:
                        meci = lista_participanti[x] + " - " + lista_participanti[x+1]
                        lista_meciuri.append(meci.replace("U23","Under23").replace("U20","Under20"))
                    else:
                        continue
                    x=x+1
                for cota in cote:
                    if cota.text.strip() == "":
                        lista_cote.append(float(cota.text.strip().replace("","1.00")))
                    else:
                        lista_cote.append(float(cota.text.strip()))
                dict = {}
                if sport =='fotbal':
                    dict.update({"Zi": zi_ro, "Sport" : sport, "Meci" : lista_meciuri, "1" : lista_cote[::3], "X": lista_cote[1:len(lista_cote):3], "2": lista_cote[2:len(lista_cote):3]})
                else:
                    dict.update({"Zi": zi_ro, "Sport" : sport, "Meci" : lista_meciuri, "1" : lista_cote[::2], "X": 0, "2": lista_cote[1:len(lista_cote):2]})       
                df_categ = pd.DataFrame(data=dict)
                df2 = pd.concat([df2,df_categ]).reset_index(drop=True)
            driver.quit()

    df_join = df2.copy()
    df_join["Meci_match"]=df_join["Meci"]
    df_join["Meci"] = df_join["Meci"].apply(lambda x: (difflib.get_close_matches(x, df1["Meci"], cutoff=0.80)[:1] or [None])[0])

    df = pd.merge(df_join, df1, how="left", on="Meci")
    df = df.replace(to_replace='None', value=np.nan).dropna()
    df['Profit(%)'] = np.where(df['Sport_x'] == 'fotbal', round(100*((1/((1/df[["1_x", "1_y"]].max(axis=1))+(1/df[["X_x", "X_y"]].max(axis=1))+(1/df[["2_x", "2_y"]].max(axis=1))))-1),2), round(100*((1/((1/df[["1_x", "1_y"]].max(axis=1))+(1/df[["2_x", "2_y"]].max(axis=1))))-1),2))
    df = df.sort_values(by=["Profit(%)"], ascending=False).reset_index(drop=True)

    df['Miza pe 1'] = round(miza / df[["1_x", "1_y"]].max(axis=1) + df['Profit(%)']/100*(miza / df[["1_x", "1_y"]].max(axis=1)),2)
    df['Miza pe X'] = np.where(df['Sport_x'] =='fotbal', round(miza / df[["X_x", "X_y"]].max(axis=1) + df['Profit(%)']/100*(miza / df[["X_x", "X_y"]].max(axis=1)),2),0)
    df['Miza pe 2'] = round(miza / df[["2_x", "2_y"]].max(axis=1) + df['Profit(%)']/100*(miza / df[["2_x", "2_y"]].max(axis=1)),2)
    df['Castig 1'] = round(df['Miza pe 1']*df[["1_x", "1_y"]].max(axis=1),2)
    df['Castig X'] = np.where(df['Sport_x'] =='fotbal', round(df['Miza pe X']*df[["X_x", "X_y"]].max(axis=1),2),0)
    df['Castig 2'] = round(df['Miza pe 2']*df[["2_x", "2_y"]].max(axis=1),2)
    df.to_excel("Date_extrase.xlsx")
    
    sb_rows = df.loc[df['Profit(%)'] > 0]
    if counter == 0:
        sb = pd.concat([sb,sb_rows]).reset_index(drop=True)
    else:
        new_rows = sb_rows[~sb_rows['Meci'].isin(sb['Meci'])]
        sb = pd.concat([sb,new_rows]).reset_index(drop=True)
    sb.to_excel("Surebets.xlsx")
    print(sb)
    counter = counter + 1
    time.sleep(300)
