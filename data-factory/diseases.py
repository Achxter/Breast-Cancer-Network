from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import calendar
import time
from tqdm.auto import tqdm

url = "https://www.ncbi.nlm.nih.gov/research/pubtator-api/publications/export/biocxml?pmids={}"

pubs_df = pd.read_csv("../data/1676879038-pubs-breast-cancer-4860.csv")

logs_str = "Logs: {}"


def get_disease_from_pubs(row):
    # print(logs_str.format("Getting disease from pub: {}".format(row['PMID'])))

    disease = np.array([])

    metadata_url = url.format(row['PMID'])
    metadata_response = requests.get(metadata_url)

    metadata_soup = BeautifulSoup(metadata_response.content, 'xml')
    disease_sections = metadata_soup.find_all('infon', {'key': 'type'})
    for disease_section in disease_sections:
        if(disease_section.get_text().strip().lower() == 'disease'):
            text = disease_section.parent.find('text').get_text().strip()
            new_disease = np.array([row['PMID'], text])
            disease = np.append(disease, new_disease)

    # print(logs_str.format("Found: {} diseases".format(disease.size)))

    return disease


def get_disease(df, limit=0):
    print(logs_str.format(
        "🔨 Getting disease from {} publications".format(df.shape[0])))
    disease = np.array([])

    pqbar = tqdm(desc="Processing", total=limit if limit >
                 0 else df.shape[0], position=0, leave=True)

    for index, row in df.iterrows():
        if(limit > 0 and index >= limit):
            break

        # print(logs_str.format("Iteration number: {}".format(index)))

        try:
            new_disease = get_disease_from_pubs(row)
            disease = np.append(disease, new_disease)
        except Exception as e:
            print(logs_str.format("Error: {}".format(e)))
            continue
        finally:
            pqbar.update(1)

    pqbar.close()
    print("-" * 30)
    print(logs_str.format("🌟 Job done!"))
    print("-" * 30)
    print(logs_str.format("📊 Found {} diseases".format(disease.size)))

    return disease


def transorm_to_df(dis, columns):
    df = pd.DataFrame(dis.reshape(-1, 2), columns=columns)
    return df


def diseases_mining():
    diseases = get_disease(pubs_df)
    diseases_df = transorm_to_df(diseases, ['PMID', 'Disease'])

    diseases_df.dropna(inplace=True)  # Remove NaN
    diseases_df["Disease"] = diseases_df["Disease"].astype(
        str).str.lower()  # Lowercase
    diseases_df = diseases_df.drop_duplicates()  # Remove duplicates

    diseases_df.describe()

    file_path = "../data/"
    ts = calendar.timegm(time.gmtime())
    num_dis = diseases_df.shape[0]
    file_name = "{}-diseases-{}.csv".format(ts, num_dis)

    diseases_df.to_csv(file_path+file_name, index=False)


def diseases_cleaning(df):
    df = df.dropna()
    df = df.drop_duplicates(['Disease'])
    return df
