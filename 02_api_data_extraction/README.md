## 02_api_data_extraction

### Project Description

This project focuses on extracting data from Tokopedia's API to obtain detailed product information. The data is retrieved directly from the API and includes product details such as sales per item, price, discounted price, rating, and more. The data is requested from the API obtained from the network.

### Features

- **Scraping Metrics:**
  - Product name
  - Product ID
  - Price
  - Image Link
  - Discount Percentage
  - Price after Discount
  - Campaign Start
  - Review Count
  - Rating Count
  - Average Rating
  - Product Created Date
  - Stock
  - Weight 
  - Condition
  - Category
  - etc

- **Input Parameters:**
  - The only required input parameter is the store "ID," which can be obtained from the store link.

  Example:
  For the store link tokopedia.com/happyfolkss, the store ID is happyfolkss.

- **Output:**
  The output is an Excel file with two sheets:
  - Product List
  - Product Detail

### How It Works

1. **Input Search Criteria:**
   - Provide the store ID you want to extract for.

2. **Data Extraction:**
   - The script will open Tokopedia Store for the given store ID.
   - It gathers important metrics.

3. **Output:**
   - The results are saved in an Excel file, ready for analysis.
