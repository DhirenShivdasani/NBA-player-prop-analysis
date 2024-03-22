from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


chrome_options = uc.ChromeOptions()
chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
chrome_options.add_argument("--disable-notifications")
chrome_options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.geolocation": 1, # 1:Allow, 2:Block
})

chrome_options.page_load_strategy = 'eager'  # Waits for the DOMContentLoaded event


driver = uc.Chrome(options=chrome_options)


driver.get("https://app.prizepicks.com/")
# time.sleep(5)

wait = WebDriverWait(driver, timeout = 10)  # Wait for up to 10 seconds
try:
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div[3]/div/div/button')))
    element.click()
except Exception as e:
    print(f"Error: {e}")


ppPlayers = []


wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
try:
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='name'][normalize-space()='NBA']")))
    element.click()
except Exception as e:
    print(f"Error: {e}")

time.sleep(4)


stat_container = WebDriverWait(driver, 15).until(
    EC.visibility_of_element_located((By.CLASS_NAME, "stat-container"))
)

categories = driver.find_element(By.CSS_SELECTOR, ".stat-container").text.split('\n')

for category in categories:
    driver.find_element(By.XPATH, f"//div[text()='{category}']").click()


    # projectionsPP = WebDriverWait(driver, 2).until(
    #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, "/html/body/div[1]/div/div[3]/div[1]/div/main/div/div[2]")))
    # print(projectionsPP)

    WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, "#projections > ul"))
)

    # Find all prop items under the specified container
    projectionsPP = driver.find_elements(By.CSS_SELECTOR, "#projections > ul > li")

    for projections in projectionsPP:

        goblin_icon = projections.find_elements(By.XPATH, ".//button[@aria-label='Open modal for Demons and Goblins']")
        
        # If the goblin icon is present, skip this prop
        if goblin_icon:
            continue
        

        names = projections.find_element(By.ID, "test-player-name").text
        team = projections.find_element(By.ID, 'test-team-position').text
        value = projections.find_element(By.CSS_SELECTOR, '.flex.flex-1.items-center.pr-2').text.strip()
        proptype = projections.find_element(By.CSS_SELECTOR, 'div.align-items-center > div.text-soClean-140').text.strip()
        print(proptype)
        
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