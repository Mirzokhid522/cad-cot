import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CAD_URL = "https://market-bulls.com/cot-report-canadian-dollar-cad/"
DATA_FILE = "market_data.json"

def harvest_cad():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    # Load existing master_data so we keep other currency records intact
    master_data = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                master_data = json.load(f)
            except json.JSONDecodeError:
                master_data = {}

    print("Opening browser for CAD...")
    try:
        driver.set_page_load_timeout(40)
        driver.get(CAD_URL)
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(2)

        print("Extracting candlestick chart data for CAD...")
        extracted_data = driver.execute_script("""
            let chartInstance = null;
            if (typeof price_chart !== 'undefined') chartInstance = price_chart;
            else if (typeof chart !== 'undefined') chartInstance = chart;
            else {
                for (let key in window) {
                    try {
                        if (window[key] && window[key].data && window[key].data.datasets) {
                            chartInstance = window[key];
                            break;
                        }
                    } catch (e) {}
                }
            }

            if (!chartInstance || !chartInstance.data || !chartInstance.data.datasets[0]) {
                return [];
            }

            const dataset = chartInstance.data.datasets[0].data;
            return dataset.map((item, index) => {
                let dateStr = item.x ? new Date(item.x).toLocaleDateString([], { year: "2-digit", month: "short", day: "2-digit" }) : `Index ${index}`;
                let open = item.o !== undefined ? item.o : item.open;
                let high = item.h !== undefined ? item.h : item.high;
                let low = item.l !== undefined ? item.l : item.low;
                let close = item.c !== undefined ? item.c : item.close;
                let isCyan = close >= open;

                return {
                    index: index,
                    date: dateStr,
                    open: open,
                    high: high,
                    low: low,
                    close: close,
                    color: isCyan ? "Cyan" : "Purple"
                };
            });
        """)
        
        if extracted_data and len(extracted_data) > 0:
            master_data["CAD"] = extracted_data
            print(f"Successfully captured {len(extracted_data)} rows for CAD!")
        else:
            master_data["CAD"] = []
            print("Warning: No chart dataset found for CAD. Stored empty data array.")
            
    except Exception as e:
        print(f"Error harvesting CAD: {e}")
        master_data["CAD"] = []

    driver.quit()

    with open(DATA_FILE, "w") as f:
        json.dump(master_data, f, indent=4)
    print("\nCAD Harvest finished! Data saved to market_data.json")

if __name__ == "__main__":
    harvest_cad()