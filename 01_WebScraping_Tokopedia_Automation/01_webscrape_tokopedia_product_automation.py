# Library

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Chrome Profile
chrome_options = webdriver.ChromeOptions()

chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument(f'user-data-dir=C:\\Users\\{os.getlogin()}\\Downloads\\Scraping\\Chrome_Profile\\') # Directory Chrome Profile

driver = webdriver.Chrome(options=chrome_options)

driver.get('https://www.tokopedia.com')

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def search(keyword):
    search_input = driver.find_element(By.CSS_SELECTOR, 'input[data-unify="Search"]')
    search_input.send_keys(Keys.CONTROL + "a")
    search_input.send_keys(Keys.DELETE)
    search_input.send_keys(f'{keyword}')
    search_input.send_keys(Keys.RETURN)

def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            try:
                next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-16uzo3v-unf-pagination-item[aria-label="Laman berikutnya"]'))
                )
                break
            except:
                None
        last_height = new_height

def scrape_data(max_data):
    data = []
    total_page = 1
    total_product = 0

    while True:
        scroll_to_bottom(driver)
        products = driver.find_elements(By.CSS_SELECTOR, 'div[class*="KeRtO-dE1UuZjZ6nmihLZw"]')
        for product in products:
            try:
                try:
                    name = product.find_element(By.CSS_SELECTOR, 'span[class*="OWkG6oHwAppMn1hIBsC3pQ"]').text
                except:
                    name = None
                try:
                    price = product.find_element(By.CSS_SELECTOR, 'div[class*="_8cR53N0JqdRc+mQCckhS0g"]').text
                except:
                    continue
                try:
                    rating = product.find_element(By.CSS_SELECTOR, 'span[class*="nBBbPk9MrELbIUbobepKbQ"]').text
                except:
                    rating = None
                try:
                    sold = product.find_element(By.CSS_SELECTOR, 'span[class*="eLOomHl6J3IWAcdRU8M08A"]').text
                except:
                    sold = None
                try:
                    location = product.find_element(By.CSS_SELECTOR, 'span[class*="-9tiTbQgmU1vCjykywQqvA== flip"]').text
                except:
                    location = None
                try:
                    store = product.find_element(By.CSS_SELECTOR, 'span[class*="X6c-fdwuofj6zGvLKVUaNQ=="]').text
                except:
                    continue
                    
                print(name, price, rating, location,store)
                data.append({
                    'Name': name,
                    'Price': price,
                    'Rating': rating,
                    'Product Sold': sold,
                    'Location': location,
                    'Store': store
                })
                total_product += 1
                if total_product == max_data:
                    break
            except Exception as e:
                # print(f"Error: {e}")
                continue
        
        if total_product >= max_data:
            break

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'button.css-16uzo3v-unf-pagination-item[aria-label="Laman berikutnya"]')
            next_button.click()
            total_page += 1
        except:
            print(f"Maximum Product: {total_product}")
            break
    
    df = pd.DataFrame(data).drop_duplicates()

    return df

while True:
    clear_terminal()
    keyword = input("What are you searching? (Type Done if u already finished your job)\n")

    keyword_lower = keyword.lower()

    if keyword_lower == 'done':
        print("You Are Welcome")
        break
    else:
        search(keyword)
        max_data = input("How many data do u need? (Number Only (Example:100))\n")

        while True:
            try:
                max_data = int(max_data)
                break
            except:
                print("Number Only\n")
                max_data = input("How many data do u need? (Number Only (Example:100))\n")

        
        dataframe = scrape_data(max_data)

        dataframe['Product Sold'] = dataframe['Product Sold'].fillna('0')
        dataframe['sold_est'] = dataframe['Product Sold'].apply(lambda x: 'more than' if pd.notnull(x) and '+' in x else None)
        dataframe['Product Sold'] = (dataframe['Product Sold'].str.replace(' terjual','').str.replace('+','').str.replace('rb','000')).astype(int)

        df_tom_10 = dataframe[(~dataframe['Store'].isna())].head(10)
        df_top_10 = dataframe.sort_values(by=['Product Sold'])
        df_top_10 = df_top_10.tail(10)

        dataframe['Price'] = (dataframe['Price'].str.replace('Rp','').str.replace('.','')).astype(int)
        df_rating_all = dataframe[(~dataframe['Rating'].isna())]

        df_rating_all['Rating'] = df_rating_all['Rating'].astype(float)

        df_rating_all["Rating Group"] = pd.cut(df_rating_all["Rating"],
                                bins=[0, 4, 4.5, 5],
                                labels=["<= 4 star", "4 - 4.5 star", "> 4.5 star"])

        summary = pd.DataFrame([
            {'Name': 'Minimum Price Purchased', 'Value': df_rating_all['Price'].min(), 'Product Name': df_rating_all.loc[df_rating_all['Price'].idxmin(), 'Name']},
            {'Name': 'Maximum Price Purchased', 'Value': df_rating_all['Price'].max(), 'Product Name': df_rating_all.loc[df_rating_all['Price'].idxmax(), 'Name']},
            {'Name': 'Average Price Purchased', 'Value': int(df_rating_all['Price'].mean()), 'Product Name': None},
            {'Name': 'Total Purchased Product', 'Value': df_rating_all['Name'].count(), 'Product Name': None},
            {'Name': 'Minimum Price Listed', 'Value': dataframe['Price'].min(), 'Product Name': dataframe.loc[dataframe['Price'].idxmin(), 'Name']},
            {'Name': 'Maximum Price Listed', 'Value': dataframe['Price'].max(), 'Product Name': dataframe.loc[dataframe['Price'].idxmax(), 'Name']},
            {'Name': 'Average Price Listed', 'Value': int(dataframe['Price'].mean()), 'Product Name': None},
            {'Name': 'Total Listed Product', 'Value': dataframe['Name'].count(), 'Product Name': None},
        ])

        group_summary = pd.DataFrame([
            {'Name': 'Less Than 4 Star', 'Value': df_rating_all[df_rating_all['Rating Group'] == "<= 4 star"]['Name'].count(), 'Product Name': None},
            {'Name': 'Maximum Price (<= 4 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "<= 4 star"]['Price'].max(), 'Product Name': df_rating_all.loc[df_rating_all[df_rating_all['Rating Group'] == "<= 4 star"]['Price'].idxmax(), 'Name']},
            {'Name': 'Minimum Price (<= 4 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "<= 4 star"]['Price'].min(), 'Product Name': df_rating_all.loc[df_rating_all[df_rating_all['Rating Group'] == "<= 4 star"]['Price'].idxmin(), 'Name']},
            {'Name': 'Average Price (<= 4 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "<= 4 star"]['Price'].mean(), 'Product Name': None},
            {'Name': 'Most Sold Product (<= 4 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "<= 4 star"]['Product Sold'].max(), 'Product Name': df_rating_all.loc[df_rating_all[df_rating_all['Rating Group'] == "<= 4 star"]['Product Sold'].idxmax(), 'Name']},
            {'Name': '4 - 4.5 Star', 'Value': df_rating_all[df_rating_all['Rating Group'] == "4 - 4.5 star"]['Name'].count(), 'Product Name': None},
            {'Name': 'Maximum Price (4 - 4.5 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "4 - 4.5 star"]['Price'].max(), 'Product Name': df_rating_all.loc[df_rating_all[df_rating_all['Rating Group'] == "4 - 4.5 star"]['Price'].idxmax(), 'Name']},
            {'Name': 'Minimum Price (4 - 4.5 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "4 - 4.5 star"]['Price'].min(), 'Product Name': df_rating_all.loc[df_rating_all[df_rating_all['Rating Group'] == "4 - 4.5 star"]['Price'].idxmin(), 'Name']},
            {'Name': 'Average Price (4 - 4.5 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "4 - 4.5 star"]['Price'].mean(), 'Product Name': None},
            {'Name': 'Most Sold Product (4 - 4.5 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "4 - 4.5 star"]['Product Sold'].max(), 'Product Name': df_rating_all.loc[df_rating_all[df_rating_all['Rating Group'] == "4 - 4.5 star"]['Product Sold'].idxmax(), 'Name']},
            {'Name': 'More Than 4.5 Star', 'Value': df_rating_all[df_rating_all['Rating Group'] == "> 4.5 star"]['Name'].count(), 'Product Name': None},
            {'Name': 'Maximum Price (> 4.5 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "> 4.5 star"]['Price'].max(), 'Product Name': df_rating_all.loc[df_rating_all[df_rating_all['Rating Group'] == "> 4.5 star"]['Price'].idxmax(), 'Name']},
            {'Name': 'Minimum Price (> 4.5 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "> 4.5 star"]['Price'].min(), 'Product Name': df_rating_all.loc[df_rating_all[df_rating_all['Rating Group'] == "> 4.5 star"]['Price'].idxmin(), 'Name']},
            {'Name': 'Average Price (> 4.5 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "> 4.5 star"]['Price'].mean(), 'Product Name': None},
            {'Name': 'Most Sold Product (> 4.5 Star)', 'Value': df_rating_all[df_rating_all['Rating Group'] == "> 4.5 star"]['Product Sold'].max(), 'Product Name': df_rating_all.loc[df_rating_all[df_rating_all['Rating Group'] == "> 4.5 star"]['Product Sold'].idxmax(), 'Name']},
        ]
        )

        file_name = f'Export File//{keyword}.xlsx'

        # Create ExcelWriter with openpyxl engine
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            dataframe.to_excel(writer,sheet_name='Raw Data',index=False)
            df_tom_10.to_excel(writer, sheet_name='Summary', startrow=1, startcol=0,index=False)
            
            workbook = writer.book
            worksheet = workbook['Summary']
            worksheet.cell(row=1, column=1, value="10 Product Top of Mind")

            worksheet.cell(row=14, column=1, value="Top Selling Product")
            df_top_10.to_excel(writer, sheet_name='Summary', startrow=14, startcol=0,index=False)

            worksheet.cell(row=27, column=1, value="Summary Data")
            summary.to_excel(writer, sheet_name='Summary', startrow=27, startcol=0,index=False)

            worksheet.cell(row=38, column=1, value="Summary Group")
            group_summary.to_excel(writer, sheet_name='Summary', startrow=38, startcol=0,index=False)

            workbook.save(file_name)
