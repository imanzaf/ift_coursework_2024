# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 20:57:12 2025

@author: Seven
"""

import os
import re
import time
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def match_score(text, search_term):
    text_words = set(text.lower().split())
    term_words = set(search_term.lower().split())
    return sum(1 for word in term_words if word in text_words)

def search_click_download_report(search_term):
    raw_search_term = search_term.strip()
    driver = webdriver.Chrome()
    report_folder = "report"
    if not os.path.exists(report_folder):
        os.makedirs(report_folder)
    return_data = (raw_search_term, "none", "none")
    try:
        wait = WebDriverWait(driver, 10)
        driver.get("https://www.responsibilityreports.com/")
        search_box = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[name='search'][placeholder='Company Name or Ticker Symbol']")
            )
        )
        search_box.click()
        search_box.clear()
        search_box.send_keys(raw_search_term)
        search_box.send_keys(Keys.ENTER)
        time.sleep(2)
        all_links = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
        count = len(all_links)
        print(f"Number of <a> tags obtained using the original search term '{raw_search_term}': {count}")
        if count == 21:
            modified_search_term = clean_company_name(raw_search_term)
            print(f"Original search term returned 21 <a> tags, re-searching using normalized search term '{modified_search_term}'")
            while True:
                driver.get("https://www.responsibilityreports.com/")
                search_box = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "input[name='search'][placeholder='Company Name or Ticker Symbol']")
                    )
                )
                search_box.click()
                search_box.clear()
                search_box.send_keys(modified_search_term)
                search_box.send_keys(Keys.ENTER)
                time.sleep(2)
                all_links = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                count = len(all_links)
                print(f"Number of <a> tags obtained using the normalized search term '{modified_search_term}': {count}")
                if count == 21:
                    if " " in modified_search_term:
                        modified_search_term = modified_search_term.rsplit(" ", 1)[0]
                        print(f"Still 21 <a> tags, shortening search term to: '{modified_search_term}'")
                        continue
                    else:
                        print("Search term shortened to the minimum but still returns 21 <a> tags, returning none.")
                        driver.quit()
                        return (raw_search_term, "none", "none")
                else:
                    break
        else:
            modified_search_term = raw_search_term
        if count == 22:
            selected_link = all_links[10]
        elif count > 22:
            candidate_links = all_links[10 : count - 12 + 1]
            best_score = -1
            selected_link = None
            for link in candidate_links:
                text = link.text.strip()
                score = match_score(text, modified_search_term)
                if score > best_score:
                    best_score = score
                    selected_link = link
            if selected_link is None:
                selected_link = candidate_links[0]
        else:
            print("Not enough <a> tags on the page, cannot proceed.")
            driver.quit()
            return (raw_search_term, "none", "none")
        selected_link.click()
        time.sleep(2)
        try:
            report_link_element = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_form_10k"))
            )
        except TimeoutException:
            print("Link with class 'btn_form_10k' not found, returning none")
            driver.quit()
            return (modified_search_term, "none", "none")
        report_url = report_link_element.get_attribute("href")
        print(f"Report URL: {report_url}")
        aria_label = report_link_element.get_attribute("aria-label") or ""
        match_year = re.search(r"(20\d{2})", aria_label)
        if not match_year:
            link_text = report_link_element.text or ""
            match_year = re.search(r"(20\d{2})", link_text)
        if not match_year:
            href = report_link_element.get_attribute("href") or ""
            match_year = re.search(r"(20\d{2})", href)
        if match_year:
            report_year = match_year.group(1)
        else:
            report_year = "none"
        safe_company_name = re.sub(r"[^\w\-]+", "_", modified_search_term)
        if report_year != "none":
            output_file = f"{safe_company_name}_{report_year}.pdf"
        else:
            output_file = f"{safe_company_name}.pdf"
        output_path = os.path.join(report_folder, output_file)
        selenium_cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        response = requests.get(report_url, cookies=cookies_dict, stream=True)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Report downloaded successfully and saved to: {output_path}")
        else:
            print(f"Report download failed, HTTP status code: {response.status_code}")
            report_url = "none"
            report_year = "none"
        return_data = (modified_search_term, report_url, report_year)
    except Exception as e:
        print("Exception occurred: ", e)
    finally:
        time.sleep(5)
        driver.quit()
    return return_data

def clean_company_name(name):
    cleaned = re.sub(r'[^\w]', ' ', name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

if __name__ == "__main__":
    df = pd.read_excel("test.xlsx", engine="openpyxl")
    records = []
    for raw_name in df["security"]:
        print(f"Processing company: {raw_name}")
        result = search_click_download_report(raw_name)
        records.append(result)
    df_out = pd.DataFrame(records, columns=["Company Name", "Report Link", "Report Year"])
    df_out.to_excel("report_info.xlsx", index=False)
    print("report_info.xlsx file has been generated.")
