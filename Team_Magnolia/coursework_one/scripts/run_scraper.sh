#!/bin/bash

source /path/to/your/venv/bin/activate

cd “/Users/magicalstarmac/Desktop/BDF_Course/IFTE0003_Big Data in Quantitative Finance 24:25/Group_Work1/ift_coursework_2024/Magnolia/coursework_one/modules/apiift_coursework_2024/Magnolia/coursework_one/modules/scraper”

/usr/bin/python3 csr_scraper.py >> /path/to/ift_coursework_2024/scraper_cron.log 2>&1
