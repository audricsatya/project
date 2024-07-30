from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import requests
import json

chrome_options = webdriver.ChromeOptions()

chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument(f'user-data-dir=C:\\Users\\{os.getlogin()}\\Downloads\\Scraping\\Chrome_Profile\\')

driver = webdriver.Chrome(options=chrome_options)

def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            try:
                next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.css-14ulvr4[data-testid="btnShopProductPageNext"]'))
                )
                break
            except:
                None
        last_height = new_height

while True:
    shop_name = input("Store ID: ")

    driver.get(f'https://www.tokopedia.com/{shop_name}')
    scroll_to_bottom(driver)

    headers = {
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'X-Version': '4c288b3',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'content-type': 'application/json',
        'accept': '*/*',
        'Referer': 'https://www.tokopedia.com/samsungelectronicsstores?source=universe&st=product',
        'X-Source': 'tokopedia-lite',
        'X-Tkpd-Lite-Service': 'zeus',
        'sec-ch-ua-platform': '"Windows"',
    }

    json_data = [
        {
            'operationName': 'ShopInfoCore',
            'variables': {
                'id': 0,
                'domain': f'{shop_name}',
            },
            'query': 'query ShopInfoCore($id: Int!, $domain: String) {\n  shopInfoByID(input: {shopIDs: [$id], fields: ["active_product", "allow_manage_all", "assets", "core", "closed_info", "create_info", "favorite", "location", "status", "is_open", "other-goldos", "shipment", "shopstats", "shop-snippet", "other-shiploc", "shopHomeType", "branch-link", "goapotik", "fs_type"], domain: $domain, source: "shoppage"}) {\n    result {\n      shopCore {\n        description\n        domain\n        shopID\n        name\n        tagLine\n        defaultSort\n        __typename\n      }\n      createInfo {\n        openSince\n        __typename\n      }\n      favoriteData {\n        totalFavorite\n        alreadyFavorited\n        __typename\n      }\n      activeProduct\n      shopAssets {\n        avatar\n        cover\n        __typename\n      }\n      location\n      isAllowManage\n      branchLinkDomain\n      isOpen\n      shipmentInfo {\n        isAvailable\n        image\n        name\n        product {\n          isAvailable\n          productName\n          uiHidden\n          __typename\n        }\n        __typename\n      }\n      shippingLoc {\n        districtName\n        cityName\n        __typename\n      }\n      shopStats {\n        productSold\n        totalTxSuccess\n        totalShowcase\n        __typename\n      }\n      statusInfo {\n        shopStatus\n        statusMessage\n        statusTitle\n        tickerType\n        __typename\n      }\n      closedInfo {\n        closedNote\n        until\n        reason\n        detail {\n          status\n          __typename\n        }\n        __typename\n      }\n      bbInfo {\n        bbName\n        bbDesc\n        bbNameEN\n        bbDescEN\n        __typename\n      }\n      goldOS {\n        isGold\n        isGoldBadge\n        isOfficial\n        badge\n        shopTier\n        __typename\n      }\n      shopSnippetURL\n      customSEO {\n        title\n        description\n        bottomContent\n        __typename\n      }\n      isQA\n      isGoApotik\n      partnerInfo {\n        fsType\n        __typename\n      }\n      __typename\n    }\n    error {\n      message\n      __typename\n    }\n    __typename\n  }\n}\n',
        },
    ]

    response = requests.post('https://gql.tokopedia.com/graphql/ShopInfoCore', headers=headers, json=json_data)
    parsed = json.loads(response.text)
    shop_id = parsed[0]['data']['shopInfoByID']['result'][0]['shopCore']['shopID']
    number_product = 1
    max_product = 200

    flattened_data_list = []

    while True:
        headers = {
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'X-Version': '4c288b3',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'content-type': 'application/json',
            'accept': '*/*',
            'Referer': 'https://www.tokopedia.com/samsungelectronicsstores?source=universe&st=product',
            'X-Source': 'tokopedia-lite',
            'X-Device': 'default_v3',
            'X-Tkpd-Lite-Service': 'zeus',
            'sec-ch-ua-platform': '"Windows"',
        }

        json_data = [
            {
                'operationName': 'ShopProducts',
                'variables': {
                    'source': 'shop',
                    'sid': f'{shop_id}',
                    'page': number_product,
                    'perPage': max_product,
                    'etalaseId': 'etalase',
                    'sort': 1,
                    'user_districtId': '2274',
                    'user_cityId': '176',
                    'user_lat': '0',
                    'user_long': '0',
                },
                'query': 'query ShopProducts($sid: String!, $source: String, $page: Int, $perPage: Int, $keyword: String, $etalaseId: String, $sort: Int, $user_districtId: String, $user_cityId: String, $user_lat: String, $user_long: String) {\n  GetShopProduct(shopID: $sid, source: $source, filter: {page: $page, perPage: $perPage, fkeyword: $keyword, fmenu: $etalaseId, sort: $sort, user_districtId: $user_districtId, user_cityId: $user_cityId, user_lat: $user_lat, user_long: $user_long}) {\n    status\n    errors\n    links {\n      prev\n      next\n      __typename\n    }\n    data {\n      name\n      product_url\n      product_id\n      price {\n        text_idr\n        __typename\n      }\n      primary_image {\n        original\n        thumbnail\n        resize300\n        __typename\n      }\n      flags {\n        isSold\n        isPreorder\n        isWholesale\n        isWishlist\n        __typename\n      }\n      campaign {\n        discounted_percentage\n        original_price_fmt\n        start_date\n        end_date\n        __typename\n      }\n      label {\n        color_hex\n        content\n        __typename\n      }\n      label_groups {\n        position\n        title\n        type\n        url\n        __typename\n      }\n      badge {\n        title\n        image_url\n        __typename\n      }\n      stats {\n        reviewCount\n        rating\n        averageRating\n        __typename\n      }\n      category {\n        id\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n',
            },
        ]

        response = requests.post('https://gql.tokopedia.com/graphql/ShopProducts', headers=headers, json=json_data)
        parsed = response.json()

        for data in parsed[0]['data']['GetShopProduct']['data']:
            flattened_data = {
                'name': data['name'],
                'product_url': data['product_url'],
                'product_id': data['product_id'],
                'product_key': data['product_url'].split('/')[4].split('?')[0],
                'price': data['price']['text_idr'],
                'primary_image_original': data['primary_image']['original'],
                'primary_image_thumbnail': data['primary_image']['thumbnail'],
                'primary_image_resize300': data['primary_image']['resize300'],
                'is_sold': data['flags']['isSold'],
                'is_preorder': data['flags']['isPreorder'],
                'is_wholesale': data['flags']['isWholesale'],
                'is_wishlist': data['flags']['isWishlist'],
                'campaign_discount_percentage': data['campaign']['discounted_percentage'],
                'campaign_original_price': data['campaign']['original_price_fmt'],
                'campaign_start_date': data['campaign']['start_date'],
                'campaign_end_date': data['campaign']['end_date'],
                'badge_title': data['badge'][0]['title'] if data['badge'] else None,
                'badge_image_url': data['badge'][0]['image_url'] if data['badge'] else None,
                'review_count': data['stats']['reviewCount'],
                'rating': data['stats']['rating'],
                'average_rating': data['stats']['averageRating'],
            }

            flattened_data_list.append(flattened_data)
        
        if parsed[0]['data']['GetShopProduct']['links']['next'] == "":
            break
        else:
            number_product += 200
            max_product += 200 

    product_data = pd.DataFrame(flattened_data_list)

    flattened_data_list = []

    for i in range (0,product_data.count().max()):
        print(f'{product_data['product_key'][i]}')
        
        headers = {
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'X-Version': '4c288b3',
            'X-TKPD-AKAMAI': 'pdpGetLayout',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'content-type': 'application/json',
            'accept': '*/*',
            'Referer': f'{product_data['product_url'][i]}',
            'X-Source': 'tokopedia-lite',
            'x-device': 'desktop',
            'X-Tkpd-Lite-Service': 'zeus',
            'sec-ch-ua-platform': '"Windows"',
        }

        json_data = [
            {
                'operationName': 'PDPGetLayoutQuery',
                'variables': {
                    'shopDomain': f'{shop_name}',
                    'productKey': f'{product_data['product_key'][i]}',
                    'layoutID': '',
                    'apiVersion': 1,
                    'tokonow': {
                        'shopID': '0',
                        'whID': '0',
                        'serviceType': '',
                    },
                    'deviceID': 'NTBlYzUzMzY5M2NhZDUzNGQwMDM1ZDFiY2RmYTY4Y2Q3NmZmOTUxMzBmNDlhNGRmYjI0ZjAyODZlZmNmOTRmNDlkZDBkNzI3YTZkNDU3NGM0NzU1OWMwZjhjZTA2ZTBm47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=',
                    'userLocation': {
                        'cityID': '176',
                        'addressID': '0',
                        'districtID': '2274',
                        'postalCode': '',
                        'latlon': '',
                    },
                    'extParam': 'src%3Dshop%26whid%3D2884264',
                },
                'query': 'fragment ProductVariant on pdpDataProductVariant {\n  errorCode\n  parentID\n  defaultChild\n  sizeChart\n  totalStockFmt\n  variants {\n    productVariantID\n    variantID\n    name\n    identifier\n    option {\n      picture {\n        urlOriginal: url\n        urlThumbnail: url100\n        __typename\n      }\n      productVariantOptionID\n      variantUnitValueID\n      value\n      hex\n      stock\n      __typename\n    }\n    __typename\n  }\n  children {\n    productID\n    price\n    priceFmt\n    slashPriceFmt\n    discPercentage\n    optionID\n    optionName\n    productName\n    productURL\n    picture {\n      urlOriginal: url\n      urlThumbnail: url100\n      __typename\n    }\n    stock {\n      stock\n      isBuyable\n      stockWordingHTML\n      minimumOrder\n      maximumOrder\n      __typename\n    }\n    isCOD\n    isWishlist\n    campaignInfo {\n      campaignID\n      campaignType\n      campaignTypeName\n      campaignIdentifier\n      background\n      discountPercentage\n      originalPrice\n      discountPrice\n      stock\n      stockSoldPercentage\n      startDate\n      endDate\n      endDateUnix\n      appLinks\n      isAppsOnly\n      isActive\n      hideGimmick\n      isCheckImei\n      minOrder\n      __typename\n    }\n    thematicCampaign {\n      additionalInfo\n      background\n      campaignName\n      icon\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ProductMedia on pdpDataProductMedia {\n  media {\n    type\n    urlOriginal: URLOriginal\n    urlThumbnail: URLThumbnail\n    urlMaxRes: URLMaxRes\n    videoUrl: videoURLAndroid\n    prefix\n    suffix\n    description\n    variantOptionID\n    __typename\n  }\n  videos {\n    source\n    url\n    __typename\n  }\n  __typename\n}\n\nfragment ProductCategoryCarousel on pdpDataCategoryCarousel {\n  linkText\n  titleCarousel\n  applink\n  list {\n    categoryID\n    icon\n    title\n    isApplink\n    applink\n    __typename\n  }\n  __typename\n}\n\nfragment ProductHighlight on pdpDataProductContent {\n  name\n  price {\n    value\n    currency\n    priceFmt\n    slashPriceFmt\n    discPercentage\n    __typename\n  }\n  campaign {\n    campaignID\n    campaignType\n    campaignTypeName\n    campaignIdentifier\n    background\n    percentageAmount\n    originalPrice\n    discountedPrice\n    originalStock\n    stock\n    stockSoldPercentage\n    threshold\n    startDate\n    endDate\n    endDateUnix\n    appLinks\n    isAppsOnly\n    isActive\n    hideGimmick\n    __typename\n  }\n  thematicCampaign {\n    additionalInfo\n    background\n    campaignName\n    icon\n    __typename\n  }\n  stock {\n    useStock\n    value\n    stockWording\n    __typename\n  }\n  variant {\n    isVariant\n    parentID\n    __typename\n  }\n  wholesale {\n    minQty\n    price {\n      value\n      currency\n      __typename\n    }\n    __typename\n  }\n  isCashback {\n    percentage\n    __typename\n  }\n  isTradeIn\n  isOS\n  isPowerMerchant\n  isWishlist\n  isCOD\n  preorder {\n    duration\n    timeUnit\n    isActive\n    preorderInDays\n    __typename\n  }\n  __typename\n}\n\nfragment ProductCustomInfo on pdpDataCustomInfo {\n  icon\n  title\n  isApplink\n  applink\n  separator\n  description\n  __typename\n}\n\nfragment ProductInfo on pdpDataProductInfo {\n  row\n  content {\n    title\n    subtitle\n    applink\n    __typename\n  }\n  __typename\n}\n\nfragment ProductDetail on pdpDataProductDetail {\n  content {\n    title\n    subtitle\n    applink\n    showAtFront\n    isAnnotation\n    __typename\n  }\n  __typename\n}\n\nfragment ProductDataInfo on pdpDataInfo {\n  icon\n  title\n  isApplink\n  applink\n  content {\n    icon\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment ProductSocial on pdpDataSocialProof {\n  row\n  content {\n    icon\n    title\n    subtitle\n    applink\n    type\n    rating\n    __typename\n  }\n  __typename\n}\n\nfragment ProductDetailMediaComponent on pdpDataProductDetailMediaComponent {\n  title\n  description\n  contentMedia {\n    url\n    ratio\n    type\n    __typename\n  }\n  show\n  ctaText\n  __typename\n}\n\nquery PDPGetLayoutQuery($shopDomain: String, $productKey: String, $layoutID: String, $apiVersion: Float, $userLocation: pdpUserLocation, $extParam: String, $tokonow: pdpTokoNow, $deviceID: String) {\n  pdpGetLayout(shopDomain: $shopDomain, productKey: $productKey, layoutID: $layoutID, apiVersion: $apiVersion, userLocation: $userLocation, extParam: $extParam, tokonow: $tokonow, deviceID: $deviceID) {\n    requestID\n    name\n    pdpSession\n    basicInfo {\n      alias\n      createdAt\n      isQA\n      id: productID\n      shopID\n      shopName\n      minOrder\n      maxOrder\n      weight\n      weightUnit\n      condition\n      status\n      url\n      needPrescription\n      catalogID\n      isLeasing\n      isBlacklisted\n      isTokoNow\n      menu {\n        id\n        name\n        url\n        __typename\n      }\n      category {\n        id\n        name\n        title\n        breadcrumbURL\n        isAdult\n        isKyc\n        minAge\n        detail {\n          id\n          name\n          breadcrumbURL\n          isAdult\n          __typename\n        }\n        __typename\n      }\n      txStats {\n        transactionSuccess\n        transactionReject\n        countSold\n        paymentVerified\n        itemSoldFmt\n        __typename\n      }\n      stats {\n        countView\n        countReview\n        countTalk\n        rating\n        __typename\n      }\n      __typename\n    }\n    components {\n      name\n      type\n      position\n      data {\n        ...ProductMedia\n        ...ProductHighlight\n        ...ProductInfo\n        ...ProductDetail\n        ...ProductSocial\n        ...ProductDataInfo\n        ...ProductCustomInfo\n        ...ProductVariant\n        ...ProductCategoryCarousel\n        ...ProductDetailMediaComponent\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n',
            },
        ]
        response = requests.post('https://gql.tokopedia.com/graphql/PDPGetLayoutQuery', headers=headers, json=json_data)
        parsed = response.json()
        data = parsed[0]['data']['pdpGetLayout']['basicInfo']
        data_detail = parsed[0]['data']['pdpGetLayout']['components'][3]['data'][0]
        flattened_data = {
            'product_name': data_detail['name'],
            'product_alias': data['alias'],
            'product_created': data['createdAt'],
            'product_url': data['url'],
            'product_image': parsed[0]['data']['pdpGetLayout']['components'][0]['data'][0]['media'][0]['urlOriginal'],
            'product_id': data['id'],
            'shop_id' : data['shopID'],
            'shop_name' : data['shopName'],
            'price': data_detail['price']['value'],
            'currency': data_detail['price']['currency'],
            'stock' : data['maxOrder'],
            'weight': data['weight'],
            'condition': data['condition'],
            'status': data['status'],
            'category': data['category']['name'],
            'category_detail': ', '.join([detail['name'] for detail in data['category']['detail']]),
            'total_order': data['txStats']['transactionSuccess'],
            'total_sold': data['txStats']['countSold'],
            'total_review': data['stats']['countReview'],
            'rating': data['stats']['rating']
        }

        flattened_data_list.append(flattened_data)
    
    product_data_detail = pd.DataFrame(flattened_data_list)
    product_data['price'] = product_data['price'].str.replace("Rp","").str.replace(".","").astype(int)
    product_data['campaign_original_price'] = pd.to_numeric(product_data['campaign_original_price'].str.replace("Rp","").str.replace(".",""), errors='coerce').fillna(0).astype(int)
    
    while True: 
        break_flag = input("Are you finished? (Y/N) ")

        if break_flag == "Y":
            break
        elif break_flag == "N":
            break
        else:
            print("Please input (Y/N) only")

    file_name = f'Export File//tokopedia_product_{shop_name}.xlsx'

    # Create ExcelWriter with openpyxl engine
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        product_data.to_excel(writer,sheet_name='product_list',index=False)
        product_data_detail.to_excel(writer, sheet_name='product_detail',index=False)
        
    if break_flag == "Y":
        break
    elif break_flag == "N":
        None