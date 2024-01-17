from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc

import time
import pandas as pd

############################################################################

driver = uc.Chrome()

###########################################################################


driver.get("https://app.prizepicks.com/")
time.sleep(3)

# WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "close")))
time.sleep(10)
# driver.find_element(By.XPATH, "/html/body/div[2]/div[3]/div/div/div[3]/button").click()
# /html/body/div[1]/div/div[3]/div[1]/div/main/div/nav/div/div[2]
ppPlayers = []

# CHANGE MLB TO ANY SPORT THAT YOU LIKE!!!!! IF THE SPORT IS NOT OFFERED ON PP THEN THE PROGRAM WILL RUN AN ERROR AND EXIT.
driver.find_element(By.XPATH, "//div[@class='name'][normalize-space()='NBA']").click()
time.sleep(5)

stat_container = WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.CLASS_NAME, "stat-container")))

categories = driver.find_element(By.CSS_SELECTOR, ".stat-container").text.split('\n')

for category in categories:
    driver.find_element(By.XPATH, f"//div[text()='{category}']").click()

    projectionsPP = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".projection")))

    for projections in projectionsPP:
        names = projections.find_element(By.CLASS_NAME, "name").text
        team = projections.find_element(By.CLASS_NAME, 'team-position').text
        value = projections.find_element(By.CLASS_NAME, "presale-score").get_attribute('innerHTML')
        proptype = projections.find_element(By.CLASS_NAME, "text").get_attribute('innerHTML')

        
        players = {
            'Name': names,
            'Team': team,
            'Value': value,
            'Prop': proptype.replace("<wbr>", "")
        }
        ppPlayers.append(players)

dfProps = pd.DataFrame(ppPlayers)
# CHANGE THE NAME OF THE FILE TO YOUR LIKING
dfProps.to_csv('test2.csv')

print("These are all of the props offered by PP.", '\n')
print(dfProps)
print('\n')